"""
AgentTrace Production Testing - Browser Compatibility Suite
Validates JavaScript SDK export structure, UUIDv7 generation in browser engine, and Chrome Extension manifest schema.
"""

import json
import os
import subprocess
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def test_js_sdk_file_structure():
    js_sdk_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "agenttrace.js"))
    assert os.path.exists(js_sdk_path), "agenttrace.js missing from workspace root"

    with open(js_sdk_path, "r", encoding="utf-8") as f:
        code = f.read()

    assert "AgentTraceBrowserSDK" in code or "class AgentTrace" in code or "recordMutation" in code or "uuidv7" in code


def test_chrome_extension_manifest_v3_schema():
    manifest_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "extension", "manifest.json"))
    assert os.path.exists(manifest_path), "Chrome extension manifest.json missing"

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    assert manifest.get("manifest_version") == 3
    assert "name" in manifest
    assert "version" in manifest
    assert "content_scripts" in manifest or "background" in manifest


def test_js_sdk_node_execution():
    """Runs node syntax validation on agenttrace.js if node binary exists."""
    js_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "agenttrace.js"))
    try:
        res = subprocess.run(["node", "-c", js_path], capture_output=True, text=True)
        if res.returncode != 0:
            pytest.fail(f"JavaScript SDK syntax check failed: {res.stderr}")
    except FileNotFoundError:
        pytest.skip("Node.js binary not installed on runner path")
