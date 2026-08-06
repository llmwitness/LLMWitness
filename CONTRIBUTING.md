# Contributing to AgentTrace

Thank you for your interest in contributing to AgentTrace! We welcome community contributions, bug fixes, performance enhancements, and security improvements.

---

## Development Standards & Workflow

### 1. Fork & Clone
```bash
git clone https://github.com/YOUR_USERNAME/AgentTrace.git
cd AgentTrace
```

### 2. Set Up Virtual Environment & Editable Install
```bash
python3 -m venv venv
source venv/bin/activate
pip install -e .[dev]
pre-commit install
```

### 3. Code Style & Formatting
AgentTrace enforces strict code formatting:
- **Black**: 120 character line limit.
- **Ruff**: Linter checking pyflakes, bugbear, and security issues.
- **Mypy**: Type annotation validation.

Run style checks before submitting PRs:
```bash
black --check .
ruff check .
mypy --config-file pyproject.toml agenttrace_sdk.py gateway.py ingest.py utils.py
```

### 4. Running Test & Benchmark Suites
Before opening a Pull Request:
```bash
pytest tests/
python test_agenttrace.py
python benchmarks/run_benchmarks.py --quick
```

---

## Pull Request Guidelines

1. **Keep PRs Focused**: Avoid mixing architectural changes with refactoring.
2. **Backwards Compatibility**: Do not break existing SDK method signatures or Gateway API routes.
3. **Include Tests**: Every new feature or bug fix must include pytest coverage in `tests/`.
4. **Commit Messages**: Use clean, descriptive commit messages (e.g., `feat: add OpenTelemetry span exporter`).
