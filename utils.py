import base64
import datetime
import hashlib
import hmac
import json
import os
import re
import time
import uuid
from typing import Any, Dict, List, Optional, Union

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519


def generate_uuidv7() -> str:
    """
    Generate an RFC 9562 compliant UUIDv7 identifier.
    Uses 48-bit millisecond timestamp + 4-bit version 7 + 12-bit rand_a + 2-bit variant + 62-bit rand_b.
    """
    ms_timestamp = int(time.time() * 1000)
    rand_a = int.from_bytes(os.urandom(2), byteorder="big") & 0x0FFF
    high = (ms_timestamp << 16) | (0x7 << 12) | rand_a
    rand_b = int.from_bytes(os.urandom(8), byteorder="big") & 0x3FFFFFFFFFFFFFFF
    low = (0x2 << 62) | rand_b
    val = (high << 64) | low
    return str(uuid.UUID(int=val))


# Regex patterns for sensitive PII data
SSN_REGEX = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
CREDIT_CARD_REGEX = re.compile(r"\b(?:\d[ -]*?){13,16}\b")
API_TOKEN_REGEX = re.compile(
    r"(?i)\b(sk-[a-zA-Z0-9_-]{20,}|bearer\s+[a-zA-Z0-9._\-]{20,}|api[_-]?key[\s:=]+['\"]?[a-zA-Z0-9._\-]{16,}['\"]?)"
)

# Pattern for Data URL base64 image strings
DATA_IMAGE_REGEX = re.compile(r"data:image\/[a-zA-Z0-9\+\-\.]+;base64,([A-Za-z0-9+/=\s]+)")


def get_default_allow_list() -> List[str]:
    """Retrieve global PII allow-list items from environment setting."""
    env_allow = os.getenv("AGENTTRACE_PII_ALLOW_LIST", "")
    if env_allow:
        return [item.strip() for item in env_allow.split(",") if item.strip()]
    return []


def _is_raw_base64_image(data_str: str) -> Optional[int]:
    """
    Checks if a string is a raw Base64 payload representing image data (>1000 chars).
    Returns decoded byte length if detected as image, else None.
    """
    cleaned = "".join(data_str.split())
    if len(cleaned) < 1000:
        return None
    # Check if string matches base64 charset
    if not re.match(r"^[A-Za-z0-9+/=]+$", cleaned):
        return None
    try:
        raw_bytes = base64.b64decode(cleaned, validate=True)
        # Check image magic bytes (PNG, JPEG, GIF, WEBP, SVG) or generic binary payload size
        is_image_header = (
            raw_bytes.startswith(b"\x89PNG")
            or raw_bytes.startswith(b"\xff\xd8\xff")
            or raw_bytes.startswith(b"GIF8")
            or raw_bytes.startswith(b"RIFF")
            or b"<svg" in raw_bytes[:100].lower()
        )
        if is_image_header or len(raw_bytes) > 500:
            return len(raw_bytes)
    except Exception:
        pass
    return None


def redact_payload(data: Any, allow_list: Optional[List[str]] = None) -> Any:
    """
    Deep-JSON & Multi-Modal PII Redaction Engine.
    Recursively traverses dicts, lists, primitives, and JSON strings.
    Redacts SSNs, Credit Cards, API Tokens (sk-...), and Base64 vision payload images.
    """
    effective_allow = (allow_list or []) + get_default_allow_list()

    if isinstance(data, dict):
        return {k: redact_payload(v, allow_list=effective_allow) for k, v in data.items()}

    elif isinstance(data, list):
        return [redact_payload(item, allow_list=effective_allow) for item in data]

    elif isinstance(data, str):
        stripped = data.strip()

        # 1. Attempt JSON String parsing and recursive traversal
        if (stripped.startswith("{") and stripped.endswith("}")) or (
            stripped.startswith("[") and stripped.endswith("]")
        ):
            try:
                parsed_json = json.loads(stripped)
                if isinstance(parsed_json, (dict, list)):
                    redacted_obj = redact_payload(parsed_json, allow_list=effective_allow)
                    return json.dumps(redacted_obj)
            except Exception:
                pass

        # 2. Check for Data URL Base64 image payload (data:image/...;base64,...)
        def replace_data_image(match: re.Match) -> str:
            b64_str = match.group(1)
            try:
                b64_clean = "".join(b64_str.split())
                raw_bytes = base64.b64decode(b64_clean)
                byte_count = len(raw_bytes)
            except Exception:
                byte_count = len(b64_str)
            return f"[REDACTED_IMAGE_PAYLOAD_SIZE_{byte_count}_BYTES]"

        if DATA_IMAGE_REGEX.search(data):
            # Exact or embedded data image match
            if DATA_IMAGE_REGEX.fullmatch(data):
                m = DATA_IMAGE_REGEX.fullmatch(data)
                try:
                    raw_bytes = base64.b64decode("".join(m.group(1).split()))
                    byte_count = len(raw_bytes)
                except Exception:
                    byte_count = len(m.group(1))
                return f"[REDACTED_IMAGE_PAYLOAD_SIZE_{byte_count}_BYTES]"
            data = DATA_IMAGE_REGEX.sub(replace_data_image, data)

        # 3. Check for Raw Base64 Image string payload (> 1000 chars)
        b64_byte_count = _is_raw_base64_image(data)
        if b64_byte_count is not None:
            return f"[REDACTED_IMAGE_PAYLOAD_SIZE_{b64_byte_count}_BYTES]"

        # 4. Standard PII Regex Redaction with allow-list preservation
        placeholders = {}
        processed_text = data
        for idx, allowed_term in enumerate(effective_allow):
            if allowed_term in processed_text:
                ph_token = f"__AGENTTRACE_ALLOW_PH_{idx}__"
                placeholders[ph_token] = allowed_term
                processed_text = processed_text.replace(allowed_term, ph_token)

        text = SSN_REGEX.sub("[REDACTED_SSN]", processed_text)
        text = CREDIT_CARD_REGEX.sub("[REDACTED_CREDIT_CARD]", text)
        text = API_TOKEN_REGEX.sub("[REDACTED_API_TOKEN]", text)

        # Restore preserved allow-list items
        for ph_token, orig_val in placeholders.items():
            text = text.replace(ph_token, orig_val)

        return text

    return data


def redact_pii(
    content: Union[str, Dict[str, Any], List[Any]], allow_list: Optional[List[str]] = None
) -> Union[str, Dict[str, Any], List[Any]]:
    """
    Backward-compatible wrapper around deep redact_payload.
    """
    return redact_payload(content, allow_list=allow_list)


class Ed25519KeyManager:
    """
    Manages Ed25519 asymmetric key pairs, environment PEM loading,
    digital signing, and SHA-256 public key fingerprint generation.
    """

    def __init__(
        self,
        private_key_pem: Optional[Union[str, bytes]] = None,
        public_key_pem: Optional[Union[str, bytes]] = None,
    ):
        if not private_key_pem:
            private_key_pem = os.getenv("AGENTTRACE_PRIVATE_KEY_PEM")
        if not public_key_pem:
            public_key_pem = os.getenv("AGENTTRACE_PUBLIC_KEY_PEM")

        self.private_key: Optional[ed25519.Ed25519PrivateKey] = None
        self.public_key: Optional[ed25519.Ed25519PublicKey] = None

        if private_key_pem:
            pem_bytes = (
                private_key_pem.encode("utf-8") if isinstance(private_key_pem, str) else private_key_pem
            )
            self.private_key = serialization.load_pem_private_key(  # type: ignore
                pem_bytes, password=None
            )
            self.public_key = self.private_key.public_key()
        elif public_key_pem:
            pem_bytes = (
                public_key_pem.encode("utf-8") if isinstance(public_key_pem, str) else public_key_pem
            )
            self.public_key = serialization.load_pem_public_key(pem_bytes)  # type: ignore
        else:
            self.private_key = ed25519.Ed25519PrivateKey.generate()
            self.public_key = self.private_key.public_key()

    def export_private_key_pem(self) -> str:
        if not self.private_key:
            raise ValueError("Private key not loaded in this Ed25519KeyManager instance")
        pem_bytes = self.private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
        return pem_bytes.decode("utf-8")

    def export_public_key_pem(self) -> str:
        if not self.public_key:
            raise ValueError("Public key not initialized")
        pem_bytes = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        return pem_bytes.decode("utf-8")

    def get_public_key_fingerprint(self) -> str:
        """
        Computes SHA-256 fingerprint hash of the Ed25519 public key bytes.
        """
        if not self.public_key:
            raise ValueError("Public key not initialized")
        raw_bytes = self.public_key.public_bytes(
            encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw
        )
        return hashlib.sha256(raw_bytes).hexdigest()

    def sign(self, payload: Union[str, bytes]) -> str:
        """
        Signs string or byte payload using Ed25519 private key.
        Returns Base64-encoded signature.
        """
        if not self.private_key:
            raise ValueError("Cannot sign without a private key")
        payload_bytes = payload.encode("utf-8") if isinstance(payload, str) else payload
        sig_bytes = self.private_key.sign(payload_bytes)
        return base64.b64encode(sig_bytes).decode("utf-8")

    def verify(self, payload: Union[str, bytes], signature_b64: str) -> bool:
        """
        Verifies Base64 signature against payload using public key.
        """
        if not self.public_key:
            return False
        payload_bytes = payload.encode("utf-8") if isinstance(payload, str) else payload
        try:
            sig_bytes = base64.b64decode(signature_b64)
            self.public_key.verify(sig_bytes, payload_bytes)
            return True
        except (InvalidSignature, Exception):
            return False


def verify_proof_receipt(
    proof_json_path_or_dict: Union[str, Dict[str, Any], List[Dict[str, Any]]],
    public_key_pem: Optional[Union[str, bytes]] = None,
) -> bool:
    """
    Standalone verification helper function for Ed25519 WORM proof receipts.
    Returns True if the receipt signature matches and payload is untampered.
    """
    proofs = []
    if isinstance(proof_json_path_or_dict, str):
        if not os.path.exists(proof_json_path_or_dict):
            return False
        try:
            with open(proof_json_path_or_dict, "r", encoding="utf-8") as f:
                data = json.load(f)
                proofs = data if isinstance(data, list) else [data]
        except Exception:
            return False
    elif isinstance(proof_json_path_or_dict, dict):
        proofs = [proof_json_path_or_dict]
    elif isinstance(proof_json_path_or_dict, list):
        proofs = proof_json_path_or_dict
    else:
        return False

    if not proofs:
        return False

    for proof in proofs:
        sig_b64 = proof.get("signature") or proof.get("hmac_signature")
        if not sig_b64:
            return False

        manifest = proof.get("proof_manifest")
        if manifest is None:
            return False

        payload_str = json.dumps(manifest, sort_keys=True)

        target_pem = public_key_pem or proof.get("public_key_pem") or os.getenv("AGENTTRACE_PUBLIC_KEY_PEM")
        if not target_pem:
            return False

        try:
            km = Ed25519KeyManager(public_key_pem=target_pem)
            if not km.verify(payload_str, sig_b64):
                return False

            fp = proof.get("public_key_fingerprint")
            if fp and km.get_public_key_fingerprint() != fp:
                return False
        except Exception:
            return False

    return True


def compute_hmac_signature(payload: Union[str, bytes], secret_key: Union[str, bytes]) -> str:
    """Legacy HMAC helper retained for backward compatibility."""
    payload_bytes = payload.encode("utf-8") if isinstance(payload, str) else payload
    key_bytes = secret_key.encode("utf-8") if isinstance(secret_key, str) else secret_key
    return hmac.new(key_bytes, payload_bytes, hashlib.sha256).hexdigest()


def verify_hmac_signature(
    payload: Union[str, bytes], signature: str, secret_key: Union[str, bytes]
) -> bool:
    """Legacy HMAC verification helper retained for backward compatibility."""
    expected_sig = compute_hmac_signature(payload, secret_key)
    return hmac.compare_digest(expected_sig, signature)
