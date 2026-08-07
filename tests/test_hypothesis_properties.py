"""
LLMWitness Community - Hypothesis Property-Based Testing Suite
Tests invariants: UUIDv7 monotonicity, PII redaction idempotency, and Ed25519 signature validity.
"""

import os
import sys
import time
import uuid

from hypothesis import given
from hypothesis import strategies as st

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from llmwitness.utils import Ed25519KeyManager, generate_uuidv7, redact_payload


def test_uuidv7_structure_and_monotonicity():
    u1 = generate_uuidv7()
    time.sleep(0.002)
    u2 = generate_uuidv7()

    parsed1 = uuid.UUID(u1)
    parsed2 = uuid.UUID(u2)

    assert parsed1.version == 7
    assert parsed2.version == 7
    # UUIDv7 strings generated across time steps preserve lexicographical ordering
    assert u1 < u2


@given(st.text(min_size=1, max_size=500))
def test_pii_redaction_idempotency(input_text):
    """Property: Redacting an already redacted payload returns identical output (redact(redact(x)) == redact(x))."""
    first_pass = redact_payload(input_text)
    second_pass = redact_payload(first_pass)
    assert first_pass == second_pass


@given(st.text(min_size=1, max_size=200))
def test_ed25519_sign_verify_invariant(payload):
    """Property: Any generated signature over arbitrary payload must verify successfully with public key."""
    km = Ed25519KeyManager()
    sig = km.sign(payload)
    assert km.verify(payload, sig) is True
    # Mutating payload breaks verification
    assert km.verify(payload + "_tampered", sig) is False
