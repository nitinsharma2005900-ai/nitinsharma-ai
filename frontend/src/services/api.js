const API_BASE = '/api';

export const api = {
  // Chat
  async chat({ query, userId = 'usr_99', sessionId = 'session_001' }) {
    const res = await fetch(`${API_BASE}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, user_id: userId, session_id: sessionId }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Chat request failed: ${res.statusText}`);
    }
    return res.json();
  },

  // Documents
  async getDocuments() {
    const res = await fetch(`${API_BASE}/documents`);
    if (!res.ok) throw new Error('Failed to fetch documents');
    return res.json();
  },

  async uploadDocument(file) {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API_BASE}/documents/upload`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Upload failed: ${res.statusText}`);
    }
    return res.json();
  },

  async deleteDocument(documentId) {
    const res = await fetch(`${API_BASE}/documents/${documentId}`, {
      method: 'DELETE',
    });
    if (!res.ok) throw new Error('Failed to delete document');
    return res.json();
  },

  // Semantic Memory
  async getUserMemories(userId = 'usr_99') {
    const res = await fetch(`${API_BASE}/users/${userId}/memories`);
    if (!res.ok) throw new Error('Failed to fetch user memories');
    return res.json();
  },

  async clearMemories(userId = 'usr_99') {
    const res = await fetch(`${API_BASE}/memory/clear`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: userId }),
    });
    if (!res.ok) throw new Error('Failed to clear memories');
    return res.json();
  },

  async deleteMemory(userId, memoryId) {
    const res = await fetch(`${API_BASE}/users/${userId}/memories/${memoryId}`, {
      method: 'DELETE',
    });
    if (!res.ok) throw new Error('Failed to delete memory');
    return res.json();
  },

  // System Health
  async getHealth() {
    const res = await fetch(`${API_BASE}/health`);
    if (!res.ok) throw new Error('System health check failed');
    return res.json();
  },

  // Analytics Inspection
  async inspectRetrieval(query, userId = 'usr_99') {
    const res = await fetch(`${API_BASE}/analytics/inspect`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, user_id: userId }),
    });
    if (!res.ok) throw new Error('Failed to inspect retrieval pipeline');
    return res.json();
  },
};
