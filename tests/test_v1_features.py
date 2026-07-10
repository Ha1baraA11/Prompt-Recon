import json
import subprocess
import sys
from pathlib import Path

from promptrecon.baseline import load_baseline, write_baseline
from promptrecon.config import load_config
from promptrecon.core import build_ignore_spec, fingerprint, scan_content
from promptrecon.models import Finding, Severity
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


def test_config_loads_data_only_rule(tmp_path: Path):
    config = tmp_path / ".promptrecon.toml"
    config.write_text('''[scan]\nexclude = ["generated/"]\n\n[[rule]]\nid = "internal"\ndescription = "internal token"\npattern = "int_[A-Za-z0-9]{8,}"\nseverity = "high"\n''')
    loaded = load_config(config)
    assert loaded.excludes == ("generated/",)
    assert loaded.rules[0].id == "internal"


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
