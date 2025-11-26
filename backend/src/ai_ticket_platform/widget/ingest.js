(() => {
  const ENDPOINT = "http://localhost:8000/api/external/collect";

  let intentId = null;
  let variant = null;
  let resolutionTimeout = null;

  // -------------------------------------
  // Utils
  // -------------------------------------

  function getIntentId() {
    try {
      const el = document.querySelector("[data-intent]");
      if (el && el.dataset.intent) return el.dataset.intent;

      if (window.SupportAI && window.SupportAI.intent)
        return window.SupportAI.intent;

      console.warn("SupportAI: Missing intent ID");
      return null;
    } catch (e) {
      console.error("SupportAI intent read failed", e);
      return null;
    }
  }

  function getVariant(intentId) {
    const key = `supportAI_variant_${intentId}`;
    let v = localStorage.getItem(key);
    if (!v) {
      v = Math.random() < 0.5 ? "A" : "B";
      localStorage.setItem(key, v);
    }
    return v;
  }

  function sendEvent(type, payload) {
    const body = JSON.stringify({ type, ...payload });
  
    fetch(ENDPOINT, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body
    }).catch((err) => console.error("SupportAI event failed:", type, err));
  }
  

  // -------------------------------------
  // Public API: Ticket Created
  // -------------------------------------

  function ticketCreated() {
    if (!intentId || !variant) return;

    // Cancel the resolution timer → user is NOT resolved
    if (resolutionTimeout) {
      clearTimeout(resolutionTimeout);
      resolutionTimeout = null;
    }

    // Send explicit ticket-created event
    sendEvent("ticket_created", {
      intent_id: intentId,
      variant
    });
  }

  // -------------------------------------
  // Init Flow
  // -------------------------------------

  function init() {
    intentId = getIntentId();
    if (!intentId) return;

    variant = getVariant(intentId);

    // Expose API for customer to call
    window.SupportAI = window.SupportAI || {};
    window.SupportAI.intent = intentId;
    window.SupportAI.variant = variant;
    window.SupportAI.ticketCreated = ticketCreated;

    // Send impression immediately
    sendEvent("impression", { intent_id: intentId, variant });

    // Schedule "resolution" (only if not cancelled by a ticket)
    resolutionTimeout = setTimeout(() => {
      sendEvent("resolution", {
        intent_id: intentId,
        variant
      });
    }, 10 * 60 * 1000); // 10 minutes
  }

  // Run on page ready
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
