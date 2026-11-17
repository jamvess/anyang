import { readFileSync } from "node:fs";
import { join } from "node:path";
import { act, cleanup, fireEvent, render, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { TutorRoom } from "@/components/chat/TutorRoom";
import fixture from "../fixtures/room/session-s15.json";

// Spec: specs/features/tutor/session-end-ui.md AC-14 to AC-16 · every request goes to a mocked fetch.
const API = "http://api.test";
const PREP = "11111111-1111-4111-8111-111111111111";
const SESSION = "22222222-2222-4222-8222-222222222222";
// Session id inside room_session_start.txt (copied from the API stub).
const NEW_SESSION = "5f0c2a8e-3b1d-4c6e-9a7f-2d8b1e4c6a90";

const END = "จบการติว";
const ENDED = "จบการติวรอบนี้แล้ว";
const NEW_ROUND = "ติวรอบใหม่";
// First line of session_end.txt.
const SUMMARY = "วันนี้ทำลิมิต 3 ข้อ ถูก 2 ข้อ ตอนนี้อยู่ระดับกำลังดีแล้ว";

const sse = (name: string) => readFileSync(join(__dirname, "..", "fixtures", "sse", name), "utf8");
const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
const sseResponse = (text: string) => new Response(text, { status: 200, headers: { "Content-Type": "text/event-stream" } });
const apiError = (status: number, code: string) => json({ error: { code, message: code } }, status);
const room = (id: string) => json({ ...fixture, session_id: id, messages: fixture.messages.slice(1, 4).map((m) => ({ ...m, card: null })) });

type Handler = (init: RequestInit) => Response;
type Call = { method: string; url: string };

/** fetch mock routed by "METHOD path"; a route may be a list used one response per call. */
function mockApi(routes: Record<string, Handler | Handler[]>) {
  const calls: Call[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL, init: RequestInit = {}) => {
      const url = String(input);
      const method = (init.method ?? "GET").toUpperCase();
      calls.push({ method, url });
      const key = `${method} ${url.replace(API, "")}`;
      const route = routes[key];
      if (!route) throw new Error(`unexpected request ${key}`);
      const handler = Array.isArray(route) ? route.shift() : route;
      if (!handler) throw new Error(`no more responses for ${key}`);
      return handler(init);
    }),
  );
  const count = (method: string, path: string) => calls.filter((c) => c.method === method && c.url === `${API}${path}`).length;
  return { calls, count };
}

const ACTIVE = `GET /exam-preps/${PREP}/sessions/active`;
const END_PATH = `/sessions/${SESSION}/end`;

async function openRoom(routes: Record<string, Handler | Handler[]>) {
  const api = mockApi({ [`GET /sessions/${SESSION}`]: () => room(SESSION), ...routes });
  const utils = render(<TutorRoom prepId={PREP} />);
  await waitFor(() => expect(utils.getByRole("button", { name: END })).toBeTruthy());
  return { api, utils };
}

async function pressEnd(utils: ReturnType<typeof render>) {
  await act(async () => void fireEvent.click(utils.getByRole("button", { name: END })));
}

beforeEach(() => {
  vi.stubEnv("NEXT_PUBLIC_API_URL", API);
});

afterEach(() => {
  cleanup();
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
});

describe("TutorRoom · ending the session", () => {
  it("PM05 the end button posts to /end once and shows the summary (AC-14)", async () => {
    const { api, utils } = await openRoom({
      [ACTIVE]: () => json({ session_id: SESSION }),
      [`POST ${END_PATH}`]: () => sseResponse(sse("session_end.txt")),
    });

    await pressEnd(utils);

    await waitFor(() => expect(utils.getByText(ENDED)).toBeTruthy());
    expect(api.count("POST", END_PATH)).toBe(1);
    expect(utils.getByText(SUMMARY, { exact: false })).toBeTruthy();
  });

  it("TM13 the new-session link opens a new session of the same prep (AC-15)", async () => {
    const { api, utils } = await openRoom({
      [ACTIVE]: [() => json({ session_id: SESSION }), () => apiError(404, "no_active_session")],
      [`POST ${END_PATH}`]: () => sseResponse(sse("session_end.txt")),
      [`POST /exam-preps/${PREP}/sessions`]: () => sseResponse(sse("room_session_start.txt")),
      [`GET /sessions/${NEW_SESSION}`]: () => room(NEW_SESSION),
    });
    await pressEnd(utils);
    await waitFor(() => expect(utils.getByText(ENDED)).toBeTruthy());

    await act(async () => void fireEvent.click(utils.getByRole("link", { name: NEW_ROUND })));

    await waitFor(() => expect(api.count("GET", `/sessions/${NEW_SESSION}`)).toBe(1));
    expect(api.count("POST", `/exam-preps/${PREP}/sessions`)).toBe(1);
    await waitFor(() => expect(utils.queryByText(ENDED)).toBeNull());
    await waitFor(() =>
      expect((utils.getByRole("textbox", { name: "พิมพ์ตอบ" }) as HTMLTextAreaElement).disabled).toBe(false),
    );
  });

  it("TM13 a 409 session_already_ended from /end locks the room without a summary (AC-16)", async () => {
    const { utils } = await openRoom({
      [ACTIVE]: () => json({ session_id: SESSION }),
      [`POST ${END_PATH}`]: () => apiError(409, "session_already_ended"),
    });

    await pressEnd(utils);

    await waitFor(() => expect(utils.getByText(ENDED)).toBeTruthy());
    expect(utils.queryByText(SUMMARY, { exact: false })).toBeNull();
    expect(utils.queryByRole("alert")).toBeNull();
    expect((utils.getByRole("textbox", { name: "พิมพ์ตอบ" }) as HTMLTextAreaElement).disabled).toBe(true);
  });
});
