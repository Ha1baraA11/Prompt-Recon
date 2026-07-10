<p align="center">
  <img src="assets/logo.png" alt="Logo Prompt-Recon" width="200">
</p>

<h1 align="center">Prompt-Recon</h1>

<p align="center">
  <strong>Scanner hors ligne de secrets pour dépôts personnels et petites équipes</strong><br>
  Vérifie l’arbre de travail, les blobs staged et l’historique Git accessible sans envoyer de candidats à un service externe.
</p>

<p align="center">
  [English](./README.md) · [简体中文](./README.zh-CN.md) · [繁體中文](./README.zh-TW.md) · [日本語](./README_ja.md) · [한국어](./README_ko.md) · [Español](./README_es.md) · [Português](./README_pt-BR.md) · [Русский](./README_ru.md) · [Deutsch](./README_de.md)
</p>

---

## Fonctionnalités

- Analyse des fichiers, blobs staged et de l’historique sans checkout des anciennes révisions.
- Règles pour AWS, GitHub, GitLab, OpenAI, Anthropic, Hugging Face, Slack, Stripe, npm, PyPI, Google API, clés privées, JWT, URL de bases de données et affectations génériques d’identifiants.
- Sorties toujours masquées ; les baselines ne conservent que des empreintes.
- Prise en charge de `.gitignore`, `.promptignore`, TOML, marqueurs allow et rapports SARIF, JSONL, CSV, Markdown.

## Prérequis et installation

- Python 3.10–3.13 ; Git pour le staging et l’historique

```bash
python -m pip install promptrecon
promptrecon scan .
promptrecon scan --staged
promptrecon scan --history
promptrecon scan . --format sarif --output results.sarif
```

Les codes de sortie sont `0` (aucune nouvelle détection), `1` (détections présentes) et `2` (erreur de configuration, Git ou exécution).

## Baseline et configuration

```bash
promptrecon baseline create .
promptrecon baseline audit
promptrecon baseline update .
```

Les baselines ne stockent pas le texte des secrets. Copiez `.promptrecon.toml.example` vers `.promptrecon.toml` pour configurer les exclusions et règles déclaratives. Utilisez `# promptrecon: allow` ou `# promptrecon: allow-next-line` pour les exceptions volontaires.

## Hooks et correction sûre

```bash
promptrecon hook install
promptrecon patch settings.py --line 12 --env-var SERVICE_TOKEN
promptrecon patch settings.py --line 12 --env-var SERVICE_TOKEN --apply
```

Un hook existant n’est jamais écrasé silencieusement. L’écriture n’a lieu qu’avec `--apply` et aucun fichier contenant le secret réel n’est créé.

## Développement et licence

```bash
python -m pytest
ruff check .
python -m mypy promptrecon
python -m build
```

MIT. Voir [LICENSE](./LICENSE) et [CHANGELOG](./CHANGELOG.md).
