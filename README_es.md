<p align="center">
  <img src="assets/logo.png" alt="Logotipo de Prompt-Recon" width="200">
</p>

<h1 align="center">Prompt-Recon</h1>

<p align="center">
  <strong>Escáner offline de secretos para repositorios personales y equipos pequeños</strong><br>
  Revisa el árbol de trabajo, blobs staged e historial Git accesible sin enviar candidatos a ningún servicio.
</p>

<p align="center">
  <a href="./README.md">English</a> · <a href="./README.zh-CN.md">简体中文</a> · <a href="./README.zh-TW.md">繁體中文</a> · <a href="./README_ja.md">日本語</a> · <a href="./README_ko.md">한국어</a> · <a href="./README_pt-BR.md">Português</a> · <a href="./README_ru.md">Русский</a> · <a href="./README_fr.md">Français</a> · <a href="./README_de.md">Deutsch</a>
</p>

---

## Funciones

- Analiza archivos, blobs staged e historial sin hacer checkout de revisiones antiguas.
- Incluye reglas para AWS, GitHub, GitLab, OpenAI, Anthropic, Hugging Face, Slack, Stripe, npm, PyPI, Google API, claves privadas, JWT, URLs de bases de datos y asignaciones genéricas de credenciales.
- Todos los informes están redactados; las baselines solo guardan huellas.
- Admite `.gitignore`, `.promptignore`, configuración TOML, marcadores allow y formatos SARIF, JSONL, CSV y Markdown.

## Requisitos e instalación

- Python 3.10–3.13; Git para staging e historial

```bash
python -m pip install promptrecon
promptrecon scan .
promptrecon scan --staged
promptrecon scan --history
promptrecon scan . --format sarif --output results.sarif
```

Los códigos de salida son `0` (sin hallazgos nuevos), `1` (hay hallazgos) y `2` (error de configuración, Git o ejecución).

## Baseline y configuración

```bash
promptrecon baseline create .
promptrecon baseline audit
promptrecon baseline update .
```

Las baselines no guardan texto secreto. Copia `.promptrecon.toml.example` a `.promptrecon.toml` para configurar exclusiones y reglas declarativas. Usa `# promptrecon: allow` o `# promptrecon: allow-next-line` para excepciones intencionadas.

## Hooks y corrección segura

```bash
promptrecon hook install
promptrecon patch settings.py --line 12 --env-var SERVICE_TOKEN
promptrecon patch settings.py --line 12 --env-var SERVICE_TOKEN --apply
```

No sobrescribe hooks existentes silenciosamente. La corrección solo escribe con `--apply` y nunca crea un archivo con el secreto real.

## Desarrollo y licencia

```bash
python -m pytest
ruff check .
python -m mypy promptrecon
python -m build
```

MIT. Consulta [LICENSE](./LICENSE) y [CHANGELOG](./CHANGELOG.md).
