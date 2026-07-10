<div align="center">

[English](./README.md) · [简体中文](./README.zh-CN.md) · [繁體中文](./README.zh-TW.md) · **日本語** · [한국어](./README_ko.md) · [Español](./README_es.md) · [Português](./README_pt-BR.md) · [Русский](./README_ru.md) · [Français](./README_fr.md) · [Deutsch](./README_de.md)

</div>

<p align="center">
  <img src="assets/logo.png" alt="Prompt-Recon ロゴ" width="200">
</p>

# Prompt-Recon

Prompt-Recon は個人リポジトリや小規模チーム向けのオフライン secrets スキャナーです。ワークツリー、Git のステージ領域、ローカルで到達可能な履歴からトークン、秘密鍵、データベース認証情報、JWT、高エントロピー値を検出します。候補値を外部へ送信することはありません。

## 機能

- 古いリビジョンを checkout せずにファイル、staged blob、Git 履歴を検査。
- AWS、GitHub、GitLab、OpenAI、Anthropic、Hugging Face、Slack、Stripe、npm、PyPI、Google API、秘密鍵、JWT、データベース URL、一般的な認証情報代入に対応。
- 出力は常にマスキングされ、baseline には指紋だけを保存。
- `.gitignore`、`.promptignore`、TOML 設定、allow マーカー、SARIF/JSONL/CSV/Markdown をサポート。

## 必要条件

- Python 3.10–3.13
- staged/履歴スキャンには Git

## インストールと使用

```bash
python -m pip install promptrecon
promptrecon scan .
promptrecon scan --staged
promptrecon scan --history
promptrecon scan . --format sarif --output results.sarif
```

終了コードは `0`（新しい未承認検出なし）、`1`（検出あり）、`2`（設定・Git・実行エラー）です。

## Baseline と設定

```bash
promptrecon baseline create .
promptrecon baseline audit
promptrecon baseline update .
```

baseline は秘密本文を保存しません。`.promptrecon.toml.example` を `.promptrecon.toml` にコピーして除外とデータ形式のルールを設定できます。意図的な例外には `# promptrecon: allow` または `# promptrecon: allow-next-line` を使用します。

## Git hook と安全な修復

```bash
promptrecon hook install
promptrecon patch settings.py --line 12 --env-var SERVICE_TOKEN
promptrecon patch settings.py --line 12 --env-var SERVICE_TOKEN --apply
```

既存 hook を黙って上書きせず、修復は `--apply` を明示した場合だけ原子的に書き込みます。実際の秘密を含む修復ファイルは作成しません。

## 開発とライセンス

```bash
python -m pytest
ruff check .
python -m mypy promptrecon
python -m build
```

MIT。[LICENSE](./LICENSE) と [CHANGELOG](./CHANGELOG.md) を参照してください。
