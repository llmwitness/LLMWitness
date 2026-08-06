"""
AgentTrace Production Testing - Fuzz Testing Suite
Fuzzes PII redaction engine, payload decoders, JSON string parsers, and header inputs with arbitrary data.
"""

import base64
import json
import os
import random
import string
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils import redact_payload, redact_pii


def random_string(length: int) -> str:
    letters = string.ascii_letters + string.digits + string.punctuation + " \t\n\r"
    return "".join(random.choice(letters) for _ in range(length))


def generate_fuzz_payload(depth: int = 0) -> any:
    if depth > 4 or random.random() < 0.3:
        choice = random.choice(["ssn", "card", "token", "b64", "text", "int", "none"])
        if choice == "ssn":
            return f"SSN: {random.randint(100,999)}-{random.randint(10,99)}-{random.randint(1000,9999)}"
        elif choice == "card":
            return f"CC: 4111-{random.randint(1000,9999)}-{random.randint(1000,9999)}-4444"
        elif choice == "token":
            return f"Bearer sk-{random_string(30)}"
        elif choice == "b64":
            return "data:image/png;base64," + base64.b64encode(os.urandom(random.randint(10, 2000))).decode("utf-8")
        elif choice == "text":
            return random_string(random.randint(5, 500))
        elif choice == "int":
            return random.randint(-10000, 10000)
        else:
            return None
    elif random.random() < 0.5:
        return [generate_fuzz_payload(depth + 1) for _ in range(random.randint(1, 5))]
    else:
        return {f"key_{random_string(5)}": generate_fuzz_payload(depth + 1) for _ in range(random.randint(1, 5))}


def test_pii_engine_fuzzing():
    """Fuzzes redact_payload with 100 randomly generated nested data structures."""
    for _ in range(100):
        payload = generate_fuzz_payload()
        try:
            redacted = redact_payload(payload)
            # Ensure serialization does not throw error
            _ = json.dumps(redacted, default=str)
        except Exception as e:
            pytest.fail(f"PII Redaction crashed during fuzzing on payload: {payload}. Error: {e}")


def test_malformed_json_strings_fuzzing():
    """Tests resilience against malformed JSON string values embedded in payload."""
    malformed_strings = [
        "{unclosed_json: true",
        "[1, 2, 3,",
        "{\"ssn\": \"123-45-6789\", invalid_syntax}",
        "\x00\x01\x02\x03",
        "data:image/invalid_b64;base64,%%%%not_base64%%%%"
    ]
    for ms in malformed_strings:
        res = redact_pii(ms)
        assert isinstance(res, str)
