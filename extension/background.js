/**
 * LLMWitness opt-in localhost background worker (Manifest V3).
 */

const INGESTION_ENDPOINT = "http://127.0.0.1:8000/ingest/extension";

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message && message.action === 'LLMWITNESS_DOM_TELEMETRY') {
    const payload = message.payload;
    
    fetch(INGESTION_ENDPOINT, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    })
    .then(response => {
      if (!response.ok) throw new Error(`ingestion returned HTTP ${response.status}`);
      return response.json();
    })
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
