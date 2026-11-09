import { act, cleanup, fireEvent, render } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ChatRoom } from "@/components/chat/ChatRoom";
import type { RoomData, SendPayload } from "@/components/chat/types";
import type { SSEEvent } from "@/lib/sse";
import fixture from "../fixtures/room/session-s15.json";
import { draw, installFakeCanvas } from "../helpers/fakeCanvas";

// Spec: specs/features/tutor/answer-canvas.md §2 items 1-3, 12 · AC-1 to AC-3, AC-15.
const room = { ...(fixture as RoomData), messages: [] };
const CANVAS = "เขียนคำตอบ";

function problem(id: string, latex: string): SSEEvent {
  return { event: "problem", data: { problem_id: id, text_latex: latex, difficulty: 3, purpose: "practice" } };
}

async function* stream(...events: SSEEvent[]): AsyncGenerator<SSEEvent> {
  for (const e of events) yield e;
  yield { event: "done", data: {} };
}

const flush = () => act(async () => void (await new Promise((r) => setTimeout(r, 0))));

beforeEach(() => {
  installFakeCanvas();
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

function regionAfter(container: HTMLElement, problemId: string): boolean {
  const card = container.querySelector(`[data-problem-id="${problemId}"]`)!;
  const canvas = container.querySelector(`[role="form"][aria-label="${CANVAS}"]`)!;
  return Boolean(card.compareDocumentPosition(canvas) & Node.DOCUMENT_POSITION_FOLLOWING);
}

describe("ChatRoom answer canvas", () => {
  it("AC-1 TM06 a problem card has the canvas under it; no problem, no canvas", async () => {
    const plain = render(<ChatRoom room={room} opening={stream({ event: "token", data: { speaker: "tutor", text: "สวัสดี" } })} />);
    await flush();
    expect(plain.queryByRole("form", { name: CANVAS })).toBeNull();
    cleanup();

    const { container, getByRole } = render(<ChatRoom room={room} opening={stream(problem("p1", "x^2 - 49"))} />);
    await flush();
    const canvas = getByRole("form", { name: CANVAS });
    for (const name of ["ปากกา", "ยางลบ", "ย้อนกลับ", "ล้าง", "ใส่รูป", "ส่งคำตอบ"]) {
      expect(canvas.querySelector(`button[aria-label="${name}"]`)).not.toBeNull();
    }
    expect(regionAfter(container, "p1")).toBe(true);
  });

  it("AC-2 only the latest problem card has a canvas", async () => {
    const { container, getAllByRole } = render(
      <ChatRoom room={room} opening={stream(problem("p1", "x^2 - 49"), problem("p2", "x^3 - x"))} />,
    );
    await flush();

    expect(getAllByRole("form", { name: CANVAS })).toHaveLength(1);
    expect(regionAfter(container, "p2")).toBe(true);
  });

  it("AC-3 a new problem in a reply brings a fresh, empty canvas", async () => {
    const sendMessage = vi.fn<(payload: SendPayload) => AsyncGenerator<SSEEvent>>(() => stream(problem("p2", "x^3 - x")));
    const { getByRole, getByLabelText } = render(
      <ChatRoom room={room} opening={stream(problem("p1", "x^2 - 49"))} sendMessage={sendMessage} />,
    );
    await flush();
    draw(getByLabelText("เขียนวิธีทำตรงนี้"));
    const sendButton = () => getByRole("button", { name: "ส่งคำตอบ" }) as HTMLButtonElement;
    expect(sendButton().disabled).toBe(false);

    fireEvent.click(sendButton());
    await flush();
    await flush();

    expect(sendButton().disabled).toBe(true); // the canvas under p2 is empty
  });

  it("AC-15 the canvas sends through the room like a photo, and the user bubble names คำตอบ.png", async () => {
    const sendMessage = vi.fn<(payload: SendPayload) => AsyncGenerator<SSEEvent>>(() => stream({ event: "token", data: { speaker: "tutor", text: "ขอดูก่อนนะ" } }));
    const { getByRole, getByLabelText, findByText } = render(
      <ChatRoom room={room} opening={stream(problem("p1", "x^2 - 49"))} sendMessage={sendMessage} />,
    );
    await flush();
    draw(getByLabelText("เขียนวิธีทำตรงนี้"));

    fireEvent.click(getByRole("button", { name: "ส่งคำตอบ" }));
    await flush();

    expect(sendMessage).toHaveBeenCalledTimes(1);
    const payload = sendMessage.mock.calls[0][0];
    expect(payload.text).toBeNull();
    expect(payload.image?.name).toBe("คำตอบ.png");
    expect(await findByText(/คำตอบ\.png/)).toBeTruthy();
  });
});

// Spec §2 B (added 9 Nov): the canvas sits at the end of the chat while a problem is open.
describe("ChatRoom answer canvas · at the end of the chat", () => {
  const canvasForm = (container: HTMLElement) =>
    container.querySelector<HTMLElement>(`[role="form"][aria-label="${CANVAS}"]`)!;
  const lastTutor = (container: HTMLElement) =>
    [...container.querySelectorAll<HTMLElement>('[data-role="tutor"]')].pop()!;
  const tutor = (text: string): SSEEvent => ({ event: "token", data: { speaker: "tutor", text } });

  async function chat(getByLabelText: (t: string) => HTMLElement, getByRole: (r: string, o: { name: string }) => HTMLElement, text: string) {
    fireEvent.change(getByLabelText("พิมพ์ตอบ"), { target: { value: text } });
    fireEvent.click(getByRole("button", { name: "ส่ง" }));
    await flush();
    await flush();
  }

  it("AC-16 AC-17 the canvas follows the latest message, shows the problem, and keeps the drawing", async () => {
    const sendMessage = vi.fn<(payload: SendPayload) => AsyncGenerator<SSEEvent>>(() =>
      stream(tutor("ลองให้ u = x^2 ดูนะ")),
    );
    const { container, getByLabelText, getByRole } = render(
      <ChatRoom room={room} opening={stream(problem("p3", "\frac{d}{dx}(x^2 \sin x)"), tutor("ลองข้อนี้"))} sendMessage={sendMessage} />,
    );
    await flush();
    draw(getByLabelText("เขียนวิธีทำตรงนี้"));

    await chat(getByLabelText, getByRole, "อันนี้ทำไม่เป็น ช่วยหน่อย");

    const form = canvasForm(container);
    expect(lastTutor(container).compareDocumentPosition(form) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(form.textContent).toContain("โจทย์");
    expect(form.querySelector(".katex")).not.toBeNull();
    expect((getByRole("button", { name: "ส่งคำตอบ" }) as HTMLButtonElement).disabled).toBe(false);
  });

  it("AC-18 the same problem again keeps the drawing; a new problem starts empty", async () => {
    const replies = [stream(problem("p1", "x^2 - 49")), stream(problem("p2", "x^3 - x"))];
    const sendMessage = vi.fn<(payload: SendPayload) => AsyncGenerator<SSEEvent>>(() => replies.shift()!);
    const { getByLabelText, getByRole } = render(
      <ChatRoom room={room} opening={stream(problem("p1", "x^2 - 49"))} sendMessage={sendMessage} />,
    );
    await flush();
    const sendAnswer = () => getByRole("button", { name: "ส่งคำตอบ" }) as HTMLButtonElement;
    draw(getByLabelText("เขียนวิธีทำตรงนี้"));

    await chat(getByLabelText, getByRole, "x^2-49");
    expect(sendAnswer().disabled).toBe(false);

    await chat(getByLabelText, getByRole, "ต่อ");
    expect(sendAnswer().disabled).toBe(true);
  });
});
