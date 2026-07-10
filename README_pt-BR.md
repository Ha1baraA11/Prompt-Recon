<div align="center">

[English](./README.md) · [简体中文](./README.zh-CN.md) · [繁體中文](./README.zh-TW.md) · [日本語](./README_ja.md) · [한국어](./README_ko.md) · [Español](./README_es.md) · **Português** · [Русский](./README_ru.md) · [Français](./README_fr.md) · [Deutsch](./README_de.md)

</div>

<p align="center">
  <img src="assets/logo.png" alt="Logo do Prompt-Recon" width="200">
</p>

# Prompt-Recon

Prompt-Recon é um scanner offline de secrets para repositórios pessoais e equipes pequenas. Ele verifica a árvore de trabalho, a área de staging do Git e o histórico local alcançável para encontrar tokens, chaves privadas, credenciais de banco de dados, JWTs e valores de alta entropia, sem enviar candidatos para nenhum serviço.

## Recursos

- Analisa arquivos, blobs staged e histórico sem fazer checkout de revisões antigas.
- Regras para AWS, GitHub, GitLab, OpenAI, Anthropic, Hugging Face, Slack, Stripe, npm, PyPI, Google API, chaves privadas, JWT, URLs de banco e atribuições genéricas de credenciais.
- Saídas sempre redigidas; baselines armazenam apenas impressões digitais.
- Suporta `.gitignore`, `.promptignore`, configuração TOML, marcadores allow e relatórios SARIF, JSONL, CSV e Markdown.

## Requisitos e instalação

- Python 3.10–3.13; Git para staging e histórico

```bash
python -m pip install promptrecon
promptrecon scan .
promptrecon scan --staged
promptrecon scan --history
promptrecon scan . --format sarif --output results.sarif
```

Códigos de saída: `0` (nenhuma nova ocorrência), `1` (ocorrências encontradas) e `2` (erro de configuração, Git ou execução).

## Baseline e configuração

```bash
promptrecon baseline create .
promptrecon baseline audit
promptrecon baseline update .
```

Baselines não armazenam texto secreto. Copie `.promptrecon.toml.example` para `.promptrecon.toml` para configurar exclusões e regras declarativas. Use `# promptrecon: allow` ou `# promptrecon: allow-next-line` para exceções intencionais.

## Hooks e correção segura

```bash
promptrecon hook install
promptrecon patch settings.py --line 12 --env-var SERVICE_TOKEN
promptrecon patch settings.py --line 12 --env-var SERVICE_TOKEN --apply
```

Hooks existentes não são sobrescritos silenciosamente. A correção só grava com `--apply` e nunca cria um arquivo contendo o segredo real.

## Desenvolvimento e licença

```bash
python -m pytest
ruff check .
python -m mypy promptrecon
python -m build
```

MIT. Consulte [LICENSE](./LICENSE) e [CHANGELOG](./CHANGELOG.md).
