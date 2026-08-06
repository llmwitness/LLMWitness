"""
Legacy compatibility layer for ingest.
Forwards FastAPI application and WORM vault handlers to agenttrace.ingest.
"""

from agenttrace.ingest import (
    ExtensionTelemetryPayload,
    GatewayTelemetryPayload,
    PROOF_FILE_PATH,
    SDKTelemetryPayload,
    app,
    audit_vault,
    get_or_create_session,
    get_session_audit,
    health_check,
    ingest_extension_telemetry,
    ingest_gateway_telemetry,
    ingest_sdk_telemetry,
    key_manager,
    seal_session_audit,
    sealed_proofs,
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
