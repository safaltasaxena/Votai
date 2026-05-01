
/**
 * src/services/api.js
 * Production-ready API service (works with Cloud Run backend)
 */

const BASE_URL = import.meta.env.VITE_API_URL;

const handleResponse = async (response) => {
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP Error: ${response.status}`);
  }
  return response.json();
};

export const api = {
  // ── Journey ─────────────────────────────────────────

  createUser: async (userData) => {
    const response = await fetch(`${BASE_URL}/journey/onboard`, {
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
    const response = await fetch(url);
    return handleResponse(response);
  },

  advanceStep: async (userId) => {
    const response = await fetch(`${BASE_URL}/journey/${userId}/advance`, {
      method: 'POST',
    });
    return handleResponse(response);
  },

  // ── Elections ───────────────────────────────────────

  getTimeline: async (regionId) => {
    const response = await fetch(`${BASE_URL}/elections/${regionId}/timeline`);
    return handleResponse(response);
  },

  // ── Parties ─────────────────────────────────────────

  getParties: async (regionId) => {
    const response = await fetch(`${BASE_URL}/parties/${regionId}`);
    return handleResponse(response);
  },

  compareParties: async (regionId, language = 'en') => {
    const response = await fetch(`${BASE_URL}/parties/${regionId}/compare?language=${language}`);
    return handleResponse(response);
  },

  // ── AI Chat ─────────────────────────────────────────

  chat: async (message, region_id) => {
    const url = `${BASE_URL}/ai/chat`;

    console.log("API CALL:", url, { message, region_id });

    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, region_id }),
    });

    return handleResponse(response);
  }
};