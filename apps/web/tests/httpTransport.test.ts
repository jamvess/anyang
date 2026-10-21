import { readFileSync } from "node:fs";
import { join } from "node:path";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { SSEEvent } from "@/lib/sse";

// Spec: specs/features/tutor/room-http.md
const fixture = (name: string) => readFileSync(join(__dirname, "fixtures", "sse", name), "utf8");

function sseResponse(text: string): Response {
  return new Response(text, {
    status: 200,
    headers: { "Content-Type": "text/event-stream" },
  });
}

afterEach(() => {
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
  vi.resetModules();
});

describe("lib/httpTransport", () => {
  it("TM20 posts the text to /sessions/{id}/messages and yields the SSE events in order", async () => {
    vi.stubEnv("NEXT_PUBLIC_API_URL", "http://api.test");
    const fetchMock = vi.fn(async () => sseResponse(fixture("tutor_reply.txt")));
    vi.stubGlobal("fetch", fetchMock);
    const { createHttpTransport } = await import("@/lib/httpTransport");

    const send = createHttpTransport("S");
    const events: SSEEvent[] = [];
    for await (const e of send({ text: "ใช่ๆ", image: null }, new AbortController().signal)) events.push(e);

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
    expect(url).toBe("http://api.test/sessions/S/messages");
    expect(init.method).toBe("POST");
    const headers = new Headers(init.headers);
    expect(headers.get("Content-Type")).toBe("application/json");
    expect(headers.get("Accept")).toBe("text/event-stream");
    expect(JSON.parse(init.body as string)).toEqual({ text: "ใช่ๆ" });
    expect(events.map((e) => e.event)).toEqual(["token", "token", "token", "token", "token", "token", "token", "done"]);
  });

  it("TM20 passes the abort signal to fetch", async () => {
    vi.stubEnv("NEXT_PUBLIC_API_URL", "http://api.test");
    const fetchMock = vi.fn(async () => sseResponse(fixture("tutor_reply.txt")));
    vi.stubGlobal("fetch", fetchMock);
    const { createHttpTransport } = await import("@/lib/httpTransport");

    const controller = new AbortController();
    for await (const _ of createHttpTransport("S")({ text: "x", image: null }, controller.signal)) break;

    const init = (fetchMock.mock.calls[0] as unknown as [string, RequestInit])[1];
    expect(init.signal).toBe(controller.signal);
  });

  it("TM20 a non-2xx response throws so the room shows its send error", async () => {
    vi.stubEnv("NEXT_PUBLIC_API_URL", "http://api.test");
    vi.stubGlobal("fetch", vi.fn(async () => new Response("boom", { status: 500 })));
    const { createHttpTransport } = await import("@/lib/httpTransport");

    const run = async () => {
      for await (const _ of createHttpTransport("S")({ text: "x", image: null }, new AbortController().signal)) {
        // drain
      }
    };
    await expect(run()).rejects.toThrow();
  });

  it("api.md Conventions: importing the module without NEXT_PUBLIC_API_URL does not throw (env is read per call, so next build works)", async () => {
    vi.stubEnv("NEXT_PUBLIC_API_URL", undefined as unknown as string);
    await expect(import("@/lib/httpTransport")).resolves.toBeTruthy();
  });
});
