import { act } from "@testing-library/react";
import { vi } from "vitest";
import type { components } from "@/lib/api";

// Shared by UploadPage.test.tsx and ProgressPage.test.tsx (spec: specs/features/exam-prep/upload-page.md).

export const API = "http://api.test";
export const PREP = "p1";
/** The tests replace POLL_MS with this (vi.mock of "@/components/materials/poll"). */
export const TEST_POLL_MS = 20;

export type Material = components["schemas"]["Material"];
export type Ingestion = components["schemas"]["Ingestion"];

export const json = (body: unknown, status = 200, headers: Record<string, string> = {}) =>
  new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json", ...headers } });
export const apiError = (status: number, code: string) => () => json({ error: { code, message: "x" } }, status);

export const material = (id: string, overrides: Partial<Material> = {}): Material => ({
  id,
  file_name: `${id}.pdf`,
  kind: null,
  kind_confidence: null,
  kind_confirmed: false,
  user_note: null,
  status: "uploaded",
  error: null,
  ...overrides,
});

/** A file of `size` bytes without allocating them (jsdom's File takes its size from the parts). */
export function file(name: string, size: number, type: string): File {
  const f = new File(["x"], name, { type });
  Object.defineProperty(f, "size", { value: size });
  return f;
}

export type Handler = () => Response | Promise<Response>;
export type Call = { key: string; init: RequestInit };

/**
 * fetch mock routed by "METHOD path" (API paths without the base URL, other URLs whole). A list
 * gives one response per call and repeats its last one, so a page can poll it.
 */
export function mockApi(routes: Record<string, Handler | Handler[]>) {
  const calls: Call[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL, init: RequestInit = {}) => {
      const key = `${(init.method ?? "GET").toUpperCase()} ${String(input).replace(API, "")}`;
      calls.push({ key, init });
      const route = routes[key];
      if (!route) throw new Error(`unexpected request ${key}`);
      const handler = Array.isArray(route) ? (route.length > 1 ? route.shift() : route[0]) : route;
      if (!handler) throw new Error(`no response for ${key}`);
      return handler();
    }),
  );
  return {
    calls,
    keys: () => calls.map((c) => c.key),
    count: (key: string) => calls.filter((c) => c.key === key).length,
  };
}

/** A response the test releases by hand. */
export function pending() {
  let release!: (r: Response) => void;
  const promise = new Promise<Response>((r) => (release = r));
  return { handler: () => promise, release: (r: Response) => act(async () => release(r)) };
}

/** Real time for `n` polls of TEST_POLL_MS, inside act so React settles. */
export const polls = (n: number) => act(() => new Promise<void>((r) => setTimeout(r, n * TEST_POLL_MS + 5)));
