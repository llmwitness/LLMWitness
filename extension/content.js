/**
 * AgentTrace Chrome Auditor Content Script (Manifest V3 Sidecar)
 * Captures structural DOM mutations and user interactions correlated by X-AgentTrace-Correlation-ID.
 * Includes adaptive throttling & noise filtering for high-frequency React/Vue SPA re-renders.
 */

(function () {
  // Utility: Generate RFC 9562 compliant UUIDv7 in browser JS
  function generateUUIDv7() {
    const ms = Date.now();
    const msHex = ms.toString(16).padStart(12, '0');

    const bytes = new Uint8Array(16);
    crypto.getRandomValues(bytes);

    for (let i = 0; i < 6; i++) {
      bytes[i] = parseInt(msHex.slice(i * 2, i * 2 + 2), 16);
    }

    bytes[6] = (bytes[6] & 0x0f) | 0x70;
    bytes[8] = (bytes[8] & 0x3f) | 0x80;

    const hex = Array.from(bytes).map(b => b.toString(16).padStart(2, '0')).join('');
    return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`;
  }

  function getActiveCorrelationId() {
    let cid = window.__AGENTTRACE_CORRELATION_ID__ ||
              document.documentElement.getAttribute('data-agenttrace-correlation-id') ||
              sessionStorage.getItem('X-AgentTrace-Correlation-ID');

    if (!cid) {
      cid = generateUUIDv7();
      sessionStorage.setItem('X-AgentTrace-Correlation-ID', cid);
      window.__AGENTTRACE_CORRELATION_ID__ = cid;
      document.documentElement.setAttribute('data-agenttrace-correlation-id', cid);
    }
    return cid;
  }

  // Telemetry Throttling & Batching Queue
  let telemetryBuffer = [];
  let throttleTimer = null;
  const THROTTLE_MS = 150; // Batch mutations every 150ms to prevent worker thread congestion

  function flushTelemetryBuffer() {
    if (telemetryBuffer.length === 0) return;

    const batchPayload = {
      correlation_id: getActiveCorrelationId(),
      timestamp: Date.now() / 1000,
      url: window.location.href,
      event_type: 'dom_batch_mutation',
      element_id: 'document-root',
      dom_delta: {
        batchSize: telemetryBuffer.length,
        events: telemetryBuffer.slice(0, 20) // Cap top 20 significant events per batch
      }
    };

    telemetryBuffer = [];

    if (typeof chrome !== 'undefined' && chrome.runtime && chrome.runtime.sendMessage) {
      chrome.runtime.sendMessage({ action: 'AGENTTRACE_DOM_TELEMETRY', payload: batchPayload }, function (response) {
        if (chrome.runtime.lastError) {
          // Worker worker unreachable
        }
      });
    }
  }

  function sendTelemetry(eventType, elementId, domDelta) {
    // Direct UI interactions (clicks, keypresses) send immediately
    if (eventType === 'click' || eventType === 'keydown' || eventType === 'input') {
      const immediatePayload = {
        correlation_id: getActiveCorrelationId(),
        timestamp: Date.now() / 1000,
        url: window.location.href,
        event_type: eventType,
        element_id: elementId || null,
        dom_delta: domDelta || {}
      };

      if (typeof chrome !== 'undefined' && chrome.runtime && chrome.runtime.sendMessage) {
        chrome.runtime.sendMessage({ action: 'AGENTTRACE_DOM_TELEMETRY', payload: immediatePayload });
      }
      return;
    }

    // Structural DOM mutations get buffered and throttled
    telemetryBuffer.push({ eventType, elementId, domDelta, ts: Date.now() });

    if (!throttleTimer) {
      throttleTimer = setTimeout(function () {
        throttleTimer = null;
        flushTelemetryBuffer();
      }, THROTTLE_MS);
    }
  }

  // 1. Setup DOM MutationObserver with Noise Filtering
  const observer = new MutationObserver(function (mutations) {
    mutations.forEach(function (mutation) {
      // Filter out non-structural noise (pure style, animation class changes)
      if (mutation.type === 'attributes' && (mutation.attributeName === 'style' || mutation.attributeName === 'class')) {
        return;
      }

      const addedNodes = Array.from(mutation.addedNodes)
        .filter(node => node.nodeType === 1) // Only element nodes
        .map(node => ({
          tagName: node.tagName || null,
          id: node.id || null
        }));

      const removedNodes = Array.from(mutation.removedNodes)
        .filter(node => node.nodeType === 1)
        .map(node => ({
          tagName: node.tagName || null,
          id: node.id || null
        }));

      if (addedNodes.length > 0 || removedNodes.length > 0) {
        sendTelemetry('dom_mutation', mutation.target.id || mutation.target.tagName, {
          type: mutation.type,
          addedCount: addedNodes.length,
          removedCount: removedNodes.length,
          addedNodesSummary: addedNodes.slice(0, 3),
          removedNodesSummary: removedNodes.slice(0, 3)
        });
      }
    });
  });

  if (document.documentElement) {
    observer.observe(document.documentElement, {
      childList: true,
      subtree: true,
      attributeFilter: ['id', 'data-agenttrace-id', 'href', 'type'] // Filter out noisy style/class attributes
    });
  }

  // 2. Click Event Listener
  document.addEventListener('click', function (e) {
    const target = e.target;
    sendTelemetry('click', target.id || null, {
      tagName: target.tagName,
      className: target.className,
      innerText: (target.innerText || '').slice(0, 50),
      x: e.clientX,
      y: e.clientY
    });
  }, true);

  // 3. Input Event Listener
  document.addEventListener('input', function (e) {
    const target = e.target;
    sendTelemetry('input', target.id || null, {
      tagName: target.tagName,
      type: target.type || null,
      valueLength: (target.value || '').length
    });
  }, true);

  // 4. Keydown Event Listener
  document.addEventListener('keydown', function (e) {
    const target = e.target;
    sendTelemetry('keydown', target.id || null, {
      key: e.key.length === 1 ? '[CHAR]' : e.key,
      code: e.code,
      ctrlKey: e.ctrlKey,
      shiftKey: e.shiftKey
    });
  }, true);

})();
