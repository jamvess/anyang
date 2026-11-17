import { act, cleanup, fireEvent, render, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ChatRoom } from "@/components/chat/ChatRoom";
import type { ChatMessage, RoomData } from "@/components/chat/types";
import type { SSEEvent } from "@/lib/sse";
import fixture from "../fixtures/room/session-s15.json";
import { draw, installFakeCanvas } from "../helpers/fakeCanvas";

// Spec: specs/features/tutor/problem-card-history.md AC-1 to AC-7 · problem cards saved by the API
// as messages (role "card", card = {problem: ProblemEvent}) come back in the room's history.
const CANVAS = "เขียนคำตอบ";
const CANVAS_AREA = "เขียนวิธีทำตรงนี้";
const PROBLEM = "โจทย์";
const PROGRESS = "ความคืบหน้า";
const CARD = "อ่านได้แบบนี้ ถูกไหม";
const P1 = { problem_id: "p1", text_latex: "x^2 - 49", difficulty: 1, purpose: "probe" };
const P2 = { problem_id: "p2", text_latex: "x^2 - 5x + 6", difficulty: 2, purpose: "practice" };
const PROGRESS_CARD = {
  days_left: 5,
  passed: 0,
  total: 1,
  readiness: 0,
  topics: [{ id: "t1", name: "ผลต่างกำลังสอง", stars: 3, level: "not_started", review_due: false, origin: "doc" }],
};
const OCR: SSEEvent = { event: "ocr_preview", data: { lines: [{ latex: "x^2-49", confidence: 0.9 }] } };

let clock = 0;
function message(role: ChatMessage["role"], extra: Partial<ChatMessage> = {}): ChatMessage {
  clock += 1;
  return {
    id: `h${clock}`,
    role,
    content: null,
    card: null,
    input_mode: null,
    attachment_path: null,
    attachment_name: null,
    created_at: new Date(Date.UTC(2026, 10, 17, 9, 0, clock)).toISOString(),
    ...extra,
  };
}
const tutor = (text: string) => message("tutor", { content: text });
const problemCard = (problem: unknown) => message("card", { card: { problem } as ChatMessage["card"] });

async function* stream(...events: SSEEvent[]): AsyncGenerator<SSEEvent> {
  for (const e of events) yield e;
  yield { event: "done", data: {} };
}

const flush = () => act(async () => void (await new Promise((r) => setTimeout(r, 0))));

let inputClicks: HTMLInputElement[];
let scrollIntoView: ReturnType<typeof vi.fn>;

beforeEach(() => {
  clock = 0;
  installFakeCanvas();
  Object.assign(URL, { createObjectURL: vi.fn(() => "blob:test/1"), revokeObjectURL: vi.fn() });
  scrollIntoView = vi.fn(function (this: Element) {});
  Element.prototype.scrollIntoView = scrollIntoView as unknown as Element["scrollIntoView"];
  inputClicks = [];
  vi.spyOn(HTMLInputElement.prototype, "click").mockImplementation(function (this: HTMLInputElement) {
    inputClicks.push(this);
  });
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  const u = URL as unknown as Record<string, unknown>;
  delete u.createObjectURL;
  delete u.revokeObjectURL;
  delete (Element.prototype as unknown as Record<string, unknown>).scrollIntoView;
});

async function open(messages: ChatMessage[], replies: (() => AsyncGenerator<SSEEvent>)[] = [], opening?: AsyncIterable<SSEEvent>) {
  const room = { ...(fixture as RoomData), messages };
  const sendMessage = vi.fn(() => (replies.shift() ?? (() => stream()))());
  const utils = render(<ChatRoom room={room} sendMessage={sendMessage} opening={opening} />);
  await flush();
  const problemCards = () => utils.queryAllByRole("region", { name: PROBLEM });
  const canvasForms = () => [...utils.container.querySelectorAll<HTMLElement>(`[role="form"][aria-label="${CANVAS}"]`)];
  return { ...utils, problemCards, canvasForms };
}

describe("ChatRoom · problem cards from the history", () => {
  it("TM13 a saved problem card shows as a problem card after the tutor's words (AC-1)", async () => {
    const t = await open([tutor("เริ่มที่ผลต่างกำลังสองนะ"), problemCard(P1)]);

    const cards = t.problemCards();
    expect(cards).toHaveLength(1);
    expect(cards[0].textContent).toContain("x^2 - 49");
    const bubble = t.container.querySelector('[data-role="tutor"]')!;
    expect(bubble.compareDocumentPosition(cards[0]) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(t.queryByRole("group", { name: PROGRESS })).toBeNull();
  });

  it("TM15 a saved card without problem is still a progress card (AC-2)", async () => {
    const t = await open([message("card", { card: PROGRESS_CARD as unknown as ChatMessage["card"] }), tutor("สวัสดี")]);

    expect(t.getByRole("group", { name: PROGRESS })).toBeTruthy();
    expect(t.problemCards()).toHaveLength(0);
  });

  it("TM13 TM06 a saved problem card brings the canvas with that problem (AC-3)", async () => {
    const t = await open([tutor("ลองข้อนี้"), problemCard(P1)]);

    const forms = t.canvasForms();
    expect(forms).toHaveLength(1);
    expect(forms[0].textContent).toContain("x^2 - 49");
  });

  it("TM06 two saved problem cards: one canvas, for the second (AC-4)", async () => {
    const t = await open([problemCard(P1), tutor("ถูกต้อง ข้อต่อไป"), problemCard(P2)]);

    expect(t.problemCards()).toHaveLength(2);
    const forms = t.canvasForms();
    expect(forms).toHaveLength(1);
    expect(forms[0].textContent).toContain("x^2 - 5x + 6");
    expect(forms[0].textContent).not.toContain("x^2 - 49");
  });

  it("TM06 a new problem from the stream replaces the saved one on the canvas (AC-5)", async () => {
    const t = await open([tutor("ลองข้อนี้"), problemCard(P1)], [() => stream({ event: "problem", data: P2 })]);

    fireEvent.change(t.getByLabelText("พิมพ์ตอบ"), { target: { value: "x^2-49 = (x-7)(x+7)" } });
    fireEvent.click(t.getByRole("button", { name: "ส่ง" }));
    await flush();
    await flush();

    const forms = t.canvasForms();
    expect(forms).toHaveLength(1);
    expect(forms[0].textContent).toContain("x^2 - 5x + 6");
  });

  it("AM02 a drawing sent for a saved problem goes back to the canvas on retake (AC-6)", async () => {
    const t = await open([tutor("ลองข้อนี้"), problemCard(P1)], [() => stream(OCR)]);

    draw(t.getByLabelText(CANVAS_AREA));
    fireEvent.click(t.getByRole("button", { name: "ส่งคำตอบ" }));
    await flush();
    await flush();
    inputClicks = [];
    scrollIntoView.mockClear();
    const card = t.getAllByRole("region", { name: CARD }).pop()!;
    fireEvent.click(within(card).getByRole("button", { name: "ถ่ายใหม่" }));
    await flush();

    expect(scrollIntoView.mock.instances).toContain(t.canvasForms()[0]);
    expect(inputClicks).toHaveLength(0);
  });

  it.each([
    ["without text_latex", { problem_id: "p1" }],
    ["not an object", "x"],
  ])("TM13 a problem card %s is not shown and the rest of the history is (AC-7)", async (_name, broken) => {
    const t = await open([tutor("สวัสดี"), problemCard(broken), tutor("ลองพิมพ์คำตอบมานะ")]);

    expect(t.problemCards()).toHaveLength(0);
    expect(t.canvasForms()).toHaveLength(0);
    const texts = [...t.container.querySelectorAll('[data-role="tutor"]')].map((b) => b.textContent);
    expect(texts.join(" ")).toContain("สวัสดี");
    expect(texts.join(" ")).toContain("ลองพิมพ์คำตอบมานะ");
  });
});
