/**
 * AgentTrace Headless-Safe JS SDK Bridge (agenttrace.js)
 * Zero-dependency Node.js and Browser JavaScript SDK for Playwright / Puppeteer script injection.
 * Intercepts fetch calls & DOM events, appends X-AgentTrace-Correlation-ID (UUIDv7),
 * and streams telemetry asynchronously via a debounced queue.
 */

(function () {
  /**
   * Generates an RFC 9562 compliant UUIDv7 identifier in JavaScript.
   */
  function generateUUIDv7() {
    const now = Date.now();
    const hexTime = now.toString(16).padStart(12, '0');
    const randA = Math.floor(Math.random() * 0x0fff).toString(16).padStart(3, '0');
    const variant = (8 + Math.floor(Math.random() * 4)).toString(16);
    const randB = Array.from({ length: 15 }, () =>
      Math.floor(Math.random() * 16).toString(16)
    ).join('');

    return `${hexTime.slice(0, 8)}-${hexTime.slice(8, 12)}-7${randA}-${variant}${randB.slice(
      0,
      3
    )}-${randB.slice(3)}`;
  }

  class AgentTraceBridge {
    constructor(options = {}) {
      this.ingestionUrl = (options.ingestionUrl || 'http://localhost:8000').replace(/\/$/, '');
      this.correlationId = options.correlationId || generateUUIDv7();
      this.debounceMs = options.debounceMs || 100;
      this.queue = [];
      this.timer = null;
      this.initialized = false;
      this.origFetch = null;
    }

    /**
     * Initializes fetch interception and DOM event tracking.
     */
    init(options = {}) {
      if (options.ingestionUrl) this.ingestionUrl = options.ingestionUrl.replace(/\/$/, '');
      if (options.correlationId) this.correlationId = options.correlationId;
      if (options.debounceMs) this.debounceMs = options.debounceMs;

      if (this.initialized) return this;
      this.initialized = true;

      this.patchFetch();
      this.attachDOMListeners();
      return this;
    }

    setCorrelationId(cid) {
      this.correlationId = cid;
    }

    getCorrelationId() {
      return this.correlationId;
    }

    enqueue(event) {
      const payload = {
        correlation_id: this.correlationId,
        timestamp: Date.now() / 1000,
        url: typeof window !== 'undefined' ? window.location.href : 'http://node.local',
        ...event,
      };
      this.queue.push(payload);
      this.scheduleFlush();
    }

    scheduleFlush() {
      if (this.timer) clearTimeout(this.timer);
      this.timer = setTimeout(() => this.flush(), this.debounceMs);
    }

    async flush() {
      if (this.queue.length === 0) return;
      const items = [...this.queue];
      this.queue = [];

      for (const item of items) {
        try {
          const endpoint = `${this.ingestionUrl}/ingest/extension`;
          const rawFetch = this.origFetch || (typeof fetch === 'function' ? fetch : null);
          if (rawFetch) {
            await rawFetch(endpoint, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify(item),
            });
          }
        } catch (err) {
          // Silent warning to prevent disrupting host application flow
          if (typeof console !== 'undefined' && console.warn) {
            console.warn('[AgentTrace Bridge Warning] Ingestion streaming error:', err);
          }
        }
      }
    }

    patchFetch() {
      if (typeof window === 'undefined' || !window.fetch) return;
      const self = this;
      this.origFetch = window.fetch;

      window.fetch = async function (input, init) {
        const targetUrl = typeof input === 'string' ? input : (input && input.url ? input.url : '');

        // Skip intercepting ingestion endpoint calls to avoid recursion loops
        if (targetUrl && targetUrl.includes('/ingest/')) {
          return self.origFetch.apply(this, arguments);
        }

        init = init || {};
        let headers;
        if (init.headers instanceof Headers) {
          headers = init.headers;
        } else if (Array.isArray(init.headers)) {
          headers = new Headers(init.headers);
        } else {
          headers = new Headers(init.headers || {});
        }

        if (!headers.has('X-AgentTrace-Correlation-ID')) {
          headers.set('X-AgentTrace-Correlation-ID', self.correlationId);
        }
        init.headers = headers;

        self.enqueue({
          event_type: 'fetch_request',
          element_id: null,
          dom_delta: {
            method: init.method || 'GET',
            url: targetUrl,
          },
        });

        return self.origFetch.call(this, input, init);
      };
    }

    attachDOMListeners() {
      if (typeof window === 'undefined' || typeof document === 'undefined') return;
      const self = this;

      ['click', 'submit', 'input'].forEach((eventType) => {
        document.addEventListener(
          eventType,
          (e) => {
            const target = e.target;
            const elemId = target ? target.id || target.name || target.tagName : null;
            self.enqueue({
              event_type: `dom_${eventType}`,
              element_id: elemId,
              dom_delta: {
                tagName: target ? target.tagName : null,
                value: eventType === 'input' ? '[REDACTED_INPUT]' : undefined,
              },
            });
          },
          true
        );
      });

      if (typeof MutationObserver !== 'undefined' && document.body) {
        const observer = new MutationObserver((mutations) => {
          let addedCount = 0;
          let removedCount = 0;
          mutations.forEach((m) => {
            addedCount += m.addedNodes.length;
            removedCount += m.removedNodes.length;
          });

          if (addedCount > 0 || removedCount > 0) {
            self.enqueue({
              event_type: 'dom_mutation',
              element_id: 'body',
              dom_delta: {
                type: 'childList',
                addedCount,
                removedCount,
              },
            });
          }
        });

        observer.observe(document.body, { childList: true, subtree: true });
      }
    }
  }

  const defaultBridge = new AgentTraceBridge();

  if (typeof window !== 'undefined') {
    window.AgentTrace = defaultBridge;
    if (window.__AGENTTRACE_AUTO_INIT__ !== false) {
      defaultBridge.init();
    }
  }

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = { AgentTrace: defaultBridge, AgentTraceBridge, generateUUIDv7 };
  }
})();
