# Packaging

The package version is `0.1.0`. Build and inspect it locally before any publication:

```powershell
python -m build
python -m zipfile -l (Get-ChildItem dist/*.whl).FullName
python -m tarfile --list (Get-ChildItem dist/*.tar.gz).FullName
twine check dist/*
```

The wheel contains the `llmwitness` Python package, license files, and metadata. The source distribution additionally contains `llmwitness.js`, extension assets, project documentation, and the reproducible local benchmark harness. Tests, generated benchmark results, local receipts, caches, databases, logs, secrets, and generated reports must not be included in either archive.

Publishing requires a separate human review of namespace ownership, repository URLs, trademark clearance, version/tag consistency, secrets, package contents, and CI release triggers. This document does not authorize an upload.
