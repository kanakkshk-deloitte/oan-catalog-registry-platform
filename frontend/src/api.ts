const API_BASE = import.meta.env.VITE_API_BASE ?? '/api';

export async function apiCall<T>(path: string, method: string, token?: string, body?: unknown): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    method,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: body ? JSON.stringify(body) : undefined,
  });

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const text = await response.text();
      if (text) {
        const parsed = JSON.parse(text);
        detail = parsed.detail ? String(parsed.detail) : JSON.stringify(parsed);
      }
    } catch {
      // If parsing fails, detail stays as statusText
    }
    throw new Error(detail || 'Request failed');
  }

  const text = await response.text();
  if (!text) return {} as T;
  return JSON.parse(text) as T;
}
