import { act, cleanup, fireEvent, render, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ChatRoom } from "@/components/chat/ChatRoom";
import type { RoomData } from "@/components/chat/types";
import type { SSEEvent } from "@/lib/sse";
import fixture from "../fixtures/room/session-s15.json";

// Spec: specs/features/check/ocr-confirm-card.md
const room = fixture as RoomData;
const CARD_NAME = "อ่านได้แบบนี้ ถูกไหม";
const ERROR_TEXT = "ส่งไม่สำเร็จ ลองส่งอีกทีนะ";
const OCR3 = {
  lines: [
    { latex: "x^2 - 5x + 6", confidence: 0.97 },
    { latex: "= (x - 2)(x + 3)", confidence: 0.91 },
    { latex: "= x^2 + x - 6", confidence: 0.95 },
  ],
};

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

type Item = { event: SSEEvent } | { error: Error } | { end: true };

/** A stream source the test drives event by event. Each call opens a new stream. */
function controlled<Args extends unknown[]>() {
  const calls: Args[] = [];
  let items: Item[] = [];
  let wake: (() => void) | null = null;

  const fn = vi.fn((...args: Args) => {
    calls.push(args);
    items = [];
    const own = items;
    return (async function* () {
      while (true) {
        while (own.length === 0) await new Promise<void>((r) => (wake = r));
        const item = own.shift()!;
        if ("end" in item) return;
        if ("error" in item) throw item.error;
        yield item.event;
      }
    })();
  });

  const flush = () => act(async () => void (await new Promise((r) => setTimeout(r, 0))));
  const step = async (item: Item) => {
    items.push(item);
    wake?.();
    wake = null;
    await flush();
  };

  return {
    fn,
    calls,
    token: (speaker: "tutor" | "buddy", text: string) => step({ event: { event: "token", data: { speaker, text } } }),
    event: (event: string, data: unknown = {}) => step({ event: { event, data } }),
    done: () => step({ event: { event: "done", data: {} } }),
    fail: () => step({ error: new Error("network") }),
  };
}

function setup() {
  const send = controlled<[unknown, AbortSignal]>();
  const confirm = controlled<[string[], AbortSignal]>();
  const utils = render(<ChatRoom room={room} sendMessage={send.fn} confirmOcr={confirm.fn} imagesEnabled />);
  const input = utils.getByLabelText("พิมพ์ตอบ") as HTMLTextAreaElement;
  const fileInput = utils.container.querySelector<HTMLInputElement>('input[type="file"]')!;

  const sendPhoto = async () => {
    const photo = new File(["x"], "วิธีทำ.jpg", { type: "image/jpeg" });
    fireEvent.change(fileInput, { target: { files: [photo] } });
    await act(async () => void fireEvent.click(utils.getByRole("button", { name: "ส่ง" })));
  };
  const cards = () => utils.queryAllByRole("region", { name: CARD_NAME });
  const card = () => utils.getByRole("region", { name: CARD_NAME });
  const button = (name: string, c = card()) => within(c).getByRole("button", { name }) as HTMLButtonElement;
  const click = (name: string, c = card()) => act(async () => void fireEvent.click(button(name, c)));
  const editLine = async (n: number, value: string) => {
    await click(`แก้บรรทัด ${n}`);
    fireEvent.change(within(card()).getByRole("textbox", { name: `บรรทัด ${n}` }), { target: { value } });
    await click("บันทึก");
  };
  /** Bubbles and cards after the fixture's history, in screen order. */
  const initial = utils.container.querySelectorAll("[data-role], [role=region], [role=group]").length;
  const items = () =>
    [...utils.container.querySelectorAll<HTMLElement>("[data-role], [role=region], [role=group]")]
      .slice(initial)
      .map((el) => el.getAttribute("data-role") ?? el.getAttribute("aria-label"));

  /** Sends a photo and lets the reply show the OCR3 card. */
  const showCard = async () => {
    await sendPhoto();
    await send.event("ocr_preview", OCR3);
    await send.done();
  };

  return { ...utils, send, confirm, input, fileInput, sendPhoto, cards, card, button, click, editLine, items, showCard };
}

describe("ChatRoom handwriting confirm card", () => {
  // AC-1 (in the room)
  it("AM02 an ocr_preview in the reply shows the confirm card, not a bubble", async () => {
    const t = setup();

    await t.showCard();

    expect(t.items()).toEqual(["user", CARD_NAME]);
    expect(t.card().querySelectorAll("[data-ocr-line]")).toHaveLength(3);
  });

  // AC-4
  it("AM02 an ocr_preview with no lines shows no card", async () => {
    const t = setup();

    await t.sendPhoto();
    await t.send.event("ocr_preview", { lines: [] });
    await t.send.done();

    expect(t.cards()).toHaveLength(0);
  });

  // AC-5
  it("AM02 an unreadable photo answered by a tutor token shows a bubble and no card", async () => {
    const t = setup();

    await t.sendPhoto();
    await t.send.token("tutor", "รูปนี้อ่านไม่ออกเลย ถ่ายใหม่ให้หน่อย");
    await t.send.done();

    expect(t.items()).toEqual(["user", "tutor"]);
    expect(t.cards()).toHaveLength(0);
  });

  // AC-7
  it("AM02 the card splits the tutor's message around it", async () => {
    const t = setup();

    await t.sendPhoto();
    await t.send.token("tutor", "ขอดูก่อนนะ");
    await t.send.event("ocr_preview", OCR3);
    await t.send.token("tutor", "เช็คให้หน่อย");
    await t.send.done();

    expect(t.items()).toEqual(["user", "tutor", CARD_NAME, "tutor"]);
    const tutors = [...t.container.querySelectorAll<HTMLElement>('[data-role="tutor"]')].slice(-2);
    expect(tutors[0].textContent).toContain("ขอดูก่อนนะ");
    expect(tutors[1].textContent).toContain("เช็คให้หน่อย");
  });

  // AC-13
  it("AM02 confirming without edits sends every line as read and adds no user bubble", async () => {
    const t = setup();
    await t.showCard();

    await t.click("ถูกแล้ว ตรวจเลย");

    expect(t.confirm.fn).toHaveBeenCalledTimes(1);
    expect(t.confirm.calls[0][0]).toEqual(["x^2 - 5x + 6", "= (x - 2)(x + 3)", "= x^2 + x - 6"]);
    expect(t.send.fn).toHaveBeenCalledTimes(1);
    expect(t.items()).toEqual(["user", CARD_NAME]);
  });

  // AC-14
  it("AM03 confirming after edits sends the saved lines in order", async () => {
    const t = setup();
    await t.showCard();

    await t.editLine(2, "= (x - 2)(x - 3)");
    await t.editLine(3, "= x^2 - 5x + 6");
    await t.click("ถูกแล้ว ตรวจเลย");

    expect(t.confirm.calls[0][0]).toEqual(["x^2 - 5x + 6", "= (x - 2)(x - 3)", "= x^2 - 5x + 6"]);
  });

  // AC-15
  it("AM02 the confirm reply streams after the card and the card locks with the confirmed lines", async () => {
    const t = setup();
    await t.showCard();
    await t.editLine(2, "= (x - 2)(x - 3)");

    await t.click("ถูกแล้ว ตรวจเลย");
    await t.confirm.token("tutor", "บรรทัดสองยังไม่ถูกนะ");
    await t.confirm.done();

    expect(t.items()).toEqual(["user", CARD_NAME, "tutor"]);
    const tutors = [...t.container.querySelectorAll<HTMLElement>('[data-role="tutor"]')];
    expect(tutors[tutors.length - 1].textContent).toContain("บรรทัดสองยังไม่ถูกนะ");
    const c = t.card();
    expect(within(c).queryAllByRole("button")).toHaveLength(0);
    expect(c.textContent).toContain("ยืนยันแล้ว");
    expect(c.querySelector('[data-ocr-line="2"]')?.textContent).toContain("แก้แล้ว");
  });

  // AC-16
  it("AM02 while the confirm reply streams the card buttons are disabled and confirm is sent once", async () => {
    const t = setup();
    await t.showCard();

    await t.click("ถูกแล้ว ตรวจเลย");
    for (const name of ["ถูกแล้ว ตรวจเลย", "ถ่ายใหม่", "แก้บรรทัด 1"]) {
      expect(t.button(name).disabled).toBe(true);
    }
    await t.click("ถูกแล้ว ตรวจเลย");

    expect(t.confirm.fn).toHaveBeenCalledTimes(1);
    expect((t.getByRole("button", { name: "ส่ง" }) as HTMLButtonElement).disabled).toBe(true);
  });

  // AC-17
  it.each([
    ["an error event", (c: ReturnType<typeof controlled>) => c.event("error", { code: "x", message: "boom" })],
    ["a network failure", (c: ReturnType<typeof controlled>) => c.fail()],
  ])("AM02 %s in the confirm reply keeps the card open with its edits and allows confirming again", async (_how, failWith) => {
    const t = setup();
    await t.showCard();
    await t.editLine(2, "= (x - 2)(x - 3)");

    await t.click("ถูกแล้ว ตรวจเลย");
    await failWith(t.confirm as unknown as ReturnType<typeof controlled>);

    expect(t.getByRole("alert").textContent).toBe(ERROR_TEXT);
    expect(t.button("ถูกแล้ว ตรวจเลย").disabled).toBe(false);
    expect(t.card().querySelector('[data-ocr-line="2"]')?.textContent).toContain("แก้แล้ว");

    await t.click("ถูกแล้ว ตรวจเลย");
    expect(t.confirm.fn).toHaveBeenCalledTimes(2);
    expect(t.confirm.calls[1][0]).toEqual(["x^2 - 5x + 6", "= (x - 2)(x - 3)", "= x^2 + x - 6"]);
  });

  // AC-18
  it("AM02 a verdict inside the confirm reply does not break the tutor bubble or show text", async () => {
    const t = setup();
    await t.showCard();

    await t.click("ถูกแล้ว ตรวจเลย");
    await t.confirm.token("tutor", "โอเค ");
    await t.confirm.event("verdict", { verdict: "incorrect", first_wrong_line: 2, error_type: "sign" });
    await t.confirm.token("tutor", "บรรทัดสองยังไม่ถูก");
    await t.confirm.done();

    expect(t.items()).toEqual(["user", CARD_NAME, "tutor"]);
    const tutors = [...t.container.querySelectorAll<HTMLElement>('[data-role="tutor"]')];
    expect(tutors[tutors.length - 1].textContent).toContain("โอเค บรรทัดสองยังไม่ถูก");
    expect(t.container.textContent).not.toMatch(/incorrect|sign/);
  });

  // AC-19
  it("AM02 retake locks the card, does not confirm, and opens the photo picker", async () => {
    const t = setup();
    await t.showCard();
    const pick = vi.spyOn(HTMLInputElement.prototype, "click").mockImplementation(() => {});

    await t.click("ถ่ายใหม่");

    expect(t.confirm.fn).not.toHaveBeenCalled();
    const c = t.card();
    expect(within(c).queryAllByRole("button")).toHaveLength(0);
    expect(c.textContent).toContain("ส่งรูปใหม่ได้เลย");
    expect(pick.mock.contexts).toContain(t.fileInput);
  });

  // AC-20
  it("AM02 a new preview locks the older unconfirmed card", async () => {
    const t = setup();
    await t.showCard();

    await t.sendPhoto();
    await t.send.event("ocr_preview", { lines: [{ latex: "x = 2", confidence: 0.9 }] });
    await t.send.done();

    const [first, second] = t.cards();
    expect(within(first).queryAllByRole("button")).toHaveLength(0);
    expect(first.textContent).toContain("ส่งรูปใหม่ได้เลย");
    expect(t.button("ถูกแล้ว ตรวจเลย", second).disabled).toBe(false);
    expect(t.button("ถ่ายใหม่", second).disabled).toBe(false);
  });

  // Decided OQ 7: the chat stays usable while a card waits.
  it("AM02 the user can still type and send while the card waits", async () => {
    const t = setup();
    await t.showCard();

    fireEvent.change(t.input, { target: { value: "ขอถามก่อน" } });
    await act(async () => void fireEvent.click(t.getByRole("button", { name: "ส่ง" })));

    expect(t.send.fn).toHaveBeenCalledTimes(2);
    expect(t.button("ถูกแล้ว ตรวจเลย").disabled).toBe(false);
  });
});
