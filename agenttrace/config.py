import os
from typing import List, Optional


class AgentTraceConfig:
    """Type-safe configuration container with validation rules."""

    def __init__(self):
        self.secret_key: str = os.getenv("AGENTTRACE_SECRET_KEY", "agenttrace-production-worm-vault-key-2026")
        self.ingestion_url: str = os.getenv("INGESTION_SERVER_URL", "http://localhost:8000")
        self.gateway_port: int = int(os.getenv("GATEWAY_PORT", "8011"))
        self.ingest_port: int = int(os.getenv("INGEST_PORT", "8000"))
        self.mock_upstream: bool = os.getenv("AGENTTRACE_MOCK_UPSTREAM", "false").lower() in ("true", "1", "yes")
        self.disable_pii: bool = os.getenv("AGENTTRACE_DISABLE_PII_SCRUBBING", "false").lower() in ("true", "1", "yes")
        
        allow_raw = os.getenv("AGENTTRACE_PII_ALLOW_LIST", "")
        self.pii_allow_list: List[str] = [x.strip() for x in allow_raw.split(",") if x.strip()]

    def validate(self) -> List[str]:
        """Validates configuration parameters and returns list of error messages (if any)."""
        errors = []
        if not self.secret_key:
            errors.append("AGENTTRACE_SECRET_KEY must not be empty.")
        if len(self.secret_key) < 16:
            errors.append("AGENTTRACE_SECRET_KEY should be at least 16 characters for cryptographic security.")
        if not self.ingestion_url.startswith(("http://", "https://")):
            errors.append(f"INGESTION_SERVER_URL invalid scheme: '{self.ingestion_url}'. Must start with http:// or https://")
        return errors


_global_config: Optional[AgentTraceConfig] = None


def get_config() -> AgentTraceConfig:
    global _global_config
    if _global_config is None:
        _global_config = AgentTraceConfig()
    return _global_config
