/**
 * DefendableOS API client (browser + RSC safe).
 *
 * Auth tokens live in localStorage under `defendable.access_token` for the MVP.
 * A future iteration moves them to httpOnly cookies on the same origin.
 */
const BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export const TOKEN_KEY = "defendable.access_token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string | null) {
  if (typeof window === "undefined") return;
  if (token) window.localStorage.setItem(TOKEN_KEY, token);
  else window.localStorage.removeItem(TOKEN_KEY);
}

export interface ApiOptions extends RequestInit {
  json?: unknown;
  formData?: FormData;
  skipAuth?: boolean;
}

export async function api<T = unknown>(path: string, opts: ApiOptions = {}): Promise<T> {
  const headers = new Headers(opts.headers);
  if (opts.json !== undefined) {
    headers.set("Content-Type", "application/json");
  }
  if (!opts.skipAuth) {
    const t = getToken();
    if (t) headers.set("Authorization", `Bearer ${t}`);
  }

  const init: RequestInit = {
    ...opts,
    headers,
    body:
      opts.formData
        ? opts.formData
        : opts.json !== undefined
          ? JSON.stringify(opts.json)
          : opts.body,
  };

  const resp = await fetch(`${BASE}${path}`, init);
  if (!resp.ok) {
    let detail = `${resp.status} ${resp.statusText}`;
    try {
      const body = await resp.json();
      if (typeof body?.detail === "string") detail = body.detail;
    } catch {
      // ignore
    }
    throw new Error(detail);
  }
  if (resp.status === 204) return undefined as T;
  const ct = resp.headers.get("content-type") ?? "";
  return ct.includes("application/json") ? ((await resp.json()) as T) : ((await resp.text()) as unknown as T);
}
