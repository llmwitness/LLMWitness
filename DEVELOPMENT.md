# AgentTrace Local Development Guide

Welcome to the local development guide for AgentTrace maintainers and contributors.

---

## 1. Local Environment Setup

### Environment Requirements
- Python 3.10+
- Node.js 18+ (optional, for native JS SDK benchmarking)
- Docker & Docker Compose (optional, for containerized integration testing)

### Setup Steps
```bash
# Clone repository
git clone https://github.com/Vinayakdata/AgentTrace.git
cd AgentTrace

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install package in editable mode with development dependencies
pip install -e .[dev]

# Install pre-commit git hooks
pre-commit install
```

---

## 2. Launching Services Locally for Testing

Start Ingestion Server and Gateway Proxy in separate terminal sessions:

```bash
# Terminal 1: Ingestion Server
uvicorn ingest:app --host 127.0.0.1 --port 8000 --reload

# Terminal 2: Gateway Proxy (with Mock Upstream mode enabled)
AGENTTRACE_MOCK_UPSTREAM=true uvicorn gateway:app --host 127.0.0.1 --port 8011 --reload
```

---

## 3. Running Verification Suites

```bash
# Run pytest test suite
pytest tests/ -v

# Run functional test script
python test_agenttrace.py

# Run CLI configuration validation
python cli.py validate-config

# Run quick benchmark validation pass
python cli.py run-benchmarks --quick
```
