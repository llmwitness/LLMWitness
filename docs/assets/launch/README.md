# LLMWitness launch media

These images demonstrate LLMWitness Community `0.1.0` with synthetic local data.

- [`demo.gif`](demo.gif) summarizes installation, local ingestion, receipt creation, successful verification, and rejection after a signed field is modified.
- [`architecture.png`](architecture.png) shows the Community data path and its single-user localhost boundary.
- [`social-preview.png`](social-preview.png) is the repository's 1280×640 social-preview image.
- [`screenshots/`](screenshots/) contains four presentation-ready terminal captures.

The verification captures were produced from an actual local run. The unmodified receipt passed Ed25519 and HMAC verification. A copy with its signed `task_name` changed failed verification with exit code `1`.

These assets do not claim that local receipt files are immutable or WORM storage, that pattern scrubbing removes all sensitive data, or that Community `0.1.0` is a production security or compliance control.
