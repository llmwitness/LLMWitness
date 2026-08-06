# AgentTrace Security Architecture & Threat Model

This document outlines the security controls, cryptographic primitives, threat mitigation models, and data privacy guarantees enforced by AgentTrace.

---

## 1. Threat Model & Security Boundaries

AgentTrace operates under the assumption that network traffic and underlying storage layers may be subject to unauthorized inspection or post-hoc tampering.

| Threat | Attack Vector | AgentTrace Security Mitigation |
| :--- | :--- | :--- |
| **PII Data Leakage** | Agent prompts containing SSNs, Credit Cards, or API tokens stored in logs | Deep-JSON PII Engine recursively redacts sensitive patterns out-of-band before storage |
| **Audit Log Tampering** | Malicious actor modifying or deleting audit trail entries in log vault | WORM sealing computes HMAC-SHA256 digests signed with Ed25519 asymmetric key pairs |
| **Telemetry Denial of Service** | Ingestion service crash blocking LLM inference | Fail-Open proxy architecture forwards live model traffic even if ingestion is unreachable |
| **Replay Attacks** | Replaying stolen correlation IDs across sessions | RFC 9562 UUIDv7 incorporates 48-bit millisecond timestamps preventing timestamp forgery |

---

## 2. Cryptographic Implementation Details

### 2.1 Ed25519 Asymmetric Signatures (`Ed25519KeyManager`)
- **Key Spec**: Curve25519 high-speed asymmetric key pair generated via OpenSSL / `cryptography` primitives.
- **Fingerprinting**: Public key fingerprint generated using SHA-256 over raw SubjectPublicKeyInfo byte representations.
- **Verification**: Standalone `verify_proof_receipt(filepath, secret_key)` validates signature integrity independently of running server processes.

### 2.2 Out-of-Band PII Sanitization
- **Regex Engines**:
  - **SSN**: `\b\d{3}-\d{2}-\d{4}\b` -> `[REDACTED_SSN]`
  - **Credit Card**: `\b(?:\d[ -]*?){13,16}\b` -> `[REDACTED_CREDIT_CARD]`
  - **API Token**: `sk-[a-zA-Z0-9_-]{20,}` -> `[REDACTED_API_TOKEN]`
  - **Vision Payload**: Base64 image payloads (>1000 chars or data URIs) -> `[REDACTED_IMAGE_PAYLOAD_SIZE_X_BYTES]`
- **Allow-List Preservation**: Explicit allow-list terms passed via `AGENTTRACE_PII_ALLOW_LIST` environment variable are safely preserved without redaction.
