import os
import secrets

_LOCAL_SESSION_SECRET = secrets.token_hex(32)


def get_secret_key() -> str:
    """Return the configured key or one random key scoped to this process."""
    return os.getenv("LLMWITNESS_SECRET_KEY") or _LOCAL_SESSION_SECRET


class LLMWitnessConfig:
    """Type-safe configuration container with validation rules."""

    def __init__(self):
        self.secret_key_configured = bool(os.getenv("LLMWITNESS_SECRET_KEY"))
        self.private_key_configured = bool(os.getenv("LLMWITNESS_PRIVATE_KEY_PEM"))
        self.secret_key: str = get_secret_key()
        self.ingestion_url: str = os.getenv(
            "INGESTION_SERVER_URL", "http://localhost:8000"
        )
        self.gateway_port: int = int(os.getenv("GATEWAY_PORT", "8011"))
        self.ingest_port: int = int(os.getenv("INGEST_PORT", "8000"))
        self.mock_upstream: bool = os.getenv(
            "LLMWITNESS_MOCK_UPSTREAM", "false"
        ).lower() in ("true", "1", "yes")
        self.disable_pii: bool = os.getenv(
            "LLMWITNESS_DISABLE_PII_SCRUBBING", "false"
        ).lower() in ("true", "1", "yes")

        allow_raw = os.getenv("LLMWITNESS_PII_ALLOW_LIST", "")
        self.pii_allow_list: list[str] = [
            x.strip() for x in allow_raw.split(",") if x.strip()
        ]

    def validate(self) -> list[str]:
        """Validates configuration parameters and returns list of error messages (if any)."""
        errors = []
        if not self.secret_key_configured:
            errors.append(
                "LLMWITNESS_SECRET_KEY is unset; receipts will not have a durable HMAC identity."
            )
        if not self.private_key_configured:
            errors.append(
                "LLMWITNESS_PRIVATE_KEY_PEM is unset; the Ed25519 signer changes after restart."
            )
        if not self.secret_key:
            errors.append("LLMWITNESS_SECRET_KEY must not be empty.")
        if len(self.secret_key) < 16:
            errors.append(
                "LLMWITNESS_SECRET_KEY should be at least 16 characters for cryptographic security."
            )
        if not self.ingestion_url.startswith(("http://", "https://")):
            errors.append(
                f"INGESTION_SERVER_URL invalid scheme: '{self.ingestion_url}'. Must start with http:// or https://"
            )
        return errors


_global_config: LLMWitnessConfig | None = None


def get_config() -> LLMWitnessConfig:
    global _global_config
    if _global_config is None:
        _global_config = LLMWitnessConfig()
    return _global_config
