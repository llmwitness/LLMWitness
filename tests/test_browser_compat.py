"""
LLMWitness Community - Browser Compatibility Suite
Validates JavaScript SDK export structure, UUIDv7 generation in browser engine, and Chrome Extension manifest schema.
"""

import json
import os
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def test_js_sdk_file_structure():
    js_sdk_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "llmwitness.js")
    )
    assert os.path.exists(js_sdk_path), "llmwitness.js missing from workspace root"

    with open(js_sdk_path, encoding="utf-8") as f:
        code = f.read()

    assert (
        "LLMWitnessBrowserSDK" in code
        or "class LLMWitness" in code
        or "recordMutation" in code
        or "uuidv7" in code
    )


def test_chrome_extension_manifest_v3_schema():
    manifest_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "extension", "manifest.json")
    )
    assert os.path.exists(manifest_path), "Chrome extension manifest.json missing"

    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)

    assert manifest.get("manifest_version") == 3
    assert "name" in manifest
    assert "version" in manifest
    assert "content_scripts" in manifest or "background" in manifest


def test_extension_sidecar_uses_shared_uuidv7_contract():
    """The MV3 sidecar must emit IDs the gateway can use for session linking."""
    content_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "extension", "content.js")
    )
    with open(content_path, encoding="utf-8") as f:
        code = f.read()

    assert "X-LLMWitness-Correlation-ID" in code
    assert "data-llmwitness-correlation-id" in code
    assert "llmwitness:correlation-id" in code
    assert "UUIDV7_PATTERN" in code
    assert "correlation_id: getActiveCorrelationId()" in code


def test_browser_bridge_bounds_queue_and_omits_url_query_strings():
    js_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "llmwitness.js")
    )
    with open(js_path, encoding="utf-8") as f:
        code = f.read()

    assert "maxQueueSize" in code
    assert "droppedEvents" in code
    assert "window.location.origin" in code
    assert "window.location.pathname" in code
    assert "window.location.href" not in code
    assert "input instanceof Request ? input.headers" in code


def test_js_sdk_node_execution():
    """Runs node syntax validation on llmwitness.js if node binary exists."""
    js_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "llmwitness.js")
    )
    try:
        res = subprocess.run(["node", "-c", js_path], capture_output=True, text=True)
        if res.returncode != 0:
            pytest.fail(f"JavaScript SDK syntax check failed: {res.stderr}")
    except FileNotFoundError:
        pytest.skip("Node.js binary not installed on runner path")


def test_js_sdk_runtime_uuid_and_queue_contract():
    """Exercise exported browser-bridge behavior in Node when available."""
    js_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "llmwitness.js")
    )
    script = r"""
const sdk = require(process.argv[1]);
const pattern = /^[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
for (let index = 0; index < 1000; index += 1) {
  if (!pattern.test(sdk.generateUUIDv7())) process.exit(2);
}
const bridge = new sdk.LLMWitnessBridge({maxQueueSize: 2, debounceMs: 60000});
bridge.enqueue({event_type: 'one', dom_delta: {}});
bridge.enqueue({event_type: 'two', dom_delta: {}});
bridge.enqueue({event_type: 'three', dom_delta: {}});
if (bridge.queue.length !== 2 || bridge.droppedEvents !== 1) process.exit(3);
clearTimeout(bridge.timer);
"""
    try:
        result = subprocess.run(
            ["node", "-e", script, js_path], capture_output=True, text=True, timeout=10
        )
    except FileNotFoundError:
        pytest.skip("Node.js binary not installed on runner path")
    assert result.returncode == 0, result.stderr


def test_extension_content_script_node_syntax():
    """Runs syntax validation on the MV3 content script when Node is available."""
    content_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "extension", "content.js")
    )
    try:
        res = subprocess.run(
            ["node", "--check", content_path], capture_output=True, text=True
        )
        if res.returncode != 0:
            pytest.fail(f"Extension content script syntax check failed: {res.stderr}")
    except FileNotFoundError:
        pytest.skip("Node.js binary not installed on runner path")
