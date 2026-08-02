/**
 * AgentTrace Chrome Auditor Background Service Worker (Manifest V3)
 * Receives telemetry from content scripts and posts to central Ingestion Engine.
 */

const INGESTION_ENDPOINT = "http://localhost:8000/ingest/extension";

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message && message.action === 'AGENTTRACE_DOM_TELEMETRY') {
    const payload = message.payload;
    
    fetch(INGESTION_ENDPOINT, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    })
    .then(response => response.json())
    .then(data => {
      sendResponse({ status: 'success', data: data });
    })
    .catch(error => {
      sendResponse({ status: 'error', error: error.message });
    });

    // Return true to indicate asynchronous response handling
    return true;
  }
});
