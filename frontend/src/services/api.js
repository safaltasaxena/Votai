/**
 * src/services/api.js
 * Production-ready API service (Cloud Run optimized)
 */

const BASE_URL = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '');

// Debug log (helps in prod)
if (!BASE_URL) {
  console.error("CRITICAL: VITE_API_URL is not defined. API calls will fail.");
}

const handleResponse = async (response) => {
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: `HTTP ${response.status}` }));
    throw new Error(error.detail || error.message || 'API request failed');
  }
  return response.json();
};

/**
 * Cloud Run optimized fetch:
 * - Longer timeout (handles cold starts)
 * - Retry on failure (except AbortError)
 */
const safeFetch = async (url, options = {}, retries = 1) => {
  // 🔥 KEY FIX: dynamic timeout (dev vs prod)
  const timeout = import.meta.env.DEV ? 10000 : 25000;

  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeout);

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
    });

    clearTimeout(id);
    return response;

  } catch (err) {
    clearTimeout(id);

    // Retry only if NOT aborted
    if (retries > 0 && err.name !== 'AbortError') {
      console.warn(`Retrying API call: ${url}`);
      return safeFetch(url, options, retries - 1);
    }

    throw err;
  }
};

export const api = {
  // ── Journey ─────────────────────────────────────────

  createUser: async (userData) => {
    const response = await safeFetch(`${BASE_URL}/journey/onboard`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(userData),
    });
    return handleResponse(response);
  },

  getCurrentStep: async (userId, regionId, message = null) => {
    let url = `${BASE_URL}/journey/${userId}/step?region=${regionId}`;
    if (message) {
      url += `&message=${encodeURIComponent(message)}`;
    }
    const response = await safeFetch(url);
    return handleResponse(response);
  },

  advanceStep: async (userId) => {
    const response = await safeFetch(`${BASE_URL}/journey/${userId}/advance`, {
      method: 'POST',
    });
    return handleResponse(response);
  },

  // ── Elections ───────────────────────────────────────

  getTimeline: async (regionId) => {
    const response = await safeFetch(`${BASE_URL}/elections/${regionId}/timeline`);
    return handleResponse(response);
  },

  // ── Parties ─────────────────────────────────────────

  getParties: async (regionId) => {
    const response = await safeFetch(`${BASE_URL}/parties/${regionId}`);
    return handleResponse(response);
  },

  compareParties: async (regionId, language = 'en') => {
    const response = await safeFetch(`${BASE_URL}/parties/${regionId}/compare?language=${language}`);
    return handleResponse(response);
  },

  // ── AI Chat ─────────────────────────────────────────

  chat: async (message, region_id) => {
    const url = `${BASE_URL}/ai/chat`;

    try {
      const response = await safeFetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message, region_id }),
      });

      const data = await handleResponse(response);

      return {
        message: data.message || data.response || "I've updated your journey information.",
        next_action: data.next_action || "Continue",
        status: "success"
      };

    } catch (error) {
      console.error("Chat API Failure:", error);

      // 🔥 Graceful fallback (no crash, no empty UI)
      return {
        message: "I'm having trouble connecting right now, but you can continue using the guided steps above.",
        next_action: "Continue Journey",
        status: "fallback"
      };
    }
  }
};