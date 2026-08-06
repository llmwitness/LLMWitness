import datetime
import json
import os
import time
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, Header, Request, status
from pydantic import BaseModel, Field
import uvicorn

from agenttrace.utils import Ed25519KeyManager, generate_uuidv7, verify_proof_receipt

PROOF_FILE_PATH = os.getenv("AGENTTRACE_PROOF_PATH", "proof.json")

# Instantiate central key manager (loads from ENV or generates Ed25519 keypair)
key_manager = Ed25519KeyManager()

app = FastAPI(
    title="AgentTrace Ingestion & WORM Vault Service",
    description="Enterprise Cryptographic Audit Engine for Autonomous Agents",
    version="1.1.0"
)

# In-memory storage representing Write-Once-Read-Many (WORM) audit store
audit_vault: Dict[str, Dict[str, Any]] = {}
sealed_proofs: Dict[str, Dict[str, Any]] = {}


class SDKTelemetryPayload(BaseModel):
    correlation_id: str
    task_name: str
    timestamp: float
    prompt_tokens: int = 0
    completion_tokens: int = 0
    completion_string: Optional[str] = None
    tool_calls: List[Dict[str, Any]] = []
    agent_state: Dict[str, Any] = {}


class GatewayTelemetryPayload(BaseModel):
    correlation_id: str
    timestamp: float
    upstream_url: str
    status_code: int
    request_hmac: Optional[str] = None
    response_hmac: Optional[str] = None
    redacted_request: Optional[Dict[str, Any]] = None
    redacted_response: Optional[Dict[str, Any]] = None
    optimization_meta: Optional[Dict[str, Any]] = None


class ExtensionTelemetryPayload(BaseModel):
    correlation_id: str
    timestamp: float
    url: str
    event_type: str
    element_id: Optional[str] = None
    dom_delta: Dict[str, Any]


def get_or_create_session(correlation_id: str) -> Dict[str, Any]:
    if correlation_id not in audit_vault:
        audit_vault[correlation_id] = {
            "correlation_id": correlation_id,
            "created_at": time.time(),
            "sdk_events": [],
            "gateway_events": [],
            "extension_events": [],
            "is_sealed": False
        }
    return audit_vault[correlation_id]


@app.post("/ingest/sdk", status_code=201)
async def ingest_sdk_telemetry(payload: SDKTelemetryPayload):
    session = get_or_create_session(payload.correlation_id)
    if session.get("is_sealed"):
        raise HTTPException(status_code=400, detail="Audit session is sealed (WORM enforced)")
    
    session["sdk_events"].append(payload.model_dump())
    return {"status": "success", "correlation_id": payload.correlation_id, "sdk_event_count": len(session["sdk_events"])}


@app.post("/ingest/gateway", status_code=201)
async def ingest_gateway_telemetry(payload: GatewayTelemetryPayload):
    session = get_or_create_session(payload.correlation_id)
    if session.get("is_sealed"):
        raise HTTPException(status_code=400, detail="Audit session is sealed (WORM enforced)")
    
    session["gateway_events"].append(payload.model_dump())
    return {"status": "success", "correlation_id": payload.correlation_id, "gateway_event_count": len(session["gateway_events"])}


@app.post("/ingest/extension", status_code=201)
async def ingest_extension_telemetry(payload: ExtensionTelemetryPayload):
    session = get_or_create_session(payload.correlation_id)
    if session.get("is_sealed"):
        raise HTTPException(status_code=400, detail="Audit session is sealed (WORM enforced)")
    
    session["extension_events"].append(payload.model_dump())
    return {"status": "success", "correlation_id": payload.correlation_id, "extension_event_count": len(session["extension_events"])}


@app.post("/ingest/seal")
async def seal_session_audit(request_data: Dict[str, str]):
    """
    WORM Session Seal Endpoint.
    Computes a deterministic SHA256 / HMAC manifest signature over all SDK, Gateway, and Extension events,
    signs the manifest using asymmetric Ed25519 digital signature, and writes proof.json receipt.
    """
    correlation_id = request_data.get("correlation_id")
    if not correlation_id or correlation_id not in audit_vault:
        raise HTTPException(status_code=404, detail="Correlation session not found")

    session = audit_vault[correlation_id]
    session["is_sealed"] = True
    session["sealed_at"] = time.time()

    # Create deterministic event timeline manifest
    event_manifest = {
        "correlation_id": correlation_id,
        "sealed_at": session["sealed_at"],
        "events": {
            "sdk": session["sdk_events"],
            "gateway": session["gateway_events"],
            "extension": session["extension_events"],
        }
    }

    serialized_manifest = json.dumps(event_manifest, sort_keys=True)
    
    # Generate Ed25519 signature & public key fingerprint
    ed25519_signature = key_manager.sign(serialized_manifest)
    public_key_fingerprint = key_manager.get_public_key_fingerprint()

    # Generate HMAC WORM receipt signature using secret key
    secret_key = os.getenv("AGENTTRACE_SECRET_KEY", "agenttrace-production-worm-vault-key-2026")
    from agenttrace.utils import compute_hmac_signature
    
    # Store proof receipt data
    proof_receipt = {
        "correlation_id": correlation_id,
        "sealed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "events": event_manifest["events"],
        "ed25519_signature": ed25519_signature,
        "public_key_fingerprint": public_key_fingerprint,
        "hmac_signature": compute_hmac_signature(json.dumps({
            "correlation_id": correlation_id,
            "sealed_at": session["sealed_at"],
            "events": event_manifest["events"]
        }, sort_keys=True), secret_key)
    }

    sealed_proofs[correlation_id] = proof_receipt

    # Persist receipt to disk proof.json
    try:
        with open(PROOF_FILE_PATH, "w", encoding="utf-8") as f:
            json.dump(proof_receipt, f, indent=2)
    except Exception as err:
        print(f"[WORM Vault Warning] Failed to write proof file: {err}")

    return {
        "status": "sealed",
        "correlation_id": correlation_id,
        "hmac_signature": proof_receipt["hmac_signature"],
        "ed25519_signature": ed25519_signature,
        "public_key_fingerprint": public_key_fingerprint,
        "proof_file": PROOF_FILE_PATH
    }


@app.get("/ingest/session/{correlation_id}")
async def get_session_audit(correlation_id: str):
    if correlation_id not in audit_vault:
        raise HTTPException(status_code=404, detail="Correlation session not found")
    return audit_vault[correlation_id]


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "AgentTrace Ingestion Engine", "timestamp": time.time()}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
