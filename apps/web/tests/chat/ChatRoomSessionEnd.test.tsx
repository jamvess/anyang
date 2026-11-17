import { act, cleanup, fireEvent, render, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ChatRoom } from "@/components/chat/ChatRoom";
import type { EndSession, RoomData, SendMessage } from "@/components/chat/types";
import type { SSEEvent } from "@/lib/sse";
import fixture from "../fixtures/room/session-s15.json";
import { draw, installFakeCanvas } from "../helpers/fakeCanvas";

// Spec: specs/features/tutor/session-end-ui.md AC-1 to AC-13 · May decided §2 on 2026-11-17.
const room = { ...(fixture as RoomData), messages: [] };
const END = "จบการติว";
const ENDED = "จบการติวรอบนี้แล้ว";
const NEW_SESSION = "ติวรอบใหม่";
const BACK_HOME = "กลับหน้าหลัก";
const EXIT = "ออกจากห้องติว";
const SEND_ERROR = "ส่งไม่สำเร็จ ลองส่งอีกทีนะ";
const TYPING = "กำลังพิมพ์";
const CARD = "อ่านได้แบบนี้ ถูกไหม";
const L1 = "วันนี้ทำลิมิต 3 ข้อ ถูก 2 ข้อ ตอนนี้อยู่ระดับกำลังดีแล้ว";
const L2 = "ครั้งหน้าลองลิมิตที่มีรากอีกสักข้อ";

const PROBLEM: SSEEvent = {
  event: "problem",
  data: { problem_id: "p1", text_latex: "x^2 - 49", difficulty: 1, purpose: "probe" },
};
const OCR: SSEEvent = { event: "ocr_preview", data: { lines: [{ latex: "x^2-49", confidence: 0.9 }] } };
const DONE: SSEEvent = { event: "done", data: {} };
const summary = (...lines: string[]): SSEEvent => ({ event: "session_end", data: { summary_lines: lines } });

async function* stream(...events: SSEEvent[]): AsyncGenerator<SSEEvent> {
  for (const e of events) yield e;
}

async function* failing(error: unknown, ...before: SSEEvent[]): AsyncGenerator<SSEEvent> {
  for (const e of before) yield e;
  throw error;
}

/** A stream the test feeds one event at a time. */
function controlled() {
  const queue: SSEEvent[] = [];
  let wake: (() => void) | null = null;
  let closed = false;
  async function* events(): AsyncGenerator<SSEEvent> {
    for (;;) {
      if (queue.length) yield queue.shift()!;
      else if (closed) return;
      else await new Promise<void>((r) => (wake = r));
    }
  }
  const poke = () => {
    wake?.();
    wake = null;
  };
  return {
    events,
    push: (e: SSEEvent) => act(async () => void (queue.push(e), poke(), await flushPromises())),
    close: () => act(async () => void ((closed = true), poke(), await flushPromises())),
  };
}

const flushPromises = () => new Promise((r) => setTimeout(r, 0));
const flush = () => act(async () => void (await flushPromises()));

beforeEach(() => {
  installFakeCanvas();
  // jsdom has no scrollIntoView (the canvas uses it).
  Element.prototype.scrollIntoView = vi.fn() as unknown as Element["scrollIntoView"];
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  delete (Element.prototype as unknown as Record<string, unknown>).scrollIntoView;
});

type Setup = {
  end?: () => AsyncIterable<SSEEvent>;
  opening?: AsyncIterable<SSEEvent>;
  replies?: (() => AsyncIterable<SSEEvent>)[];
  withEnd?: boolean;
};

async function setup({ end = () => stream(summary(L1, L2), DONE), opening = stream(PROBLEM, DONE), replies = [], withEnd = true }: Setup = {}) {
  const endSession = vi.fn<EndSession>(() => end());
  const sendMessage = vi.fn<SendMessage>(() => (replies.shift() ?? (() => stream(DONE)))());
  const utils = render(
    <ChatRoom room={room} opening={opening} sendMessage={sendMessage} {...(withEnd ? { endSession } : {})} />,
  );
  await flush();
  const button = (name: string) => utils.getByRole("button", { name }) as HTMLButtonElement;
  const input = () => utils.getByRole("textbox", { name: "พิมพ์ตอบ" }) as HTMLTextAreaElement;
  const tutorBubbles = () => [...utils.container.querySelectorAll('[data-role="tutor"]')];
  const pressEnd = async () => {
    await act(async () => void fireEvent.click(button(END)));
    await flush();
  };
  return { ...utils, endSession, sendMessage, button, input, tutorBubbles, pressEnd };
}

function expectEnded(t: Awaited<ReturnType<typeof setup>>) {
  expect(t.input().disabled).toBe(true);
  expect(t.button("ส่ง").disabled).toBe(true);
  expect(t.button("แนบรูป").disabled).toBe(true);
  expect(t.button(END).disabled).toBe(true);
  expect(t.getByRole("status").textContent).toContain(ENDED);
  expect(t.getByRole("link", { name: BACK_HOME }).getAttribute("href")).toBe("/");
  expect(t.getByRole("link", { name: NEW_SESSION })).toBeTruthy();
  expect(t.getByRole("link", { name: EXIT })).toBeTruthy();
}

function expectUsable(t: Awaited<ReturnType<typeof setup>>) {
  expect(t.getByRole("alert").textContent).toContain(SEND_ERROR);
  expect(t.input().disabled).toBe(false);
  expect(t.button(END).disabled).toBe(false);
  expect(t.queryByText(ENDED)).toBeNull();
}

describe("ChatRoom · ending the session", () => {
  it("PM05 the summary shows as one tutor bubble at the end of the chat (AC-1)", async () => {
    const t = await setup();
    const before = t.tutorBubbles().length;

    await t.pressEnd();

    expect(t.endSession).toHaveBeenCalledTimes(1);
    const bubbles = t.tutorBubbles();
    expect(bubbles.length).toBe(before + 1);
    const last = bubbles[bubbles.length - 1];
    expect(last.textContent).toContain(`${L1}\n${L2}`);
    const log = t.getByRole("log");
    const items = log.querySelectorAll("li");
    expect(items[items.length - 1]).toBe(last);
  });

  it("PM05 a one-line summary is a bubble with one line (AC-2)", async () => {
    const t = await setup({ end: () => stream(summary(L1), DONE) });

    await t.pressEnd();

    const bubbles = t.tutorBubbles();
    const text = bubbles[bubbles.length - 1].textContent ?? "";
    expect(text).toContain(L1);
    expect(text).not.toContain("\n");
  });

  it("TM13 after the end the inputs are locked and two links lead on (AC-3)", async () => {
    const t = await setup();

    await t.pressEnd();

    expectEnded(t);
  });

  // Changed 2026-11-17 (May): the canvas goes away after the end, so the summary stays last (AC-1).
  it("TM13 after the end the canvas is gone and the problem card stays (AC-4)", async () => {
    const t = await setup();
    draw(t.getByLabelText("เขียนวิธีทำตรงนี้"));
    expect(t.button("ส่งคำตอบ").disabled).toBe(false);

    await t.pressEnd();

    expect(t.queryByLabelText("เขียนวิธีทำตรงนี้")).toBeNull();
    expect(t.queryByRole("button", { name: "ส่งคำตอบ" })).toBeNull();
    expect(t.getByText("x^2 - 49", { exact: false })).toBeTruthy();
  });

  it("TM13 after the end a waiting handwriting card cannot be pressed (AC-5)", async () => {
    const t = await setup({ replies: [() => stream(OCR, DONE)] });
    fireEvent.change(t.input(), { target: { value: "ตอบ" } });
    await act(async () => void fireEvent.click(t.button("ส่ง")));
    await flush();
    const card = t.getByRole("region", { name: CARD });
    expect((within(card).getByRole("button", { name: "ถูกแล้ว ตรวจเลย" }) as HTMLButtonElement).disabled).toBe(false);

    await t.pressEnd();

    const buttons = within(card).getAllByRole("button") as HTMLButtonElement[];
    expect(buttons.length).toBeGreaterThan(0);
    expect(buttons.every((b) => b.disabled)).toBe(true);
  });

  it("PM05 the end button is disabled while the room is answering (AC-6)", async () => {
    const opening = controlled();
    const t = await setup({ opening: opening.events() });

    expect(t.button(END).disabled).toBe(true);

    await opening.push(PROBLEM);
    await opening.push(DONE);

    expect(t.button(END).disabled).toBe(false);
  });

  it("PM05 while ending the room is busy and shows typing until the summary (AC-7)", async () => {
    const reply = controlled();
    const t = await setup({ end: () => reply.events() });

    await t.pressEnd();

    expect(t.button(END).disabled).toBe(true);
    expect(t.input().disabled).toBe(true);
    expect(t.button("ส่ง").disabled).toBe(true);
    expect(t.getByLabelText(TYPING)).toBeTruthy();

    await reply.push(summary(L1, L2));

    expect(t.queryByLabelText(TYPING)).toBeNull();
    const bubbles = t.tutorBubbles();
    expect(bubbles[bubbles.length - 1].textContent).toContain(L1);
  });

  it("TM13 a 409 before any event means the session already ended: locked, no bubble, no alert (AC-8)", async () => {
    const t = await setup({ end: () => failing(Object.assign(new Error("409"), { status: 409 })) });
    const before = t.tutorBubbles().length;

    await t.pressEnd();

    expectEnded(t);
    expect(t.tutorBubbles().length).toBe(before);
    expect(t.queryByRole("alert")).toBeNull();
  });

  it.each([
    ["a 503", () => Object.assign(new Error("503"), { status: 503 })],
    ["an error without status", () => new Error("network")],
  ])("PM05 %s shows the send error and the room stays usable (AC-9)", async (_name, error) => {
    const t = await setup({ end: () => failing(error()) });

    await t.pressEnd();

    expectUsable(t);
  });

  it.each([
    ["an error event", () => stream({ event: "error", data: { code: "internal_error", message: "x" } })],
    ["a stream without done", () => stream()],
  ])("PM05 %s is handled like a failure (AC-10)", async (_name, end) => {
    const t = await setup({ end });

    await t.pressEnd();

    expectUsable(t);
  });

  it("PM05 a summary without done stays, with the send error (AC-11)", async () => {
    const t = await setup({ end: () => stream(summary(L1, L2)) });

    await t.pressEnd();

    const bubbles = t.tutorBubbles();
    expect(bubbles[bubbles.length - 1].textContent).toContain(L1);
    expectUsable(t);
  });

  it("TM06 a room without endSession has no end button (AC-12)", async () => {
    const t = await setup({ withEnd: false });

    expect(t.queryByRole("button", { name: END })).toBeNull();
  });

  it("NFR-A1 after the end the focus is on the new-session link (AC-13)", async () => {
    const t = await setup();

    await t.pressEnd();

    expect(document.activeElement).toBe(t.getByRole("link", { name: NEW_SESSION }));
  });
});
