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

// Spec: specs/features/check/ocr-confirm-card.md AC-21 · body is the proposal in OQ 5 until Junior answers.
describe("lib/httpTransport ocr/confirm", () => {
  it("AM02 posts the confirmed lines to /sessions/{id}/ocr/confirm and yields the SSE reply", async () => {
    vi.stubEnv("NEXT_PUBLIC_API_URL", "http://api.test");
    const fetchMock = vi.fn(async () => sseResponse(fixture("tutor_reply.txt")));
    vi.stubGlobal("fetch", fetchMock);
    const { createHttpOcrConfirm } = await import("@/lib/httpTransport");

    const controller = new AbortController();
    const events: SSEEvent[] = [];
    for await (const e of createHttpOcrConfirm("s1")(["a", "b"], controller.signal)) events.push(e);

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
    expect(url).toBe("http://api.test/sessions/s1/ocr/confirm");
    expect(init.method).toBe("POST");
    expect(init.signal).toBe(controller.signal);
    expect(JSON.parse(init.body as string)).toEqual({ lines: ["a", "b"] });
    expect(events.at(-1)?.event).toBe("done");
  });
});

// Spec: specs/features/tutor/room-photo-send.md AC-5 to AC-13
describe("lib/httpTransport · sending a photo", () => {
  const UPLOAD_URL = "https://storage.test/put/abc";
  const PATH = "t/sessions/S/ab.jpeg";
  const photo = () => new File(["x".repeat(9)], "วิธีทำ.jpg", { type: "image/jpeg" });

  type Call = { method: string; url: string; init: RequestInit };

  /** Answers /uploads, the PUT and /messages; each can be replaced to fail. */
  function mockFetch(
    answers: { uploads?: () => Response; put?: () => Response; stub?: boolean } = {},
  ) {
    const calls: Call[] = [];
    vi.stubEnv("NEXT_PUBLIC_API_URL", "http://api.test");
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL, init: RequestInit = {}) => {
        const url = String(input);
        const method = (init.method ?? "GET").toUpperCase();
        calls.push({ method, url, init });
        if (url.endsWith("/uploads")) {
          if (answers.uploads) return answers.uploads();
          return new Response(JSON.stringify({ upload_url: UPLOAD_URL, path: PATH }), {
            status: 200,
            headers: { "Content-Type": "application/json", ...(answers.stub ? { "X-Stub": "true" } : {}) },
          });
        }
        if (url === UPLOAD_URL) return answers.put ? answers.put() : new Response(null, { status: 200 });
        return sseResponse(fixture("tutor_reply.txt"));
      }),
    );
    return calls;
  }

  async function sendPhoto(text: string | null = null, signal = new AbortController().signal) {
    const { createHttpTransport } = await import("@/lib/httpTransport");
    const events: SSEEvent[] = [];
    for await (const e of createHttpTransport("S")({ text, image: photo() }, signal)) events.push(e);
    return events;
  }

  const seen = (calls: Call[]) => calls.map((c) => `${c.method} ${c.url}`);
  const messagesBody = (calls: Call[]) =>
    JSON.parse(calls.find((c) => c.url.endsWith("/messages"))!.init.body as string);

  it("TM06 uploads, puts the file, then sends the message and yields its events (AC-5)", async () => {
    const calls = mockFetch();

    const events = await sendPhoto();

    expect(seen(calls)).toEqual([
      "POST http://api.test/sessions/S/uploads",
      `PUT ${UPLOAD_URL}`,
      "POST http://api.test/sessions/S/messages",
    ]);
    expect(JSON.parse(calls[0].init.body as string)).toEqual({
      kind: "image",
      content_type: "image/jpeg",
      file_name: "วิธีทำ.jpg",
      size_bytes: 9,
    });
    expect(events.length).toBeGreaterThan(0);
  });

  it("TM06 the PUT carries the file and its type, and no Authorization (AC-6)", async () => {
    const calls = mockFetch();

    await sendPhoto();

    const { init } = calls[1];
    expect(init.body).toBeInstanceOf(File);
    expect((init.body as File).name).toBe("วิธีทำ.jpg");
    const headers = new Headers(init.headers);
    expect(headers.get("Content-Type")).toBe("image/jpeg");
    expect(headers.get("Authorization")).toBeNull();
  });

  it("TM06 a photo without text sends only image_path (AC-7)", async () => {
    const calls = mockFetch();

    await sendPhoto();

    expect(messagesBody(calls)).toEqual({ image_path: PATH });
  });

  it("TM06 a photo with text sends both (AC-8)", async () => {
    const calls = mockFetch();

    await sendPhoto("ข้อ 2 ครับ");

    expect(messagesBody(calls)).toEqual({ text: "ข้อ 2 ครับ", image_path: PATH });
  });

  it("TM06 a stub ticket skips the PUT and still sends the path (AC-9)", async () => {
    const calls = mockFetch({ stub: true });

    await sendPhoto();

    expect(seen(calls)).toEqual([
      "POST http://api.test/sessions/S/uploads",
      "POST http://api.test/sessions/S/messages",
    ]);
    expect(messagesBody(calls)).toEqual({ image_path: PATH });
  });

  it("TM06 text without a photo calls no /uploads (AC-10)", async () => {
    const calls = mockFetch();
    const { createHttpTransport } = await import("@/lib/httpTransport");

    const signal = new AbortController().signal;
    const events: SSEEvent[] = [];
    for await (const e of createHttpTransport("S")({ text: "ใช่ๆ", image: null }, signal)) events.push(e);

    expect(seen(calls)).toEqual(["POST http://api.test/sessions/S/messages"]);
    expect(messagesBody(calls)).toEqual({ text: "ใช่ๆ" });
  });

  it.each([
    ["unsupported_type", 422],
    ["file_too_large", 422],
    ["rate_limited", 429],
  ])("TM21 /uploads answering %s throws and sends nothing more (AC-11)", async (code, status) => {
    const calls = mockFetch({
      uploads: () => new Response(JSON.stringify({ error: { code, message: "no" } }), { status }),
    });

    await expect(sendPhoto()).rejects.toThrow();

    expect(seen(calls)).toEqual(["POST http://api.test/sessions/S/uploads"]);
  });

  it("TM06 a failed PUT throws and sends no message (AC-12)", async () => {
    const calls = mockFetch({ put: () => new Response(null, { status: 403 }) });

    await expect(sendPhoto()).rejects.toThrow();

    expect(seen(calls)).toEqual(["POST http://api.test/sessions/S/uploads", `PUT ${UPLOAD_URL}`]);
  });

  it("TM06 every request gets the same abort signal (AC-13)", async () => {
    const calls = mockFetch();
    const controller = new AbortController();

    await sendPhoto(null, controller.signal);

    expect(calls.map((c) => c.init.signal)).toEqual([
      controller.signal,
      controller.signal,
      controller.signal,
    ]);
  });
});
