import { cleanup, render, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { TutorRoom } from "@/components/chat/TutorRoom";
import fixture from "../fixtures/room/session-s15.json";
import { installFakeCanvas } from "../helpers/fakeCanvas";

// Spec: specs/features/tutor/problem-card-history.md AC-8 · every request goes to a mocked fetch.
const API = "http://api.test";
const PREP = "11111111-1111-4111-8111-111111111111";
const SESSION = "22222222-2222-4222-8222-222222222222";
const P1 = { problem_id: "p1", text_latex: "x^2 - 49", difficulty: 1, purpose: "probe" };

const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });

const history = [
  { id: "a1", role: "tutor", content: "เริ่มที่ผลต่างกำลังสองนะ", card: null, input_mode: null, attachment_path: null, attachment_name: null, created_at: "2026-11-17T09:00:01Z" },
  { id: "a2", role: "card", content: null, card: { problem: P1 }, input_mode: null, attachment_path: null, attachment_name: null, created_at: "2026-11-17T09:00:02Z" },
];

beforeEach(() => {
  installFakeCanvas();
  vi.stubEnv("NEXT_PUBLIC_API_URL", API);
});

afterEach(() => {
  cleanup();
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
});

describe("TutorRoom · back into a room with a saved problem card", () => {
  it("TM13 reopening the open session shows the problem card and the canvas (AC-8)", async () => {
    const calls: string[] = [];
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL, init: RequestInit = {}) => {
        const key = `${(init.method ?? "GET").toUpperCase()} ${String(input).replace(API, "")}`;
        calls.push(key);
        if (key === `GET /exam-preps/${PREP}/sessions/active`) return json({ session_id: SESSION });
        if (key === `GET /sessions/${SESSION}`) return json({ ...fixture, session_id: SESSION, messages: history });
        throw new Error(`unexpected request ${key}`);
      }),
    );

    const utils = render(<TutorRoom prepId={PREP} />);

    const card = await waitFor(() => utils.getByRole("region", { name: "โจทย์" }));
    expect(card.textContent).toContain("x^2 - 49");
    expect(utils.container.querySelector('[role="form"][aria-label="เขียนคำตอบ"]')).toBeTruthy();
    expect(calls).not.toContain(`POST /exam-preps/${PREP}/sessions`);
  });
});
