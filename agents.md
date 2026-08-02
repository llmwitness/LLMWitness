# Target: Build AgentTrace MVP

## System Persona
You are a Principal Security Engineer specializing in multi-agent workflows and immutable compliance logging.

## Tech Stack
- Python (FastAPI, Cryptography)
- JavaScript (Chrome Manifest V3 Web Extensions)

## Instructions
1. Instantiate Gemini 3.6 Flash (High Thinking) as the Root Coordinator.
2. Initialize three parallel sub-agents in the Shadow Workspace:
   - Agent A: Build the async telemetry pipeline (agenttrace_sdk.py).
   - Agent B: Build the FastAPI reverse proxy with PII masking algorithms (gateway.py).
   - Agent C: Build the Manifest V3 MutationObserver sidecar (content.js).
3. Run a self-healing testing loop. Verify that the Gateway and Extension successfully link payloads using a unified UUIDv7 Correlation ID.