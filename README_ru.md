<p align="center">
  <img src="assets/logo.png" alt="Логотип Prompt-Recon" width="200">
</p>

<h1 align="center">Prompt-Recon</h1>

<p align="center">
  <strong>Офлайн-сканер секретов для личных репозиториев и небольших команд</strong><br>
  Проверяет рабочее дерево, staged blob и доступную историю Git, не отправляя кандидаты наружу.
</p>

<p align="center">
  <a href="./README.md">English</a> · <a href="./README.zh-CN.md">简体中文</a> · <a href="./README.zh-TW.md">繁體中文</a> · <a href="./README_ja.md">日本語</a> · <a href="./README_ko.md">한국어</a> · <a href="./README_es.md">Español</a> · <a href="./README_pt-BR.md">Português</a> · <a href="./README_fr.md">Français</a> · <a href="./README_de.md">Deutsch</a>
</p>

---

## Возможности

- Проверка файлов, staged blob и истории без checkout старых ревизий.
- Правила для AWS, GitHub, GitLab, OpenAI, Anthropic, Hugging Face, Slack, Stripe, npm, PyPI, Google API, закрытых ключей, JWT, URL баз данных и обычных присваиваний учётных данных.
- Все отчёты обезличены; baseline хранит только отпечатки.
- Поддержка `.gitignore`, `.promptignore`, TOML, allow-маркеров и форматов SARIF, JSONL, CSV, Markdown.

## Требования и установка

- Python 3.10–3.13; Git для staging и истории

```bash
python -m pip install promptrecon
promptrecon scan .
promptrecon scan --staged
promptrecon scan --history
promptrecon scan . --format sarif --output results.sarif
```

Коды выхода: `0` (новых находок нет), `1` (находки есть), `2` (ошибка конфигурации, Git или выполнения).

## Baseline и конфигурация

```bash
promptrecon baseline create .
promptrecon baseline audit
promptrecon baseline update .
```

Baseline не хранит текст секретов. Скопируйте `.promptrecon.toml.example` в `.promptrecon.toml` для настройки исключений и декларативных правил. Для осознанных исключений используйте `# promptrecon: allow` или `# promptrecon: allow-next-line`.

## Hooks и безопасное исправление

```bash
promptrecon hook install
promptrecon patch settings.py --line 12 --env-var SERVICE_TOKEN
promptrecon patch settings.py --line 12 --env-var SERVICE_TOKEN --apply
```

Существующий hook не перезаписывается молча. Запись выполняется только с `--apply`, файл с настоящим секретом не создаётся.

## Разработка и лицензия

```bash
python -m pytest
ruff check .
python -m mypy promptrecon
python -m build
```

MIT. См. [LICENSE](./LICENSE) и [CHANGELOG](./CHANGELOG.md).
