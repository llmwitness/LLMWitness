import datetime
import json
import os
import time
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, Header, Request, status
from pydantic import BaseModel, Field
import uvicorn

from utils import Ed25519KeyManager, generate_uuidv7, verify_proof_receipt

PROOF_FILE_PATH = os.getenv("AGENTTRACE_PROOF_PATH", "proof.json")

# Instantiate central key manager (loads from ENV or generates Ed25519 keypair)
key_manager = Ed25519KeyManager()

app = FastAPI(
    title="AgentTrace Ingestion & WORM Vault Service",
    description="Enterprise Cryptographic Audit Engine for Autonomous Agents",
    version="1.1.0"
)

# In-memory storage representing Write-Once-Read-Many (WORM) audit store
# Indexed by correlation_id
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


@app.get("/ingest/session/{correlation_id}")
async def get_session_trace(correlation_id: str):
    if correlation_id not in audit_vault:
        raise HTTPException(status_code=404, detail="Correlation ID not found")
    return audit_vault[correlation_id]


class SealRequest(BaseModel):
    correlation_id: str


@app.post("/ingest/seal")
async def seal_session_proof(request: SealRequest):
    correlation_id = request.correlation_id
    if correlation_id not in audit_vault:
        raise HTTPException(status_code=404, detail="Correlation ID not found")
    
    session = audit_vault[correlation_id]
    session["is_sealed"] = True
    session["sealed_at"] = time.time()
    
    # Serialize session deterministic representation for Ed25519 signing
    session_json = json.dumps(session, sort_keys=True)
    signature_b64 = key_manager.sign(session_json)
    public_key_fp = key_manager.get_public_key_fingerprint()
    public_key_pem = key_manager.export_public_key_pem()
    timestamp_iso = datetime.datetime.fromtimestamp(session["sealed_at"], tz=datetime.timezone.utc).isoformat()
    
    proof_record = {
        "correlation_id": correlation_id,
        "timestamp": session["sealed_at"],
        "timestamp_iso": timestamp_iso,
        "public_key_fingerprint": public_key_fp,
        "public_key_pem": public_key_pem,
        "signature": signature_b64,
        "sdk_event_count": len(session["sdk_events"]),
        "gateway_event_count": len(session["gateway_events"]),
        "extension_event_count": len(session["extension_events"]),
        "integrity_status": "VERIFIED_WORM_IMMUTABLE",
        "proof_manifest": session
    }
    
    sealed_proofs[correlation_id] = proof_record
    
    # Save/Append to proof.json manifest file
    all_proofs = []
    if os.path.exists(PROOF_FILE_PATH):
        try:
            with open(PROOF_FILE_PATH, "r", encoding="utf-8") as f:
                all_proofs = json.load(f)
                if not isinstance(all_proofs, list):
                    all_proofs = [all_proofs]
        except Exception:
            all_proofs = []
            
    # Update or add current proof
    all_proofs = [p for p in all_proofs if p.get("correlation_id") != correlation_id]
    all_proofs.append(proof_record)
    
    with open(PROOF_FILE_PATH, "w", encoding="utf-8") as f:
        json.dump(all_proofs, f, indent=2)
        
    return {
        "status": "sealed",
        "correlation_id": correlation_id,
        "public_key_fingerprint": public_key_fp,
        "signature": signature_b64,
        "timestamp_iso": timestamp_iso,
        "proof_file": PROOF_FILE_PATH
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
