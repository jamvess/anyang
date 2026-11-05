import { readFileSync } from "node:fs";
import { join } from "node:path";
import { cleanup, fireEvent, render, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { TutorRoom } from "@/components/chat/TutorRoom";
import fixture from "../fixtures/room/session-s15.json";

// Spec: specs/features/tutor/room-photo-send.md AC-14 to AC-19 · every request goes to a mocked fetch.
const API = "http://api.test";
const PREP = "11111111-1111-4111-8111-111111111111";
const SESSION = "22222222-2222-4222-8222-222222222222";

const CARD = "อ่านได้แบบนี้ ถูกไหม";
const CONFIRM = "ถูกแล้ว ตรวจเลย";
const RETAKE = "ถ่ายใหม่";
const SEND_ERROR = "ส่งไม่สำเร็จ ลองส่งอีกทีนะ";
const NO_IMAGES = "ตอนนี้ยังส่งรูปไม่ได้ พิมพ์คำตอบมาก่อนนะ";
// Lines of image_reply.txt, the recorded stub reply.
const LINES = ["x^2 - 5x + 6", "= (x - 2)(x + 3)", "= x^2 + x - 6"];

const sse = (name: string) => readFileSync(join(__dirname, "..", "fixtures", "sse", name), "utf8");

const json = (body: unknown, status = 200, headers: Record<string, string> = {}) =>
  new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json", ...headers } });
const sseResponse = (text: string) =>
  new Response(text, { status: 200, headers: { "Content-Type": "text/event-stream" } });
// The stub's ticket: its URL cannot be used, so the transport skips the PUT (spec §2).
const ticket = () =>
  json(
    { upload_url: "https://stub.invalid/storage/x", path: `t/sessions/${SESSION}/a.jpeg` },
    200,
    { "X-Stub": "true" },
  );

type Handler = (init: RequestInit) => Response;
type Call = { method: string; url: string; init: RequestInit };

/** fetch mock routed by "METHOD path"; a route may be a list used one response per call. */
function mockApi(routes: Record<string, Handler | Handler[]>) {
  const calls: Call[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL, init: RequestInit = {}) => {
      const url = String(input);
      const method = (init.method ?? "GET").toUpperCase();
      calls.push({ method, url, init });
      const key = `${method} ${url.replace(API, "")}`;
      const route = routes[key];
      if (!route) throw new Error(`unexpected request ${key}`);
      const handler = Array.isArray(route) ? route.shift() : route;
      if (!handler) throw new Error(`no more responses for ${key}`);
      return handler(init);
    }),
  );
  const count = (method: string, path: string) =>
    calls.filter((c) => c.method === method && c.url === `${API}${path}`).length;
  return { calls, count };
}

const UPLOADS = `POST /sessions/${SESSION}/uploads`;
const MESSAGES = `POST /sessions/${SESSION}/messages`;
const OCR_CONFIRM = `POST /sessions/${SESSION}/ocr/confirm`;

const OPEN_ROOM: Record<string, Handler> = {
  [`GET /exam-preps/${PREP}/sessions/active`]: () => json({ session_id: SESSION }),
  [`GET /sessions/${SESSION}`]: () =>
    json({
      ...fixture,
      session_id: SESSION,
      messages: fixture.messages.slice(1, 4).map((m) => ({ ...m, card: null })),
    }),
};

async function openRoom(routes: Record<string, Handler | Handler[]> = {}) {
  const api = mockApi({ ...OPEN_ROOM, ...routes });
  const utils = render(<TutorRoom prepId={PREP} />);
  await waitFor(() => expect(utils.container.querySelectorAll("[data-role]").length).toBe(3));
  return { api, utils };
}

function pickPhoto(utils: ReturnType<typeof render>, name = "วิธีทำ.jpg") {
  const input = utils.container.querySelector('input[type="file"]') as HTMLInputElement;
  fireEvent.change(input, { target: { files: [new File(["x"], name, { type: "image/jpeg" })] } });
}

function send(utils: ReturnType<typeof render>) {
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

describe("TutorRoom · sending a photo", () => {
  it("TM06 picking a photo attaches it and calls no API (AC-14)", async () => {
    const { api, utils } = await openRoom();
    const before = api.calls.length;

    pickPhoto(utils);

    expect(utils.getByText("วิธีทำ.jpg")).toBeTruthy();
    expect(utils.getByRole("button", { name: "เอารูปออก" })).toBeTruthy();
    expect(utils.queryByText(NO_IMAGES)).toBeNull();
    expect(api.calls.length).toBe(before);
  });

  it("AM02 sending shows the user's file name, then the card with every line (AC-15)", async () => {
    const { utils } = await openRoom({
      [UPLOADS]: ticket,
      [MESSAGES]: () => sseResponse(sse("image_reply.txt")),
    });

    pickPhoto(utils);
    send(utils);

    const card = await utils.findByRole("region", { name: CARD });
    const users = [...utils.container.querySelectorAll('[data-role="user"]')];
    expect(users.at(-1)!.textContent).toContain("วิธีทำ.jpg");
    LINES.forEach((_, i) => {
      expect(within(card).getByRole("button", { name: `แก้บรรทัด ${i + 1}` })).toBeTruthy();
    });
    // AM-01: each line is rendered as math.
    expect(card.querySelectorAll(".katex").length).toBe(LINES.length);
  });

  it("AM02 confirming posts the lines in order, then shows the verdict and the tutor (AC-16)", async () => {
    const { api, utils } = await openRoom({
      [UPLOADS]: ticket,
      [MESSAGES]: () => sseResponse(sse("image_reply.txt")),
      [OCR_CONFIRM]: () => sseResponse(sse("ocr_confirm.txt")),
    });
    pickPhoto(utils);
    send(utils);
    const card = await utils.findByRole("region", { name: CARD });

    fireEvent.click(within(card).getByRole("button", { name: CONFIRM }));

    await waitFor(() => expect(utils.getByText(/ยังไม่ถูก/)).toBeTruthy());
    const call = api.calls.find((c) => c.url === `${API}/sessions/${SESSION}/ocr/confirm`)!;
    expect(JSON.parse(call.init.body as string)).toEqual({ lines: LINES });
    await waitFor(() => expect(utils.container.textContent).toContain("บรรทัด 2 เครื่องหมายสลับกัน"));
    await waitFor(() => expect(within(card).queryByRole("button", { name: CONFIRM })).toBeNull());
  });

  it("TM06 a refused upload shows the send error and sends no message (AC-17)", async () => {
    const { api, utils } = await openRoom({
      [UPLOADS]: () => json({ error: { code: "unsupported_type", message: "no" } }, 422),
    });

    pickPhoto(utils);
    send(utils);

    expect((await utils.findByRole("alert")).textContent).toContain(SEND_ERROR);
    const users = [...utils.container.querySelectorAll('[data-role="user"]')];
    expect(users.at(-1)!.textContent).toContain("วิธีทำ.jpg");
    expect(utils.queryByRole("region", { name: CARD })).toBeNull();
    expect(api.count("POST", `/sessions/${SESSION}/messages`)).toBe(0);
    expect((utils.getByLabelText("พิมพ์ตอบ") as HTMLTextAreaElement).disabled).toBe(false);
  });

  it("AM02 retaking sends a new photo: a new upload, a new card, the old card locked (AC-18)", async () => {
    const { api, utils } = await openRoom({
      [UPLOADS]: [ticket, ticket],
      [MESSAGES]: [() => sseResponse(sse("image_reply.txt")), () => sseResponse(sse("image_reply.txt"))],
    });
    pickPhoto(utils);
    send(utils);
    const first = await utils.findByRole("region", { name: CARD });

    fireEvent.click(within(first).getByRole("button", { name: RETAKE }));
    pickPhoto(utils, "ใหม่.jpg");
    send(utils);

    await waitFor(() => expect(api.count("POST", `/sessions/${SESSION}/uploads`)).toBe(2));
    await waitFor(() => expect(api.count("POST", `/sessions/${SESSION}/messages`)).toBe(2));
    await waitFor(() => expect(utils.getAllByRole("region", { name: CARD }).length).toBe(2));
    const [old, latest] = utils.getAllByRole("region", { name: CARD });
    expect(within(old).queryByRole("button", { name: CONFIRM })).toBeNull();
    expect(within(latest).getByRole("button", { name: CONFIRM })).toBeTruthy();
  });

  it("TM06 the whole path has no answer choice buttons (AC-19)", async () => {
    const { utils } = await openRoom({
      [UPLOADS]: ticket,
      [MESSAGES]: () => sseResponse(sse("image_reply.txt")),
    });

    pickPhoto(utils);
    send(utils);
    const card = await utils.findByRole("region", { name: CARD });

    const names = within(card)
      .getAllByRole("button")
      .map((b) => b.getAttribute("aria-label") ?? b.textContent);
    const allowed = [CONFIRM, RETAKE, ...LINES.map((_, i) => `แก้บรรทัด ${i + 1}`)];
    expect(names.sort()).toEqual(allowed.sort());
  });
});
