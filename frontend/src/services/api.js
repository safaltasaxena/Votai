/**
 * src/services/api.js
 * 
 * Centralized API service for interacting with the FastAPI backend.
 * Uses the proxy configured in vite.config.js (/api -> http://localhost:8000).
 */

const API_BASE = '/api';

const handleResponse = async (response) => {
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP Error: ${response.status}`);
  }
  return response.json();
};

export const api = {
  // ── Journey ────────────────────────────────────────────────────────────────
  
  createUser: async (userData) => {
    // Backend expects: user_id, age, country, state, language, first_time_voter
    const response = await fetch(`${API_BASE}/journey/onboard`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(userData),
    });
    return handleResponse(response);
  },

  getCurrentStep: async (userId, regionId = 'unknown', message = null) => {
    let url = `${API_BASE}/journey/${userId}/step?region=${regionId}`;
    if (message) {
      url += `&message=${encodeURIComponent(message)}`;
    }
    const response = await fetch(url);
    return handleResponse(response);
  },

  advanceStep: async (userId) => {
    const response = await fetch(`${API_BASE}/journey/${userId}/advance`, {
      method: 'POST',
    });
    return handleResponse(response);
  },

  // ── Elections ──────────────────────────────────────────────────────────────

  getTimeline: async (regionId) => {
    const response = await fetch(`${API_BASE}/elections/${regionId}/timeline`);
    return handleResponse(response);
  },

  // ── Parties ────────────────────────────────────────────────────────────────

  getParties: async (regionId) => {
    const response = await fetch(`${API_BASE}/parties/${regionId}`);
    return handleResponse(response);
  }
};
