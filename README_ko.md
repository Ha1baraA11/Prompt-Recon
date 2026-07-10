<div align="center">

[English](./README.md) · [简体中文](./README.zh-CN.md) · [繁體中文](./README.zh-TW.md) · [日本語](./README_ja.md) · **한국어** · [Español](./README_es.md) · [Português](./README_pt-BR.md) · [Русский](./README_ru.md) · [Français](./README_fr.md) · [Deutsch](./README_de.md)

</div>

<p align="center">
  <img src="assets/logo.png" alt="Prompt-Recon 로고" width="200">
</p>

# Prompt-Recon

Prompt-Recon은 개인 저장소와 소규모 팀을 위한 오프라인 secrets 스캐너입니다. 작업 트리, Git 스테이징 영역, 로컬에서 접근 가능한 기록을 검사하여 공급자 토큰, 개인 키, 데이터베이스 자격 증명, JWT, 고엔트로피 값을 찾습니다. 후보 값은 외부로 전송되지 않습니다.

## 기능

- 이전 버전을 checkout하지 않고 파일, staged blob, Git 기록 검사.
- AWS, GitHub, GitLab, OpenAI, Anthropic, Hugging Face, Slack, Stripe, npm, PyPI, Google API, 개인 키, JWT, 데이터베이스 URL 및 일반 자격 증명 대입 규칙 제공.
- 콘솔과 기계 보고서는 항상 마스킹되며 baseline에는 지문만 저장.
- `.gitignore`, `.promptignore`, TOML 설정, allow 마커, SARIF/JSONL/CSV/Markdown 지원.

## 요구 사항 및 설치

- Python 3.10–3.13, staged/기록 검사용 Git

```bash
python -m pip install promptrecon
promptrecon scan .
promptrecon scan --staged
promptrecon scan --history
promptrecon scan . --format sarif --output results.sarif
```

종료 코드는 `0`(새 미승인 탐지 없음), `1`(탐지 있음), `2`(설정·Git·실행 오류)입니다.

## Baseline 및 설정

```bash
promptrecon baseline create .
promptrecon baseline audit
promptrecon baseline update .
```

baseline은 비밀 본문을 저장하지 않습니다. `.promptrecon.toml.example`을 `.promptrecon.toml`로 복사해 제외 경로와 데이터 기반 규칙을 설정하세요. 의도적인 예외에는 `# promptrecon: allow` 또는 `# promptrecon: allow-next-line`을 사용합니다.

## Hook 및 안전한 수정

```bash
promptrecon hook install
promptrecon patch settings.py --line 12 --env-var SERVICE_TOKEN
promptrecon patch settings.py --line 12 --env-var SERVICE_TOKEN --apply
```

기존 hook을 조용히 덮어쓰지 않으며, `--apply`를 명시한 경우에만 원자적으로 씁니다. 실제 비밀이 포함된 수정 파일은 만들지 않습니다.

## 개발 및 라이선스

```bash
python -m pytest
ruff check .
python -m mypy promptrecon
python -m build
```

MIT. [LICENSE](./LICENSE)와 [CHANGELOG](./CHANGELOG.md)를 확인하세요.
