# Development

```bash
python -m venv .venv
python -m pip install -e ".[dev]"
pytest -q
ruff check llmwitness tests
mypy --config-file pyproject.toml llmwitness
python -m build
```

Run Community services only on loopback:

```bash
python -m uvicorn llmwitness.ingest:app --host 127.0.0.1 --port 8000
python -m uvicorn llmwitness.gateway:app --host 127.0.0.1 --port 8011
```

Configure persistent development keys and shared tokens through environment variables; never commit them. Generated keys are process-local and unsuitable for durable identity.
