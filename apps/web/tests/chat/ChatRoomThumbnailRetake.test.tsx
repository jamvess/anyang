import { act, cleanup, fireEvent, render, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ChatRoom } from "@/components/chat/ChatRoom";
import { THUMBNAIL_MAX_PX } from "@/components/chat/MessageList";
import type { RoomData, SendPayload } from "@/components/chat/types";
import type { SSEEvent } from "@/lib/sse";
import fixture from "../fixtures/room/session-s15.json";
import { draw, installFakeCanvas } from "../helpers/fakeCanvas";

// Spec: specs/features/tutor/answer-canvas.md §2 D (thumbnail) and §2 E (retake to the canvas)
// · AC-20 to AC-29, AC-24b. May decided these on 2026-11-12 (§10 items 3-4, D1, D2).
const room = { ...(fixture as RoomData), messages: [] };
const CANVAS = "เขียนคำตอบ";
const CANVAS_AREA = "เขียนวิธีทำตรงนี้";
const CARD = "อ่านได้แบบนี้ ถูกไหม";
const OCR: SSEEvent = { event: "ocr_preview", data: { lines: [{ latex: "x^2-49", confidence: 0.9 }] } };

function problem(id: string, latex: string): SSEEvent {
  return { event: "problem", data: { problem_id: id, text_latex: latex, difficulty: 3, purpose: "practice" } };
}

async function* stream(...events: SSEEvent[]): AsyncGenerator<SSEEvent> {
  for (const e of events) yield e;
  yield { event: "done", data: {} };
}

const flush = () => act(async () => void (await new Promise((r) => setTimeout(r, 0))));

let urls: string[];
let createObjectURL: ReturnType<typeof vi.fn>;
let revokeObjectURL: ReturnType<typeof vi.fn>;
let scrollIntoView: ReturnType<typeof vi.fn>;
let inputClicks: HTMLInputElement[];

beforeEach(() => {
  installFakeCanvas();
  urls = [];
  createObjectURL = vi.fn(() => {
    const url = `blob:test/${urls.length + 1}`;
    urls.push(url);
    return url;
  });
  revokeObjectURL = vi.fn();
  // jsdom has neither; set them for this test and take them away again in afterEach.
  Object.assign(URL, { createObjectURL, revokeObjectURL });
  // jsdom has no scrollIntoView; record which element it was called on.
  scrollIntoView = vi.fn(function (this: Element) {});
  Element.prototype.scrollIntoView = scrollIntoView as unknown as Element["scrollIntoView"];
  // Opening the file picker = clicking an <input type="file">; record which one.
  inputClicks = [];
  vi.spyOn(HTMLInputElement.prototype, "click").mockImplementation(function (this: HTMLInputElement) {
    inputClicks.push(this);
  });
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
  const u = URL as unknown as Record<string, unknown>;
  delete u.createObjectURL;
  delete u.revokeObjectURL;
  delete (Element.prototype as unknown as Record<string, unknown>).scrollIntoView;
});

function photo(name: string): File {
  return new File(["x"], name, { type: "image/jpeg" });
}

/** The Composer's file input: the one outside the canvas form. */
function composerFileInput(container: HTMLElement): HTMLInputElement {
  const all = [...container.querySelectorAll<HTMLInputElement>('input[type="file"]')];
  const canvas = container.querySelector(`[role="form"][aria-label="${CANVAS}"]`);
  return all.find((i) => !canvas?.contains(i))!;
}

function setup(replies: (() => AsyncGenerator<SSEEvent>)[], opening = stream(problem("p1", "x^2 - 49"))) {
  const sendMessage = vi.fn<(payload: SendPayload) => AsyncGenerator<SSEEvent>>(() => (replies.shift() ?? (() => stream()))());
  const utils = render(<ChatRoom room={room} opening={opening} sendMessage={sendMessage} />);

  async function sendPhoto(name: string, note?: string) {
    fireEvent.change(composerFileInput(utils.container), { target: { files: [photo(name)] } });
    if (note) fireEvent.change(utils.getByLabelText("พิมพ์ตอบ"), { target: { value: note } });
    fireEvent.click(utils.getByRole("button", { name: "ส่ง" }));
    await flush();
    await flush();
  }

  async function sendCanvas() {
    draw(utils.getByLabelText(CANVAS_AREA));
    fireEvent.click(utils.getByRole("button", { name: "ส่งคำตอบ" }));
    await flush();
    await flush();
  }

  const lastUserBubble = () => [...utils.container.querySelectorAll<HTMLElement>('[data-role="user"]')].pop()!;
  const lastCard = () => utils.getAllByRole("region", { name: CARD }).pop()!;
  const retake = async () => {
    inputClicks = [];
    scrollIntoView.mockClear();
    fireEvent.click(within(lastCard()).getByRole("button", { name: "ถ่ายใหม่" }));
    await flush();
  };
  const canvasForm = () => utils.container.querySelector<HTMLElement>(`[role="form"][aria-label="${CANVAS}"]`);

  return { ...utils, sendMessage, sendPhoto, sendCanvas, lastUserBubble, lastCard, retake, canvasForm };
}

describe("ChatRoom · thumbnail in the sent bubble (§2 D)", () => {
  it("AC-20 TM06 NFR-A1 a photo from 📷 shows a thumbnail with alt text, not the file name box", async () => {
    const t = setup([() => stream()]);
    await flush();
    await t.sendPhoto("วิธีทำ.jpg");

    const bubble = t.lastUserBubble();
    const img = within(bubble).getByRole("img", { name: "รูปที่ส่ง: วิธีทำ.jpg" }) as HTMLImageElement;
    expect(img.getAttribute("src")).toBe(urls[urls.length - 1]);
    expect(bubble.textContent).not.toContain("📷 วิธีทำ.jpg");
  });

  it("AC-21 TM06 a drawing sent from the canvas shows a thumbnail named คำตอบ.png", async () => {
    const t = setup([() => stream()]);
    await flush();
    await t.sendCanvas();

    expect(within(t.lastUserBubble()).getByRole("img", { name: "รูปที่ส่ง: คำตอบ.png" })).toBeTruthy();
  });

  it("AC-22 TM06 a photo with a note shows the thumbnail and then the note in the same bubble", async () => {
    const t = setup([() => stream()]);
    await flush();
    await t.sendPhoto("วิธีทำ.jpg", "ไม่แน่ใจบรรทัด 3");

    const bubble = t.lastUserBubble();
    const img = within(bubble).getByRole("img", { name: "รูปที่ส่ง: วิธีทำ.jpg" });
    const note = within(bubble).getByText("ไม่แน่ใจบรรทัด 3");
    expect(img.compareDocumentPosition(note) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  it("AC-23 TM06 an image message loaded from the API keeps the 📷 file name, no thumbnail", async () => {
    const fromApi: RoomData = {
      ...room,
      messages: [
        {
          id: "m1",
          role: "user",
          content: null,
          input_mode: "image",
          attachment_path: "t/sessions/s/0f1e.jpg",
          attachment_name: "วิธีทำ.jpg",
          created_at: "2026-08-28T13:47:00Z",
        } as RoomData["messages"][number],
      ],
    };
    const { container } = render(<ChatRoom room={fromApi} opening={stream()} />);
    await flush();

    const bubble = container.querySelector<HTMLElement>('[data-role="user"]')!;
    expect(bubble.textContent).toContain("📷 วิธีทำ.jpg");
    expect(within(bubble).queryByRole("img")).toBeNull();
    expect(createObjectURL).not.toHaveBeenCalled();
  });

  it("AC-24 TM06 the thumbnail's longer side is limited to THUMBNAIL_MAX_PX", async () => {
    const t = setup([() => stream()]);
    await flush();
    await t.sendPhoto("วิธีทำ.jpg");

    const img = within(t.lastUserBubble()).getByRole("img", { name: "รูปที่ส่ง: วิธีทำ.jpg" }) as HTMLImageElement;
    expect(img.style.maxWidth).toBe(`${THUMBNAIL_MAX_PX}px`);
    expect(img.style.maxHeight).toBe(`${THUMBNAIL_MAX_PX}px`);
    expect(img.style.objectFit).toBe("contain");
  });

  it("AC-24b NFR-A1 the thumbnail opens a full view; ปิด and Esc close it and focus returns", async () => {
    const t = setup([() => stream()]);
    await flush();
    await t.sendPhoto("วิธีทำ.jpg");

    // A link, not a button (May 12 Nov): the room keeps only its input buttons (RoomPagePhoto AC-19).
    const open = within(t.lastUserBubble()).getByRole("link", { name: "ดูรูปเต็ม: วิธีทำ.jpg" });
    fireEvent.click(open);
    const dialog = t.getByRole("dialog");
    expect(dialog.getAttribute("aria-modal")).toBe("true");
    expect((within(dialog).getByRole("img") as HTMLImageElement).getAttribute("src")).toBe(urls[urls.length - 1]);

    fireEvent.click(within(dialog).getByRole("button", { name: "ปิด" }));
    expect(t.queryByRole("dialog")).toBeNull();
    expect(document.activeElement).toBe(open);

    fireEvent.click(open);
    fireEvent.keyDown(t.getByRole("dialog"), { key: "Escape" });
    expect(t.queryByRole("dialog")).toBeNull();
  });

  it("AC-25 TM06 leaving the room revokes every object URL it made", async () => {
    const t = setup([() => stream(), () => stream()]);
    await flush();
    await t.sendPhoto("หนึ่ง.jpg");
    await t.sendCanvas();
    const made = [...urls];
    expect(made.length).toBeGreaterThanOrEqual(2);
    expect(revokeObjectURL).not.toHaveBeenCalled();

    t.unmount();

    for (const url of made) expect(revokeObjectURL).toHaveBeenCalledWith(url);
  });
});

describe("ChatRoom · retake goes to the canvas for canvas answers (§2 E)", () => {
  it("AC-26 AM02 retake on a card from the canvas scrolls to the canvas, focuses it, opens no file picker", async () => {
    const t = setup([() => stream(OCR)]);
    await flush();
    await t.sendCanvas();

    await t.retake();

    expect(scrollIntoView.mock.instances).toContain(t.canvasForm());
    expect(document.activeElement).toBe(t.getByLabelText(CANVAS_AREA));
    expect(inputClicks).toHaveLength(0);
    expect(within(t.lastCard()).getByText("ส่งรูปใหม่ได้เลย")).toBeTruthy(); // retaken
  });

  it("AC-27 AM02 retake on a card from 📷 opens the Composer's file picker, no scroll to the canvas", async () => {
    const t = setup([() => stream(OCR)]);
    await flush();
    await t.sendPhoto("วิธีทำ.jpg");

    await t.retake();

    expect(inputClicks).toEqual([composerFileInput(t.container)]);
    expect(scrollIntoView.mock.instances).not.toContain(t.canvasForm());
  });

  it("AC-28 AM02 the source follows the latest image: canvas then 📷 → the new card's retake opens the file picker", async () => {
    const t = setup([() => stream(OCR), () => stream(OCR)]);
    await flush();
    await t.sendCanvas();
    await t.sendPhoto("วิธีทำ.jpg");

    await t.retake();

    expect(inputClicks).toEqual([composerFileInput(t.container)]);
    expect(scrollIntoView.mock.instances).not.toContain(t.canvasForm());
  });

  it("AC-29 AM02 a card from the canvas when no problem is open (no canvas) falls back to the file picker", async () => {
    // Defensive case (§2 E item 29): no flow in the room closes a problem yet, so the canvas is
    // taken out of the page directly to stand for "no canvas any more".
    const t = setup([() => stream(OCR)]);
    await flush();
    await t.sendCanvas();
    t.canvasForm()?.remove();

    await t.retake();

    expect(inputClicks).toEqual([composerFileInput(t.container)]);
  });
});
