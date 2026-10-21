import { readFileSync } from "node:fs";
import { join } from "node:path";
import { act, cleanup, fireEvent, render, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { TutorRoom } from "@/components/chat/TutorRoom";
import fixture from "../fixtures/room/session-s15.json";

// Spec: specs/features/tutor/room-http.md · every request goes to a mocked fetch, never the network.
const API = "http://api.test";
const PREP = "11111111-1111-4111-8111-111111111111";
const SESSION = "22222222-2222-4222-8222-222222222222";
// Session id inside room_session_start.txt (copied from the API stub).
const NEW_SESSION = "5f0c2a8e-3b1d-4c6e-9a7f-2d8b1e4c6a90";

const SEND_ERROR = "ส่งไม่สำเร็จ ลองส่งอีกทีนะ";
const LOAD_ERROR = "เปิดห้องติวไม่สำเร็จ";
const NOT_FOUND = "ไม่พบการเตรียมสอบนี้";
const LOADING = "กำลังเปิดห้องติว…";
const NO_IMAGES = "ตอนนี้ยังส่งรูปไม่ได้ พิมพ์คำตอบมาก่อนนะ";

const sse = (name: string) => readFileSync(join(__dirname, "..", "fixtures", "sse", name), "utf8");

const room = (overrides: Record<string, unknown> = {}) => ({
  ...fixture,
  session_id: SESSION,
  messages: fixture.messages.slice(1, 4).map((m) => ({ ...m, card: null })),
  ...overrides,
});

const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
const notFound = (code: string) => json({ error: { code, message: "not found" } }, 404);
const sseResponse = (text: string) =>
  new Response(text, { status: 200, headers: { "Content-Type": "text/event-stream" } });

/** An SSE response the test writes to chunk by chunk; `close()` ends it without anything more. */
function openStream() {
  let controller!: ReadableStreamDefaultController<Uint8Array>;
  const body = new ReadableStream<Uint8Array>({ start: (c) => void (controller = c) });
  const encoder = new TextEncoder();
  return {
    response: new Response(body, { status: 200, headers: { "Content-Type": "text/event-stream" } }),
    push: (text: string) => act(async () => controller.enqueue(encoder.encode(text))),
    close: () => act(async () => controller.close()),
  };
}

type Handler = (init: RequestInit) => Response | Promise<Response>;
type Call = { method: string; url: string; init: RequestInit };

/** fetch mock routed by "METHOD path"; a route may be a list used one response per call. */
function mockApi(routes: Record<string, Handler | Handler[]>) {
  const calls: Call[] = [];
  const fetchMock = vi.fn(async (input: RequestInfo | URL, init: RequestInit = {}) => {
    const url = String(input);
    const method = (init.method ?? "GET").toUpperCase();
    calls.push({ method, url, init });
    const key = `${method} ${url.replace(API, "")}`;
    const route = routes[key];
    if (!route) throw new Error(`unexpected request ${key}`);
    const handler = Array.isArray(route) ? route.shift() : route;
    if (!handler) throw new Error(`no more responses for ${key}`);
    return handler(init);
  });
  vi.stubGlobal("fetch", fetchMock);
  const count = (method: string, path: string) =>
    calls.filter((c) => c.method === method && c.url === `${API}${path}`).length;
  return { calls, count };
}

const activeOk = () => json({ session_id: SESSION });
const activePath = `/exam-preps/${PREP}/sessions/active`;

function bubbles(container: HTMLElement) {
  return [...container.querySelectorAll("[data-role]")];
}

async function typeAndSend(utils: ReturnType<typeof render>, text: string) {
  fireEvent.change(utils.getByLabelText("พิมพ์ตอบ"), { target: { value: text } });
  fireEvent.click(utils.getByRole("button", { name: "ส่ง" }));
}

beforeEach(() => {
  vi.stubEnv("NEXT_PUBLIC_API_URL", API);
});

afterEach(() => {
  cleanup();
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
});

describe("TutorRoom · opening the room (TM-13)", () => {
  it("TM13 resumes the open session: shows its messages and header and does not start a new session", async () => {
    const api = mockApi({
      [`GET ${activePath}`]: activeOk,
      [`GET /sessions/${SESSION}`]: () => json(room()),
    });
    const utils = render(<TutorRoom prepId={PREP} />);

    await waitFor(() => expect(bubbles(utils.container)).toHaveLength(3));
    expect(utils.getByText(fixture.prep_name)).toBeTruthy();
    expect(utils.getByText(`สอบใน ${fixture.days_left} วัน`)).toBeTruthy();
    expect(api.count("POST", `/exam-preps/${PREP}/sessions`)).toBe(0);
  });

  it("TM13 with no open session it starts one and the opening message streams in without a user bubble", async () => {
    const api = mockApi({
      [`GET ${activePath}`]: () => notFound("no_active_session"),
      [`POST /exam-preps/${PREP}/sessions`]: () => sseResponse(sse("room_session_start.txt")),
      [`GET /sessions/${NEW_SESSION}`]: () => json(room({ session_id: NEW_SESSION, messages: [] })),
    });
    const utils = render(<TutorRoom prepId={PREP} />);

    await waitFor(() => {
      const all = bubbles(utils.container);
      expect(all.map((b) => b.getAttribute("data-role"))).toEqual(["tutor"]);
      expect(all[0].textContent).toContain("สวัสดี");
    });
    expect(utils.getByText(fixture.prep_name)).toBeTruthy();
    expect(api.count("POST", `/exam-preps/${PREP}/sessions`)).toBe(1);
    expect(api.count("GET", `/sessions/${NEW_SESSION}`)).toBe(1);
  });

  it("TM13 the room shows as soon as the session event arrives, typing until the first token, send locked until done", async () => {
    const stream = openStream();
    mockApi({
      [`GET ${activePath}`]: () => notFound("no_active_session"),
      [`POST /exam-preps/${PREP}/sessions`]: () => stream.response,
      [`GET /sessions/${NEW_SESSION}`]: () => json(room({ session_id: NEW_SESSION, messages: [] })),
    });
    const utils = render(<TutorRoom prepId={PREP} />);

    await stream.push(`event: session\ndata: {"session_id": "${NEW_SESSION}"}\n\n`);
    await waitFor(() => expect(utils.getByLabelText("พิมพ์ตอบ")).toBeTruthy());
    expect(utils.getByLabelText("กำลังพิมพ์")).toBeTruthy();
    fireEvent.change(utils.getByLabelText("พิมพ์ตอบ"), { target: { value: "ข้อต่อไป" } });
    expect((utils.getByRole("button", { name: "ส่ง" }) as HTMLButtonElement).disabled).toBe(true);

    await stream.push(`event: token\ndata: {"speaker": "tutor", "text": "สวัสดี"}\n\nevent: done\ndata: {}\n\n`);
    await stream.close();
    await waitFor(() => expect(utils.queryByLabelText("กำลังพิมพ์")).toBeNull());
    expect((utils.getByRole("button", { name: "ส่ง" }) as HTMLButtonElement).disabled).toBe(false);
  });

  it("TM20 a room opened from a new session sends to that session", async () => {
    const api = mockApi({
      [`GET ${activePath}`]: () => notFound("no_active_session"),
      [`POST /exam-preps/${PREP}/sessions`]: () => sseResponse(sse("room_session_start.txt")),
      [`GET /sessions/${NEW_SESSION}`]: () => json(room({ session_id: NEW_SESSION, messages: [] })),
      [`POST /sessions/${NEW_SESSION}/messages`]: () => sseResponse(sse("tutor_reply.txt")),
    });
    const utils = render(<TutorRoom prepId={PREP} />);
    await waitFor(() => expect(bubbles(utils.container)).toHaveLength(1));
    await waitFor(() =>
      expect((utils.getByRole("button", { name: "ส่ง" }) as HTMLButtonElement).disabled).toBe(true),
    );

    await typeAndSend(utils, "ใช่ๆ");

    await waitFor(() => expect(api.count("POST", `/sessions/${NEW_SESSION}/messages`)).toBe(1));
  });

  it("TM13 shows a loading state and no composer while the room is loading", () => {
    mockApi({ [`GET ${activePath}`]: () => new Promise<Response>(() => {}) });
    const utils = render(<TutorRoom prepId={PREP} />);

    expect(utils.getByText(LOADING)).toBeTruthy();
    expect(utils.queryByLabelText("พิมพ์ตอบ")).toBeNull();
  });

  it("TM13 a 404 other than no_active_session shows 'prep not found' with only a link home", async () => {
    const api = mockApi({ [`GET ${activePath}`]: () => notFound("prep_not_found") });
    const utils = render(<TutorRoom prepId={PREP} />);

    const alert = await utils.findByRole("alert");
    expect(alert.textContent).toContain(NOT_FOUND);
    expect(utils.getByRole("link", { name: "กลับหน้าหลัก" }).getAttribute("href")).toBe("/");
    expect(utils.queryByRole("button", { name: "ลองใหม่" })).toBeNull();
    expect(api.count("POST", `/exam-preps/${PREP}/sessions`)).toBe(0);
  });

  it("TM13 a server error shows the load error with retry and home; retry loads the room", async () => {
    mockApi({
      [`GET ${activePath}`]: [() => json({ error: { code: "internal", message: "x" } }, 500), activeOk],
      [`GET /sessions/${SESSION}`]: () => json(room()),
    });
    const utils = render(<TutorRoom prepId={PREP} />);

    const alert = await utils.findByRole("alert");
    expect(alert.textContent).toContain(LOAD_ERROR);
    expect(alert.textContent).not.toContain("x");
    expect(utils.getByRole("link", { name: "กลับหน้าหลัก" }).getAttribute("href")).toBe("/");

    fireEvent.click(utils.getByRole("button", { name: "ลองใหม่" }));
    await waitFor(() => expect(bubbles(utils.container)).toHaveLength(3));
  });

  it("TM13 a network failure while loading shows the load error", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => {
        throw new TypeError("Failed to fetch");
      }),
    );
    const utils = render(<TutorRoom prepId={PREP} />);

    expect((await utils.findByRole("alert")).textContent).toContain(LOAD_ERROR);
  });

  it("TM13 an error event before the session event shows the load error and never loads a room", async () => {
    const api = mockApi({
      [`GET ${activePath}`]: () => notFound("no_active_session"),
      [`POST /exam-preps/${PREP}/sessions`]: () =>
        sseResponse('event: error\ndata: {"code": "ai_unavailable", "message": "timeout"}\n\n'),
    });
    const utils = render(<TutorRoom prepId={PREP} />);

    expect((await utils.findByRole("alert")).textContent).toContain(LOAD_ERROR);
    expect(api.calls.filter((c) => c.url.startsWith(`${API}/sessions/`))).toHaveLength(0);
  });

  it("TM20 an opening stream that ends without done keeps the partial bubble and shows the send error", async () => {
    mockApi({
      [`GET ${activePath}`]: () => notFound("no_active_session"),
      [`POST /exam-preps/${PREP}/sessions`]: () =>
        sseResponse(
          `event: session\ndata: {"session_id": "${NEW_SESSION}"}\n\nevent: token\ndata: {"speaker": "tutor", "text": "สวัส"}\n\n`,
        ),
      [`GET /sessions/${NEW_SESSION}`]: () => json(room({ session_id: NEW_SESSION, messages: [] })),
    });
    const utils = render(<TutorRoom prepId={PREP} />);

    const alert = await utils.findByRole("alert");
    expect(alert.textContent).toContain(SEND_ERROR);
    const all = bubbles(utils.container);
    expect(all).toHaveLength(1);
    expect(all[0].textContent).toContain("สวัส");
  });

  it("TM21 input limits come from the API room data", async () => {
    mockApi({
      [`GET ${activePath}`]: activeOk,
      [`GET /sessions/${SESSION}`]: () => json(room({ limits: { max_message_chars: 50, max_image_mb: 10 } })),
    });
    const utils = render(<TutorRoom prepId={PREP} />);
    await waitFor(() => expect(utils.getByLabelText("พิมพ์ตอบ")).toBeTruthy());

    fireEvent.change(utils.getByLabelText("พิมพ์ตอบ"), { target: { value: "ก".repeat(51) } });

    expect((utils.getByRole("button", { name: "ส่ง" }) as HTMLButtonElement).disabled).toBe(true);
    expect(utils.getByText("ข้อความยาวเกิน 50 ตัวอักษร")).toBeTruthy();
  });
});

describe("TutorRoom · sending (TM-20)", () => {
  async function openRoom(sendRoute: Handler | Handler[]) {
    const api = mockApi({
      [`GET ${activePath}`]: activeOk,
      [`GET /sessions/${SESSION}`]: () => json(room()),
      [`POST /sessions/${SESSION}/messages`]: sendRoute,
    });
    const utils = render(<TutorRoom prepId={PREP} />);
    await waitFor(() => expect(bubbles(utils.container)).toHaveLength(3));
    return { api, utils };
  }

  it("TM20 posts the text as JSON to the session and asks for an event stream", async () => {
    const { api, utils } = await openRoom(() => sseResponse(sse("tutor_reply.txt")));

    await typeAndSend(utils, "(x-7)(x+7)");

    await waitFor(() => expect(api.count("POST", `/sessions/${SESSION}/messages`)).toBe(1));
    const call = api.calls.find((c) => c.method === "POST" && c.url === `${API}/sessions/${SESSION}/messages`)!;
    const headers = new Headers(call.init.headers);
    expect(headers.get("Content-Type")).toBe("application/json");
    expect(headers.get("Accept")).toBe("text/event-stream");
    expect(JSON.parse(call.init.body as string)).toEqual({ text: "(x-7)(x+7)" });
  });

  it("TM20 the streamed reply shows as tutor, buddy, tutor bubbles after the user bubble", async () => {
    const { utils } = await openRoom(() => sseResponse(sse("tutor_reply.txt")));

    await typeAndSend(utils, "ใช่ๆ");

    await waitFor(() => {
      const added = bubbles(utils.container).slice(3);
      expect(added.map((b) => b.getAttribute("data-role"))).toEqual(["user", "tutor", "buddy", "tutor"]);
      expect(added[0].textContent).toContain("ใช่ๆ");
      expect(added[1].textContent).toContain("ถูกแล้ว");
    });
  });

  it("TM20 an HTTP 500 keeps the user bubble and shows the send error", async () => {
    const { utils } = await openRoom(() => new Response("boom", { status: 500 }));

    await typeAndSend(utils, "ใช่ๆ");

    expect((await utils.findByRole("alert")).textContent).toContain(SEND_ERROR);
    const last = bubbles(utils.container).at(-1)!;
    expect(last.getAttribute("data-role")).toBe("user");
  });

  it("TM20 a network failure while sending shows the send error", async () => {
    const { utils } = await openRoom(() => {
      throw new TypeError("Failed to fetch");
    });

    await typeAndSend(utils, "ใช่ๆ");

    expect((await utils.findByRole("alert")).textContent).toContain(SEND_ERROR);
  });

  it("TM20 leaving the room aborts the reply that is still streaming", async () => {
    const stream = openStream();
    const { api, utils } = await openRoom(() => stream.response);

    await typeAndSend(utils, "ใช่ๆ");
    await waitFor(() => expect(api.count("POST", `/sessions/${SESSION}/messages`)).toBe(1));
    const call = api.calls.find((c) => c.method === "POST" && c.url.endsWith("/messages"))!;
    utils.unmount();

    expect(call.init.signal?.aborted).toBe(true);
  });

  it("TM20 leaving the room aborts the opening stream that is still streaming", async () => {
    const stream = openStream();
    const api = mockApi({
      [`GET ${activePath}`]: () => notFound("no_active_session"),
      [`POST /exam-preps/${PREP}/sessions`]: () => stream.response,
      [`GET /sessions/${NEW_SESSION}`]: () => json(room({ session_id: NEW_SESSION, messages: [] })),
    });
    const utils = render(<TutorRoom prepId={PREP} />);
    await stream.push(`event: session\ndata: {"session_id": "${NEW_SESSION}"}\n\n`);
    await waitFor(() => expect(utils.getByLabelText("พิมพ์ตอบ")).toBeTruthy());
    const call = api.calls.find((c) => c.method === "POST" && c.url.endsWith(`/exam-preps/${PREP}/sessions`))!;

    utils.unmount();

    expect(call.init.signal?.aborted).toBe(true);
  });
});

describe("TutorRoom · images (TM-06)", () => {
  it("TM06 picking a photo does not attach it, explains images cannot be sent yet and calls no API", async () => {
    const api = mockApi({
      [`GET ${activePath}`]: activeOk,
      [`GET /sessions/${SESSION}`]: () => json(room()),
    });
    const utils = render(<TutorRoom prepId={PREP} />);
    await waitFor(() => expect(bubbles(utils.container)).toHaveLength(3));
    const before = api.calls.length;

    const file = utils.container.querySelector('input[type="file"]') as HTMLInputElement;
    fireEvent.change(file, { target: { files: [new File(["x"], "วิธีทำ.jpg", { type: "image/jpeg" })] } });

    expect(utils.getByText(NO_IMAGES)).toBeTruthy();
    expect(utils.queryByText("วิธีทำ.jpg")).toBeNull();
    expect(utils.queryByRole("button", { name: "เอารูปออก" })).toBeNull();
    expect(api.calls.length).toBe(before);
    expect(within(utils.container).getByRole("button", { name: "แนบรูป" })).toBeTruthy();
  });
});
