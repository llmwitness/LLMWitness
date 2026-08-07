# Contributing

Focused bug fixes, tests, documentation corrections, and narrowly scoped improvements are welcome.

Before submitting a change:

```bash
python -m pip install -e ".[dev]"
pytest -q
ruff check llmwitness tests
mypy --config-file pyproject.toml llmwitness
python -m build
```

Do not commit receipts, logs, generated packages, benchmark outputs, credentials, personal data, private prompts, or proprietary Cloud/Enterprise implementation. Report vulnerabilities privately as described in [SECURITY.md](SECURITY.md).

Contributions are accepted under Apache-2.0. Contributors must have the right to submit their work. Repository owners should obtain legal advice before introducing a contributor agreement or attempting future relicensing.
