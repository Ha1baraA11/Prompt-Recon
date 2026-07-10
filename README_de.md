<p align="center">
  <img src="assets/logo.png" alt="Prompt-Recon-Logo" width="200">
</p>

<h1 align="center">Prompt-Recon</h1>

<p align="center">
  <strong>Offline-Scanner für Secrets in persönlichen Repositories und kleinen Teams</strong><br>
  Prüft Arbeitsbaum, staged Blobs und erreichbare Git-Historie, ohne Kandidaten irgendwohin zu senden.
</p>

<p align="center">
  <a href="./README.md">English</a> · <a href="./README.zh-CN.md">简体中文</a> · <a href="./README.zh-TW.md">繁體中文</a> · <a href="./README_ja.md">日本語</a> · <a href="./README_ko.md">한국어</a> · <a href="./README_es.md">Español</a> · <a href="./README_pt-BR.md">Português</a> · <a href="./README_ru.md">Русский</a> · <a href="./README_fr.md">Français</a>
</p>

---

## Funktionen

- Prüft Dateien, staged Blobs und Git-Historie, ohne alte Revisionen auszuchecken.
- Regeln für AWS, GitHub, GitLab, OpenAI, Anthropic, Hugging Face, Slack, Stripe, npm, PyPI, Google API, private Schlüssel, JWT, Datenbank-URLs und allgemeine Zugangsdaten-Zuweisungen.
- Ausgaben sind immer redigiert; Baselines speichern nur Fingerabdrücke.
- Unterstützt `.gitignore`, `.promptignore`, TOML-Konfiguration, allow-Marker sowie SARIF-, JSONL-, CSV- und Markdown-Berichte.

## Voraussetzungen und Installation

- Python 3.10–3.13; Git für Staging und Historie

```bash
python -m pip install promptrecon
promptrecon scan .
promptrecon scan --staged
promptrecon scan --history
promptrecon scan . --format sarif --output results.sarif
```

Exit-Codes: `0` (keine neuen Funde), `1` (Funde vorhanden), `2` (Konfigurations-, Git- oder Laufzeitfehler).

## Baseline und Konfiguration

```bash
promptrecon baseline create .
promptrecon baseline audit
promptrecon baseline update .
```

Baselines speichern keinen Secret-Text. Kopieren Sie `.promptrecon.toml.example` nach `.promptrecon.toml`, um Ausschlüsse und deklarative Regeln zu konfigurieren. Für bewusste Ausnahmen verwenden Sie `# promptrecon: allow` oder `# promptrecon: allow-next-line`.

## Hooks und sichere Korrektur

```bash
promptrecon hook install
promptrecon patch settings.py --line 12 --env-var SERVICE_TOKEN
promptrecon patch settings.py --line 12 --env-var SERVICE_TOKEN --apply
```

Vorhandene Hooks werden nicht still überschrieben. Geschrieben wird nur mit `--apply`; eine Datei mit dem echten Secret wird nie erzeugt.

## Entwicklung und Lizenz

```bash
python -m pytest
ruff check .
python -m mypy promptrecon
python -m build
```

MIT. Siehe [LICENSE](./LICENSE) und [CHANGELOG](./CHANGELOG.md).
