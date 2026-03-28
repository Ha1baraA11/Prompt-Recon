# file: tests/test_pre_commit_smoke.py

"""
Prompt-Recon Pre-commit Hook Smoke Test

覆盖 4 个核心场景：
1. 正常提交通过
2. 暂存泄漏被拦截
3. 工作区脏但暂存区干净仍通过（staged blob 隔离性）
4. .env 文件被扫描
"""

import unittest
import tempfile
import subprocess
import os
import sys
import shutil

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)


class TestPreCommitHook(unittest.TestCase):

    def setUp(self):
        """在临时目录创建 Git 仓库并安装 Hook"""
        self.temp_dir = tempfile.mkdtemp(prefix='pr_test_')
        self.repo_dir = os.path.join(self.temp_dir, 'repo')
        os.makedirs(self.repo_dir)

        # 初始化 Git 仓库
        subprocess.run(['git', 'init'], cwd=self.repo_dir, check=True, capture_output=True)
        subprocess.run(
            ['git', 'config', 'user.email', 'test@test.com'],
            cwd=self.repo_dir, check=True, capture_output=True
        )
        subprocess.run(
            ['git', 'config', 'user.name', 'Test User'],
            cwd=self.repo_dir, check=True, capture_output=True
        )

        # 安装 Hook（用生成的 wrapper）
        install_script = os.path.join(REPO_ROOT, 'scripts', 'install_pre_commit_hook.py')
        result = subprocess.run(
            [sys.executable, install_script],
            cwd=self.repo_dir, capture_output=True, text=True
        )
        self.assertEqual(result.returncode, 0, f"Hook install failed: {result.stderr}")

        # 读取生成的 hook 脚本，检查是否用了 -m 方式启动
        hook_path = os.path.join(self.repo_dir, '.git', 'hooks', 'pre-commit')
        hook_content = open(hook_path).read()
        self.assertIn('-m promptrecon.hooks.pre_commit', hook_content)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def _git_commit(self, msg='test'):
        """运行 git commit，返回 subprocess.CompletedProcess"""
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
        # 先提交一个干净文件（创建历史）
        clean_content = 'x = 1\n'
        with open(os.path.join(self.repo_dir, 'clean.py'), 'w') as f:
            f.write(clean_content)
        subprocess.run(['git', 'add', 'clean.py'], cwd=self.repo_dir, check=True, capture_output=True)
        result1 = self._git_commit('clean commit')
        self.assertEqual(result1.returncode, 0)

        # 工作区加入 dirty.py（含 secret，未 staged）
        dirty_content = 'api_key = "sk-pretend-not-staged"\n'
        with open(os.path.join(self.repo_dir, 'dirty.py'), 'w') as f:
            f.write(dirty_content)
        # --allow-empty 强制提交（无新 staged 内容），验证 hook 不扫 untracked 文件
        result2 = subprocess.run(
            ['git', 'commit', '-m', 'verify hook', '--allow-empty'],
            cwd=self.repo_dir, capture_output=True, text=True
        )
        self.assertEqual(result2.returncode, 0,
                         f"dirty.py is untracked; hook should only scan staged blob. "
                         f"Got: {result2.stdout}\n{result2.stderr}")

    # ---- 场景4：.env 文件被扫描（用引号值触发 generic_secret） ----
    def test_env_file_scanned(self):
        # generic_secret 要求引号，OPENAI_API_KEY=sk-... 不带引号 → 不匹配
        # 用带引号的格式来测试 .env 能否被扫描
        env_content = 'api_key = "sk-mock-1234567890abcdefghijklmnop"\n'
        with open(os.path.join(self.repo_dir, '.env'), 'w') as f:
            f.write(env_content)
        subprocess.run(['git', 'add', '.env'], cwd=self.repo_dir, check=True, capture_output=True)
        result = self._git_commit('add env')
        self.assertNotEqual(result.returncode, 0,
                             f"Expected blocked, got: {result.stdout}\n{result.stderr}")
        combined = result.stdout + result.stderr
        self.assertIn('BLOCKED', combined)


if __name__ == '__main__':
    unittest.main()
