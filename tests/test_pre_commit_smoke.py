# file: tests/test_pre_commit_smoke.py

"""
Prompt-Recon Pre-commit Hook Smoke Test

覆盖 4 个核心场景：
1. 正常提交通过
2. 暂存泄漏被拦截
3. 工作区脏但暂存区干净仍通过（staged blob 隔离性）
4. .env 文件被扫描

回归测试：
5. 外部目录扫描：仓库外文件能报出 finding，不静默漏报
6. 默认 ignore：.git/venv/__pycache__ 在无 .promptignore 时不被扫描
"""

import unittest
import tempfile
import subprocess
import os
import sys
import shutil

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

from promptrecon.core import scan_file, load_ignore_patterns, should_ignore
from promptrecon.rules.builtin import load_builtin_rules


class TestPreCommitHook(unittest.TestCase):

    def setUp(self):
        """在临时目录创建 Git 仓库并安装 Hook"""
        self.temp_dir = tempfile.mkdtemp(prefix='pr_test_')
        self.repo_dir = os.path.join(self.temp_dir, 'repo')
        os.makedirs(self.repo_dir)

        subprocess.run(['git', 'init'], cwd=self.repo_dir, check=True, capture_output=True)
        subprocess.run(
            ['git', 'config', 'user.email', 'test@test.com'],
            cwd=self.repo_dir, check=True, capture_output=True
        )
        subprocess.run(
            ['git', 'config', 'user.name', 'Test User'],
            cwd=self.repo_dir, check=True, capture_output=True
        )

        install_script = os.path.join(REPO_ROOT, 'scripts', 'install_pre_commit_hook.py')
        result = subprocess.run(
            [sys.executable, install_script],
            cwd=self.repo_dir, capture_output=True, text=True
        )
        self.assertEqual(result.returncode, 0, f"Hook install failed: {result.stderr}")

        hook_path = os.path.join(self.repo_dir, '.git', 'hooks', 'pre-commit')
        with open(hook_path) as hf:
            hook_content = hf.read()
        self.assertIn('-m promptrecon.hooks.pre_commit', hook_content)
        # 验证绝对路径被写进了 wrapper
        self.assertIn(sys.executable, hook_content)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def _git_commit(self, msg='test'):
        result = subprocess.run(
            ['git', 'commit', '-m', msg],
            cwd=self.repo_dir, capture_output=True, text=True
        )
        return result

    # ---- 场景1：正常提交通过 ----
    def test_normal_commit_passes(self):
        safe_content = 'print("hello world")\n'
        with open(os.path.join(self.repo_dir, 'hello.py'), 'w') as f:
            f.write(safe_content)
        subprocess.run(['git', 'add', 'hello.py'], cwd=self.repo_dir, check=True, capture_output=True)
        result = self._git_commit('normal commit')
        self.assertEqual(result.returncode, 0,
                         f"Expected pass, got: {result.stdout}\n{result.stderr}")

    # ---- 场景2：暂存泄漏被拦截 ----
    def test_staged_secret_blocked(self):
        secret_content = 'api_key = "sk-mock-1234567890abcdefghijklmnop"\n'
        with open(os.path.join(self.repo_dir, 'secret.py'), 'w') as f:
            f.write(secret_content)
        subprocess.run(['git', 'add', 'secret.py'], cwd=self.repo_dir, check=True, capture_output=True)
        result = self._git_commit('add secret')
        self.assertNotEqual(result.returncode, 0,
                            f"Expected blocked, got: {result.stdout}\n{result.stderr}")
        combined = result.stdout + result.stderr
        self.assertIn('BLOCKED', combined)
        self.assertIn('generic_secret', combined)

    # ---- 场景3：工作区脏但暂存区干净仍通过 ----
    def test_working_dirty_staged_clean_passes(self):
        clean_content = 'x = 1\n'
        with open(os.path.join(self.repo_dir, 'clean.py'), 'w') as f:
            f.write(clean_content)
        subprocess.run(['git', 'add', 'clean.py'], cwd=self.repo_dir, check=True, capture_output=True)
        result1 = self._git_commit('clean commit')
        self.assertEqual(result1.returncode, 0)

        dirty_content = 'api_key = "sk-pretend-not-staged"\n'
        with open(os.path.join(self.repo_dir, 'dirty.py'), 'w') as f:
            f.write(dirty_content)
        result2 = subprocess.run(
            ['git', 'commit', '-m', 'verify hook', '--allow-empty'],
            cwd=self.repo_dir, capture_output=True, text=True
        )
        self.assertEqual(result2.returncode, 0,
                         f"dirty.py is untracked; hook should only scan staged blob. "
                         f"Got: {result2.stdout}\n{result2.stderr}")

    # ---- 场景4：.env 文件被扫描 ----
    def test_env_file_scanned(self):
        env_content = 'api_key = "sk-mock-1234567890abcdefghijklmnop"\n'
        with open(os.path.join(self.repo_dir, '.env'), 'w') as f:
            f.write(env_content)
        subprocess.run(['git', 'add', '.env'], cwd=self.repo_dir, check=True, capture_output=True)
        result = self._git_commit('add env')
        self.assertNotEqual(result.returncode, 0,
                            f"Expected blocked, got: {result.stdout}\n{result.stderr}")
        combined = result.stdout + result.stderr
        self.assertIn('BLOCKED', combined)

    # ---- 回归5：外部目录扫描不漏报 ----
    def test_external_path_scan_finds_secret(self):
        """对仓库外临时文件调用 scan_file(...display_root=...)，必须返回 finding"""
        rules = load_builtin_rules()
        external_dir = tempfile.mkdtemp(prefix='pr_external_')
        try:
            secret_file = os.path.join(external_dir, 'api.py')
            with open(secret_file, 'w') as f:
                f.write('api_key = "sk-mock-1234567890abcdefghijklmnop"\n')
            findings = scan_file(secret_file, rules, display_root=external_dir)
            self.assertGreater(len(findings), 0,
                              f"scan_file on external file should find secret, got: {findings}")
            self.assertEqual(findings[0]['file'], 'api.py')
        finally:
            shutil.rmtree(external_dir)

    # ---- 回归6：默认 ignore 不扫 .git/venv/__pycache__ ----
    def test_default_ignore_excludes_git_and_venv(self):
        """无 .promptignore 时，.git/venv/__pycache__ 不会被扫描（只测内置默认规则）"""
        test_dir = tempfile.mkdtemp(prefix='pr_ignore_')
        try:
            git_dir = os.path.join(test_dir, '.git')
            os.makedirs(git_dir)
            secret_in_git = os.path.join(git_dir, 'config.py')
            with open(secret_in_git, 'w') as f:
                f.write('api_key = "sk-git-secret"\n')

            venv_dir = os.path.join(test_dir, 'venv')
            os.makedirs(venv_dir)
            secret_in_venv = os.path.join(venv_dir, 'activate.py')
            with open(secret_in_venv, 'w') as f:
                f.write('api_key = "sk-venv-secret"\n')

            normal_file = os.path.join(test_dir, 'main.py')
            with open(normal_file, 'w') as f:
                f.write('print("hello")\n')

            # 文件不存在，测默认规则
            ignore_patterns = load_ignore_patterns('.promptignore')
            self.assertTrue(len(ignore_patterns) > 0)

            self.assertTrue(should_ignore(secret_in_git, ignore_patterns))
            self.assertTrue(should_ignore(secret_in_venv, ignore_patterns))
            self.assertFalse(should_ignore(normal_file, ignore_patterns))
        finally:
            shutil.rmtree(test_dir)

    def test_directory_prune_by_bare_name(self):
        """
        裸目录项（如 ignored_dir）应剪枝整棵子树，不只是忽略当前目录本身。
        创建 ignored_dir/nested/secret.py 和 main.py，
        断言只有 main.py 被报出，ignored_dir 和 secret.py 都不出现。
        """
        external_dir = tempfile.mkdtemp(prefix='pr_prune_')
        try:
            # 外部目录有自己的 .promptignore
            with open(os.path.join(external_dir, '.promptignore'), 'w') as f:
                f.write('ignored_dir\n')

            # 放一个会被忽略的子目录，里面有深层文件
            nested_dir = os.path.join(external_dir, 'ignored_dir', 'nested')
            os.makedirs(nested_dir)
            with open(os.path.join(nested_dir, 'secret.py'), 'w') as f:
                f.write('api_key = "sk-deep-secret"\n')

            # 放一个正常文件
            with open(os.path.join(external_dir, 'main.py'), 'w') as f:
                f.write('api_key = "sk-visible"\n')

            result = subprocess.run(
                [sys.executable, '-m', 'promptrecon', 'scan', '-d', external_dir],
                cwd=REPO_ROOT, capture_output=True, text=True
            )
            combined = result.stdout + result.stderr

            # main.py 应该被报出
            self.assertIn('main.py', combined,
                         f"main.py should be reported: {combined}")
            # ignored_dir 和 nested/secret.py 都不应该出现
            self.assertNotIn('ignored_dir', combined,
                            f"ignored_dir should NOT be in output: {combined}")
            self.assertNotIn('secret.py', combined,
                            f"nested secret.py should NOT be in output: {combined}")
        finally:
            shutil.rmtree(external_dir)


if __name__ == '__main__':
    unittest.main()
