// The user's token on every API request (spec: specs/features/platform/web-login.md §2.3).
// The API decides who may read what (RLS); the browser only sends the Supabase session's token
// and goes to the login page when the API says 401.

import { apiUrl } from "./apiUrl";
import { postSSE, type SSEEvent } from "./sse";
import { createClient } from "./supabase";

/** How the browser leaves for the login page; tests replace `go`. */
export const loginRedirect = {
  go: (href: string) => window.location.assign(href),
};

/**
 * `{Authorization: "Bearer <token>"}` of the Supabase session, or `{}` when there is none or
 * Supabase is not set up (tests, a dev machine on the stubs with AUTH_REQUIRED=false).
 */
export async function authHeaders(): Promise<Record<string, string>> {
  try {
    const { data } = await createClient().auth.getSession();
    const token = data.session?.access_token;
    return token ? { Authorization: `Bearer ${token}` } : {};
  } catch {
    return {};
  }
}

/** `next` only when it is a path of this site, so a link cannot send the user elsewhere. */
export function safeNext(next: string | undefined): string {
  if (!next || !next.startsWith("/") || next.startsWith("//") || next.includes("\\")) return "/";
  return next;
}

function toLogin(): void {
  const here = `${window.location.pathname}${window.location.search}`;
  loginRedirect.go(`/login?next=${encodeURIComponent(here)}`);
}

/** `fetch` to the API with the token; a 401 goes to the login page (the response is returned). */
export async function apiFetch(path: string, init: RequestInit = {}): Promise<Response> {
  const headers = new Headers(init.headers);
  for (const [name, value] of Object.entries(await authHeaders())) headers.set(name, value);
  const res = await fetch(apiUrl(path), { ...init, headers });
  if (res.status === 401) toLogin();
  return res;
}

/** `postSSE` to the API with the token; a 401 goes to the login page, then the stream fails. */
export async function* apiSSE(
  path: string,
  body: unknown,
  init: { signal?: AbortSignal } = {},
): AsyncGenerator<SSEEvent> {
  const headers = await authHeaders();
  try {
    yield* postSSE(apiUrl(path), body, { ...init, headers });
  } catch (error) {
    if ((error as { status?: number }).status === 401) toLogin();
    throw error;
  }
}
