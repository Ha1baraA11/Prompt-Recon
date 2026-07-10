"""Built-in offline rules. Patterns deliberately avoid network verification."""

from __future__ import annotations

from ..models import Rule, Severity


def builtin_rules() -> tuple[Rule, ...]:
    return (
        Rule("aws_access_key", "AWS access key ID", r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b", Severity.HIGH),
        Rule("github_token", "GitHub token", r"\bgh[pousr]_[A-Za-z0-9_]{30,}\b", Severity.CRITICAL),
        Rule("gitlab_token", "GitLab token", r"\bglpat-[A-Za-z0-9_-]{20,}\b", Severity.HIGH),
        Rule("openai_api_key", "OpenAI API key", r"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b", Severity.CRITICAL),
        Rule("anthropic_api_key", "Anthropic API key", r"\bsk-ant-[A-Za-z0-9_-]{20,}\b", Severity.CRITICAL),
        Rule("huggingface_token", "Hugging Face token", r"\bhf_[A-Za-z0-9]{20,}\b", Severity.HIGH),
        Rule("slack_token", "Slack token", r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b", Severity.HIGH),
        Rule("stripe_key", "Stripe secret key", r"\bsk_(?:live|test)_[A-Za-z0-9]{16,}\b", Severity.HIGH),
        Rule("npm_token", "npm token", r"\bnpm_[A-Za-z0-9]{20,}\b", Severity.HIGH),
        Rule("pypi_token", "PyPI token", r"\bpypi-[A-Za-z0-9_-]{20,}\b", Severity.HIGH),
        Rule("google_api_key", "Google API key", r"\bAIza[0-9A-Za-z_-]{35}\b", Severity.HIGH),
        Rule("private_key", "Private key material", r"-----BEGIN (?:[A-Z ]+ )?PRIVATE KEY-----", Severity.CRITICAL),
        Rule(
            "jwt",
            "JSON Web Token",
            r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b",
            Severity.MEDIUM,
            0.75,
        ),
        Rule(
            "database_url",
            "Credential-bearing database URL",
            r"\b(?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?):\/\/[^\s:@/]+:[^\s@/]+@",
            Severity.HIGH,
        ),
        Rule(
            "generic_secret",
            "Hard-coded credential assignment",
            r"\b(?:password|passwd|token|secret|api[_-]?key)\s*[:=]\s*(['\"])([^'\"]{8,})\1",
            Severity.MEDIUM,
            0.7,
            2,
        ),
        Rule(
            "high_entropy",
            "High-entropy encoded secret candidate",
            r"['\"]([A-Za-z0-9+/=_-]{32,})['\"]",
            Severity.MEDIUM,
            0.55,
            1,
        ),
    )
