# AgentTrace Release Engineering — Packaging & Distribution Guide

This document outlines standard packaging, editable installation, artifact validation, and PyPI release distribution procedures for AgentTrace.

---

## 1. Package Architecture & Metadata

- **Package Name**: `agenttrace`
- **Version**: `0.1.0`
- **Build Backend**: PEP 517 / PEP 621 compliant via `setuptools.build_meta`
- **Python Compatibility**: Python 3.10+
- **Core Dependencies**:
  - `fastapi >= 0.100.0`
  - `uvicorn >= 0.22.0`
  - `cryptography >= 41.0.0`
  - `httpx >= 0.24.0`
  - `psutil >= 5.9.0`

---

## 2. Local Development & Editable Installation

To work on AgentTrace locally with live code reload:

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in editable mode with development dependencies
pip install -e .[dev]
```

Verify the editable installation:
```bash
python -c "import agenttrace_sdk; print(agenttrace_sdk.__file__)"
```

---

## 3. Building Release Artifacts (Wheel & Source Distribution)

Ensure `build` package is installed:
```bash
pip install --upgrade build twine
```

Build standard `.whl` and `.tar.gz` distribution packages:
```bash
python -m build
```

This generates build distribution files inside the `dist/` directory:
- `dist/agenttrace-0.1.0-py3-none-any.whl` (Pure Python Wheel)
- `dist/agenttrace-0.1.0.tar.gz` (Source Distribution)

---

## 4. Twine Package Validation

Before uploading to PyPI, validate the source distribution and wheel metadata:

```bash
twine check dist/*
```

Expected output:
```text
Checking dist/agenttrace-0.1.0-py3-none-any.whl: PASSED
Checking dist/agenttrace-0.1.0.tar.gz: PASSED
```

---

## 5. Publishing to PyPI / TestPyPI

### TestPyPI Dry Run:
```bash
twine upload --repository testpypi dist/*
```

### Production PyPI Release:
```bash
twine upload dist/*
```

Authentication can be configured using API tokens (`__token__`) or `.pypirc` credentials.
