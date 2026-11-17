import { apiFetch } from "@/lib/auth";

// The error envelope of api.md Conventions, for the upload and reading pages.
// (ScopeReview and TutorRoom keep their own copy: a shared one in lib/ is a refactor of its own ·
// self-review PR #139 item 9, PR #141 item 9.)

/** A refused request: its status and the API's error code. */
export class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly code: string | null,
  ) {
    super(`API ${status}${code ? ` ${code}` : ""}`);
  }
}

export async function errorCode(res: Response): Promise<string | null> {
  const body = await res.json().catch(() => null);
  return body?.error?.code ?? null;
}

export async function getJSON<T>(path: string, signal?: AbortSignal): Promise<T> {
  const res = await apiFetch(path, { signal });
  if (!res.ok) throw new ApiError(res.status, await errorCode(res));
  return res.json();
}

/** 401: `apiFetch` is already on its way to the login page, so the page shows no error. */
export const isAuthRedirect = (e: unknown) => e instanceof ApiError && e.status === 401;
