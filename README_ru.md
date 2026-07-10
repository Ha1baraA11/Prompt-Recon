<div align="center">

[English](./README.md) · [简体中文](./README.zh-CN.md) · [繁體中文](./README.zh-TW.md) · [日本語](./README_ja.md) · [한국어](./README_ko.md) · [Español](./README_es.md) · [Português](./README_pt-BR.md) · **Русский** · [Français](./README_fr.md) · [Deutsch](./README_de.md)

</div>

<p align="center">
  <img src="assets/logo.png" alt="Логотип Prompt-Recon" width="200">
</p>

# Prompt-Recon

Prompt-Recon — офлайн-сканер секретов для личных репозиториев и небольших команд. Он проверяет рабочее дерево, область staging Git и доступную локальную историю, обнаруживая токены, закрытые ключи, учётные данные баз данных, JWT и значения с высокой энтропией, не отправляя кандидаты наружу.

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
