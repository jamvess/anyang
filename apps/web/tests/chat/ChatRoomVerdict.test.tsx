import { act, cleanup, fireEvent, render, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ChatRoom } from "@/components/chat/ChatRoom";
import type { RoomData } from "@/components/chat/types";
import type { SSEEvent } from "@/lib/sse";
import fixture from "../fixtures/room/session-s15.json";

// Spec: specs/features/check/verdict-mark.md
const room = fixture as RoomData;
const MARK = "ผลตรวจ";
const CARD = "อ่านได้แบบนี้ ถูกไหม";
const OCR2 = {
  lines: [
    { latex: "x^2 - 5x + 6", confidence: 0.97 },
    { latex: "= (x - 2)(x + 3)", confidence: 0.91 },
  ],
};

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

type Item = { event: SSEEvent } | { end: true };

/** A stream source the test drives event by event. Each call opens a new stream. */
function controlled<Args extends unknown[]>() {
  let items: Item[] = [];
  let wake: (() => void) | null = null;

  const fn = vi.fn((..._args: Args) => {
    items = [];
    const own = items;
    return (async function* () {
      while (true) {
        while (own.length === 0) await new Promise<void>((r) => (wake = r));
        const item = own.shift()!;
        if ("end" in item) return;
        yield item.event;
      }
    })();
  });

  const step = async (item: Item) => {
    items.push(item);
    wake?.();
    wake = null;
    await act(async () => void (await new Promise((r) => setTimeout(r, 0))));
  };

  return {
    fn,
    token: (speaker: "tutor" | "buddy", text: string) => step({ event: { event: "token", data: { speaker, text } } }),
    event: (event: string, data: unknown = {}) => step({ event: { event, data } }),
    verdict: (verdict: string, first_wrong_line: number | null, error_type: string | null) =>
      step({ event: { event: "verdict", data: { verdict, first_wrong_line, error_type } } }),
    done: () => step({ event: { event: "done", data: {} } }),
  };
}

function setup() {
  const send = controlled<[unknown, AbortSignal]>();
  const confirm = controlled<[string[], AbortSignal]>();
  const utils = render(<ChatRoom room={room} sendMessage={send.fn} confirmOcr={confirm.fn} imagesEnabled />);
  const input = utils.getByLabelText("พิมพ์ตอบ") as HTMLTextAreaElement;
  const sendButton = () => utils.getByRole("button", { name: "ส่ง" });

  const sendText = async (text: string) => {
    fireEvent.change(input, { target: { value: text } });
    await act(async () => void fireEvent.click(sendButton()));
  };
  const sendPhoto = async () => {
    const photo = new File(["x"], "วิธีทำ.jpg", { type: "image/jpeg" });
    fireEvent.change(utils.container.querySelector('input[type="file"]')!, { target: { files: [photo] } });
    await act(async () => void fireEvent.click(sendButton()));
  };

  const SELECTOR = "[data-role], [role=region], [role=group], [data-verdict]";
  const initial = utils.container.querySelectorAll(SELECTOR).length;
  /** Bubbles, cards and marks after the fixture's history, in screen order. */
  const items = () =>
    [...utils.container.querySelectorAll<HTMLElement>(SELECTOR)]
      .slice(initial)
      .map((el) => el.getAttribute("data-role") ?? el.getAttribute("aria-label"));
  const marks = () => utils.queryAllByRole("status", { name: MARK });
  const tutors = () => [...utils.container.querySelectorAll<HTMLElement>('[data-role="tutor"]')];

  return { ...utils, send, confirm, sendText, sendPhoto, items, marks, tutors };
}

describe("ChatRoom verdict mark", () => {
  // AC-6
  it("AM05 a verdict before the tutor's words shows the mark between the answer and the reply", async () => {
    const t = setup();

    await t.sendText("(x-7)(x+7)");
    await t.send.verdict("correct", null, null);
    await t.send.token("tutor", "ถูกต้อง");
    await t.send.done();

    expect(t.items()).toEqual(["user", MARK, "tutor"]);
    expect(t.marks()[0].textContent).toContain("✓ ถูก");
    expect(t.tutors().at(-1)?.textContent).toContain("ถูกต้อง");
  });

  // AC-7
  it("AM05 a verdict in the middle of the tutor's words splits the bubble around the mark", async () => {
    const t = setup();

    await t.sendText("(x-2)(x+3)");
    await t.send.token("tutor", "โอเค ");
    await t.send.verdict("incorrect", 2, "sign");
    await t.send.token("tutor", "บรรทัดสองยังไม่ถูก");
    await t.send.done();

    expect(t.items()).toEqual(["user", "tutor", MARK, "tutor"]);
    const [before, after] = t.tutors().slice(-2);
    expect(before.textContent).toContain("โอเค");
    expect(after.textContent).toContain("บรรทัดสองยังไม่ถูก");
    expect(t.marks()[0].textContent).toContain("✗ ยังไม่ถูก · บรรทัด 2");
  });

  // AC-8
  it("AM05 after confirming a handwriting card the mark shows between the card and the tutor", async () => {
    const t = setup();
    await t.sendPhoto();
    await t.send.event("ocr_preview", OCR2);
    await t.send.done();

    const card = t.getByRole("region", { name: CARD });
    await act(async () => void fireEvent.click(within(card).getByRole("button", { name: "ถูกแล้ว ตรวจเลย" })));
    await t.confirm.verdict("incorrect", 2, "sign");
    await t.confirm.token("tutor", "บรรทัดสองยังไม่ถูกนะ");
    await t.confirm.done();

    expect(t.items()).toEqual(["user", CARD, MARK, "tutor"]);
    expect(t.marks()[0].textContent).toContain("✗ ยังไม่ถูก · บรรทัด 2");
    expect(card.textContent).toContain("ยืนยันแล้ว");
  });

  // AC-9
  it("AM05 two answers keep two marks in order and the older one does not change", async () => {
    const t = setup();

    await t.sendText("(x-2)(x+3)");
    await t.send.verdict("incorrect", 1, "sign");
    await t.send.token("tutor", "ลองอีกข้อ");
    await t.send.done();
    await t.sendText("(x-3)(x-4)");
    await t.send.verdict("correct", null, null);
    await t.send.token("tutor", "เยี่ยม");
    await t.send.done();

    expect(t.items()).toEqual(["user", MARK, "tutor", "user", MARK, "tutor"]);
    expect(t.marks().map((m) => m.getAttribute("data-verdict"))).toEqual(["incorrect", "correct"]);
    expect(t.marks()[0].textContent).toContain("✗ ยังไม่ถูก · บรรทัด 1");
  });

  // AC-3 (in the room)
  it("AM06 a no_answer verdict shows no mark and the tutor's words stay one bubble", async () => {
    const t = setup();

    await t.sendText("ไม่รู้");
    await t.send.verdict("incorrect", null, "no_answer");
    await t.send.token("tutor", "ไม่เป็นไร ");
    await t.send.token("tutor", "ดูขั้นแรกก่อนนะ");
    await t.send.done();

    expect(t.marks()).toHaveLength(0);
    expect(t.items()).toEqual(["user", "tutor"]);
    expect(t.tutors().at(-1)?.textContent).toContain("ไม่เป็นไร ดูขั้นแรกก่อนนะ");
  });

  // AC-4 (in the room)
  it.each([[{ verdict: "maybe", first_wrong_line: null, error_type: null }], [{}]])(
    "TM20 an unknown verdict %j shows no mark, keeps the bubble and shows no alert",
    async (payload) => {
      const t = setup();

      await t.sendText("ตอบ");
      await t.send.token("tutor", "ถูก");
      await t.send.event("verdict", payload);
      await t.send.token("tutor", "แล้ว");
      await t.send.done();

      expect(t.marks()).toHaveLength(0);
      expect(t.items()).toEqual(["user", "tutor"]);
      expect(t.tutors().at(-1)?.textContent).toContain("ถูกแล้ว");
      expect(t.queryByRole("alert")).toBeNull();
    },
  );
});
