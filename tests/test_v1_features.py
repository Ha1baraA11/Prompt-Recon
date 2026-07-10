import json
import subprocess
import sys
from pathlib import Path

import pytest

from promptrecon.baseline import load_baseline, write_baseline
from promptrecon.config import load_config
from promptrecon.core import (
    build_ignore_spec,
    fingerprint,
    is_scannable_bytes,
    load_ignore_patterns,
    scan_content,
    scan_file,
    scan_worktree,
    should_ignore,
)
from promptrecon.models import Finding, ScanOptions, Severity
from promptrecon.rules.defaults import builtin_rules


def test_detection_is_redacted_and_allowlisted():
    content = 'token = "real-value-12345678"\n# promptrecon: allow\nsecret = "known-value-12345678"\n'
    findings = scan_content(content, builtin_rules(), "settings.py")
    assert findings
    assert all("real-value" not in item.redacted for item in findings)
    assert all("known-value" not in item.redacted for item in findings)


def test_baseline_contains_fingerprints_only(tmp_path: Path):
    finding = Finding("demo", "a.py", 1, Severity.HIGH, 1.0, "[REDACTED]", fingerprint("demo", "a.py", "secret-value"))
    path = tmp_path / "baseline.json"
    write_baseline(path, [finding])
    payload = json.loads(path.read_text())
    assert payload["entries"] == [finding.fingerprint]
    assert "secret-value" not in path.read_text()
    assert load_baseline(path).contains(finding)


def test_baseline_rejects_bad_files_and_requires_force(tmp_path: Path):
    path = tmp_path / "baseline.json"
    path.write_text("not json")
    with pytest.raises(ValueError):
        load_baseline(path)
    path.write_text(json.dumps({"version": 2, "entries": []}))
    with pytest.raises(ValueError):
        load_baseline(path)
    finding = Finding("demo", "a.py", 1, Severity.HIGH, 1.0, "[REDACTED]", "a" * 64)
    with pytest.raises(FileExistsError):
        write_baseline(path, [finding])
    write_baseline(path, [finding], force=True)


def test_config_loads_data_only_rule(tmp_path: Path):
    config = tmp_path / ".promptrecon.toml"
    config.write_text('''[scan]\nexclude = ["generated/"]\n\n[[rule]]\nid = "internal"\ndescription = "internal token"\npattern = "int_[A-Za-z0-9]{8,}"\nseverity = "high"\n''')
    loaded = load_config(config)
    assert loaded.excludes == ("generated/",)
    assert loaded.rules[0].id == "internal"


def test_config_rejects_invalid_values(tmp_path: Path):
    cases = [
        "[scan]\nexclude = \"nope\"\n",
        "[scan]\nmax_file_size = 0\n",
        "[[rule]]\nid = \"bad\"\ndescription = \"bad\"\npattern = \"[\"\n",
        "not = [valid",
    ]
    for index, content in enumerate(cases):
        path = tmp_path / f"bad-{index}.toml"
        path.write_text(content)
        with pytest.raises(ValueError):
            load_config(path)
    assert load_config(tmp_path / "missing.toml").max_file_size > 0
    for index, content in enumerate(
        ["scan = \"nope\"\n", "[scan]\ndisable_rules = \"nope\"\n", "[[rule]]\n"]
    ):
        path = tmp_path / f"bad-extra-{index}.toml"
        path.write_text(content)
        with pytest.raises(ValueError):
            load_config(path)


def test_ignore_spec_uses_gitwildmatch(tmp_path: Path):
    spec = build_ignore_spec(tmp_path, ["generated/"])
    assert spec.match_file("generated/nested/key.txt")
    assert not spec.match_file("src/key.txt")


def test_cli_sarif_and_exit_codes(tmp_path: Path):
    (tmp_path / "safe.py").write_text("x = 1\n")
    safe = subprocess.run([sys.executable, "-m", "promptrecon", "scan", str(tmp_path)], capture_output=True, text=True)
    assert safe.returncode == 0
    (tmp_path / "secret.py").write_text('api_key = "sk-proj-abcdefghijklmnopqrstuvwxyz123456"\n')  # promptrecon: allow
    report = tmp_path / "results.sarif"
    blocked = subprocess.run([sys.executable, "-m", "promptrecon", "scan", str(tmp_path), "--format", "sarif", "--output", str(report)], capture_output=True, text=True)
    assert blocked.returncode == 1
    assert "sk-proj" not in report.read_text()
    assert json.loads(report.read_text())["version"] == "2.1.0"


def test_patch_is_preview_only_by_default(tmp_path: Path):
    source = tmp_path / "settings.py"
    source.write_text('TOKEN = "secret-value-12345678"\n')  # promptrecon: allow
    preview = subprocess.run([sys.executable, "-m", "promptrecon", "patch", str(source), "--line", "1", "--env-var", "TOKEN"], capture_output=True, text=True)
    assert preview.returncode == 0
    assert source.read_text() == 'TOKEN = "secret-value-12345678"\n'  # promptrecon: allow
    assert "secret-value" not in preview.stdout


def test_core_scanning_guards_and_compatibility_adapters(tmp_path: Path):
    assert not is_scannable_bytes(b"a\0b", 10)
    assert not is_scannable_bytes(b"12345", 4)
    assert is_scannable_bytes(b"safe", 10)
    ignore = tmp_path / ".promptignore"
    ignore.write_text("ignored.txt\n")
    assert "ignored.txt" in load_ignore_patterns(str(ignore))
    assert should_ignore("nested/ignored.txt", ["ignored.txt"])
    assert should_ignore("/build/out.py", ["build/"])
    source = tmp_path / "source.py"
    source.write_text('api_key = "sk-proj-abcdefghijklmnopqrstuvwxyz123456"\n')  # promptrecon: allow
    assert scan_file(str(source), object())


def test_scan_worktree_filters_files_and_baseline(tmp_path: Path):
    (tmp_path / "secret.py").write_text('api_key = "sk-proj-abcdefghijklmnopqrstuvwxyz123456"\n')  # promptrecon: allow
    (tmp_path / "ignored.py").write_text('api_key = "sk-proj-abcdefghijklmnopqrstuvwxyz123456"\n')  # promptrecon: allow
    (tmp_path / ".gitignore").write_text("ignored.py\n")
    (tmp_path / "binary.bin").write_bytes(b"x\0y")
    (tmp_path / "large.txt").write_text("x" * 300)
    result = scan_worktree(ScanOptions(tmp_path, max_file_size=200), builtin_rules(), build_ignore_spec(tmp_path, ()))
    assert result.scanned_files >= 1
    assert result.skipped_files >= 2
    assert result.findings
    baseline_path = tmp_path / "baseline.json"
    write_baseline(baseline_path, result.findings)
    baseline_result = scan_worktree(
        ScanOptions(tmp_path, max_file_size=200), builtin_rules(), build_ignore_spec(tmp_path, ()), load_baseline(baseline_path)
    )
    assert not baseline_result.findings
    assert baseline_result.suppressed_findings
