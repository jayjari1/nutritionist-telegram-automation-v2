/**
 * lib/api.ts
 * ----------
 * API helper — wraps fetch with JWT token and error handling.
 * All pages use this to call the FastAPI backend.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface FetchOptions extends RequestInit {
  token?: string;
}

export async function api<T = any>(
  path: string,
  options: FetchOptions = {}
): Promise<T> {
  const { token, ...fetchOptions } = options;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...fetchOptions,
    headers,
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(error.detail || `HTTP ${res.status}`);
  }

  return res.json();
}

// Convenience methods
export const apiGet = <T = any>(path: string, token?: string) =>
  api<T>(path, { method: "GET", token });

export const apiPost = <T = any>(path: string, body: any, token?: string) =>
  api<T>(path, { method: "POST", body: JSON.stringify(body), token });

export const apiPatch = <T = any>(path: string, body: any, token?: string) =>
  api<T>(path, { method: "PATCH", body: JSON.stringify(body), token });

export const apiDelete = <T = any>(path: string, token?: string) =>
  api<T>(path, { method: "DELETE", token });
