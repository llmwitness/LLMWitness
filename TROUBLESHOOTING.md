# AgentTrace Troubleshooting & Operational Diagnostics Guide

This guide provides step-by-step diagnostic workflows for resolving common operational issues when deploying AgentTrace in development, testing, or production environments.

---

## Common Issues & Resolutions

### 1. Gateway Connection Refused (`ConnectionRefusedError` / `404 Not Found`)

**Symptoms**:
HTTP client requests to `http://localhost:8011/v1/chat/completions` fail with connection refused or socket errors.

**Root Causes & Solutions**:
- **Gateway service not running**: Ensure `gateway.py` server is running via Uvicorn:
  ```bash
  uvicorn gateway:app --host 127.0.0.1 --port 8011
  ```
- **Port Conflict**: Port 8011 is occupied by another process. Use `netstat -ano` or `lsof -i :8011` to inspect port usage, or change default port in `config.py`.

---

### 2. Proof Receipt Verification Failure (`verify_proof_receipt()` Returns `False`)

**Symptoms**:
Calling `verify_proof_receipt("proof.json", secret_key)` returns `False`.

**Root Causes & Solutions**:
- **Mismatched Secret Key**: Verify `AGENTTRACE_SECRET_KEY` matches the exact secret used when sealing the audit session via `POST /ingest/seal`.
- **WORM Vault File Tampering**: `proof.json` content or event order was modified after sealing. Re-seal the audit trace session or inspect audit logs for illegal mutations.

---

### 3. PII Scrubbing Disabling for Intentional Test Data

**Symptoms**:
Test API credentials or synthetic test SSNs are redacted into `[REDACTED_SSN]` during unit tests.

**Root Causes & Solutions**:
- **Pass Bypass Header**: Pass `X-AgentTrace-Disable-PII-Scrubbing: true` in your test request headers.
- **Environment Variable**: Set `AGENTTRACE_DISABLE_PII_SCRUBBING=true` in your test environment.
- **PII Allow List**: Specify custom allowed strings in `AGENTTRACE_PII_ALLOW_LIST=SAFE_TOKEN_1,SAFE_TOKEN_2`.

---

### 4. Cache Misses on Identical Prompts

**Symptoms**:
Subsequent identical prompts to `/v1/chat/completions` result in `X-AgentTrace-Cache-Hit: false`.

**Root Causes & Solutions**:
- **Missing Caching Header**: Header `X-AgentTrace-Enable-Caching: true` must be explicitly included in request headers.
- **State Hash Mismatch**: If `X-AgentTrace-State-Hash` changes between requests, AgentTrace correctly treats state change as a cache miss to prevent stale model state hallucinations. Ensure matching state hashes are passed for identical memory states.
