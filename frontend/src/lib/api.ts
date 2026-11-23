/**
 * NexusDB Frontend API Client
 */

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export function getAuthHeaders(): Record<string, string> {
  const token = localStorage.getItem('nexus_token');
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}

export async function login(username: string, password: string) {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Login failed');
  }
  return res.json();
}

export async function fetchMetrics() {
  const res = await fetch(`${API_BASE}/metrics`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error('Failed to load metrics');
  return res.json();
}

export async function fetchAuditLogs(limit = 50, offset = 0, eventType?: string) {
  const url = new URL(`${API_BASE}/audit`);
  url.searchParams.set('limit', limit.toString());
  url.searchParams.set('offset', offset.toString());
  if (eventType) url.searchParams.set('event_type', eventType);

  const res = await fetch(url.toString(), {
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error('Failed to load audit logs');
  return res.json();
}

export async function verifyAuditChain() {
  const res = await fetch(`${API_BASE}/audit/verify`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Chain verification failed');
  }
  return res.json();
}

export async function fetchSchema() {
  const res = await fetch(`${API_BASE}/schema`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error('Failed to load schema catalog');
  return res.json();
}

export async function testRetrievalPlayground(question: string, topK = 8) {
  const res = await fetch(`${API_BASE}/schema/playground`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({ question, top_k: topK }),
  });
  if (!res.ok) throw new Error('Playground retrieval failed');
  return res.json();
}

export async function confirmAction(actionName: string, params: any, confirmationToken: string, idempotencyKey: string) {
  const res = await fetch(`${API_BASE}/actions/confirm`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({
      action_name: actionName,
      parameters: params,
      confirmation_token: confirmationToken,
      idempotency_key: idempotencyKey,
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to execute action');
  }
  return res.json();
}
