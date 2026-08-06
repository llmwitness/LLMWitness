# Security Policy & Vulnerability Disclosure

## Supported Versions

AgentTrace receives security updates according to the version support matrix below:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |
| < 0.1.0 | :x:                |

---

## Reporting Vulnerabilities

The AgentTrace Engineering Committee takes security seriously. If you discover a security vulnerability, PII redaction bypass, or cryptographic flaw in WORM proof receipts:

**DO NOT OPEN A PUBLIC GITHUB ISSUE.**

Please report security issues privately via email to:
`security@agenttrace.dev`

### What to Include in Your Security Report
- Detailed description of the vulnerability (e.g., regex bypass pattern, signature forgery, buffer overflow).
- Proof-of-concept code or step-by-step reproduction instructions.
- Potential impact on privacy, compliance logging, or system integrity.

### Our Security Response Process & SLAs
1. **Initial Response**: Within 24 hours of receiving your report.
2. **Triaging & Fix Plan**: Within 72 hours of confirmation.
3. **Patch Release**: High severity vulnerabilities will receive a security hotfix release within 7 days.

---

## Security Architecture Guarantee

AgentTrace guarantees:
- **Zero Raw PII Storage**: SSNs, Credit Cards, API Tokens, and Base64 images are sanitized out-of-band before audit receipt generation.
- **WORM Audit Trail Integrity**: Once an audit session is sealed, post-hoc file modifications immediately invalidate Ed25519 digital signatures.
