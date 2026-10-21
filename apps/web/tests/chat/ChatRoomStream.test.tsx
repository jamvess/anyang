import { readFileSync } from "node:fs";
import { join } from "node:path";
import { act, cleanup, fireEvent, render, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ChatRoom, NEAR_BOTTOM_PX } from "@/components/chat/ChatRoom";
import type { ChatMessage, RoomData, SendPayload } from "@/components/chat/types";
import { createFakeTransport } from "@/lib/fakeTransport";
import type { SSEEvent } from "@/lib/sse";
import fixture from "../fixtures/room/session-s15.json";

// Spec: specs/features/tutor/chat-streaming.md
const room = fixture as RoomData;
const ERROR_TEXT = "ส่งไม่สำเร็จ ลองส่งอีกทีนะ";

const sseFixture = (name: string) =>
  readFileSync(join(__dirname, "..", "fixtures", "sse", name), "utf8");

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

type Item = { event: SSEEvent } | { error: Error } | { end: true };

/** A transport the test drives event by event. Each send opens a new stream. */
function controlledTransport() {
  const calls: { payload: SendPayload; signal: AbortSignal }[] = [];
  let items: Item[] = [];
  let wake: (() => void) | null = null;

  function put(item: Item) {
    items.push(item);
    wake?.();
    wake = null;
  }

  const sendMessage = vi.fn((payload: SendPayload, signal: AbortSignal) => {
    calls.push({ payload, signal });
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
    put(item);
    await flush();
  };

  return {
    sendMessage,
    calls,
    flush,
    token: (speaker: "tutor" | "buddy", text: string) =>
      step({ event: { event: "token", data: { speaker, text } } }),
    event: (event: string, data: unknown = {}) => step({ event: { event, data } }),
    done: () => step({ event: { event: "done", data: {} } }),
    end: () => step({ end: true }),
    fail: (message = "network") => step({ error: new Error(message) }),
  };
}

function setup(sendMessage: Parameters<typeof ChatRoom>[0]["sendMessage"], r: RoomData = room) {
  const utils = render(<ChatRoom room={r} sendMessage={sendMessage} />);
  const input = utils.getByLabelText("พิมพ์ตอบ") as HTMLTextAreaElement;
  const sendButton = () => utils.getByRole("button", { name: "ส่ง" }) as HTMLButtonElement;
  const bubbles = () => [...utils.container.querySelectorAll<HTMLElement>("[data-role]")];
  const initial = bubbles().length;
  const newBubbles = () => bubbles().slice(initial);
  const type = (text: string) => fireEvent.change(input, { target: { value: text } });
  const send = async (text: string) => {
    type(text);
    await act(async () => void fireEvent.click(sendButton()));
  };
  return { ...utils, input, sendButton, bubbles, newBubbles, type, send };
}

const roles = (els: HTMLElement[]) => els.map((el) => el.getAttribute("data-role"));

describe("ChatRoom streaming", () => {
  // AC-1
  it("TM20 sends the text through the transport and shows the user bubble before the reply", async () => {
    const t = controlledTransport();
    const { send, newBubbles } = setup(t.sendMessage);

    await send("(x-7)(x+7)");
    await t.token("tutor", "ถูก");

    expect(t.sendMessage).toHaveBeenCalledTimes(1);
    expect(t.calls[0].payload).toEqual({ text: "(x-7)(x+7)", image: null });
    expect(roles(newBubbles())).toEqual(["user", "tutor"]);
    expect(newBubbles()[0].textContent).toContain("(x-7)(x+7)");
  });

  // AC-2
  it("TM20 joins tokens of the same speaker into one bubble with the tutor name", async () => {
    const t = controlledTransport();
    const { send, newBubbles } = setup(t.sendMessage);

    await send("ตอบ");
    await t.token("tutor", "ถูก");
    await t.token("tutor", "แล้ว");
    await t.done();

    const tutor = newBubbles().filter((b) => b.getAttribute("data-role") === "tutor");
    expect(tutor).toHaveLength(1);
    expect(tutor[0].textContent).toContain("ถูกแล้ว");
    expect(within(tutor[0]).getByText(room.tutor_name)).toBeTruthy();
  });

  // AC-3
  it("TM20 shows text before the stream ends and grows the same bubble", async () => {
    const t = controlledTransport();
    const { send, newBubbles } = setup(t.sendMessage);

    await send("ตอบ");
    await t.token("tutor", "ถูก");
    expect(roles(newBubbles())).toEqual(["user", "tutor"]);
    expect(newBubbles()[1].textContent).toContain("ถูก");

    await t.token("tutor", "แล้ว");
    expect(roles(newBubbles())).toEqual(["user", "tutor"]);
    expect(newBubbles()[1].textContent).toContain("ถูกแล้ว");
  });

  // AC-4
  it("TM20 a tutor, buddy, tutor scene becomes three bubbles in order", async () => {
    const t = controlledTransport();
    const { send, newBubbles } = setup(t.sendMessage);

    await send("ตอบ");
    await t.token("tutor", "ถูกแล้ว");
    await t.token("buddy", "เดี๋ยวนะพี่");
    await t.token("tutor", "แยกไม่ได้");
    await t.done();

    expect(roles(newBubbles())).toEqual(["user", "tutor", "buddy", "tutor"]);
    expect(within(newBubbles()[2]).getByText(room.buddy_name!)).toBeTruthy();
    expect(newBubbles()[2].textContent).toContain("เดี๋ยวนะพี่");
  });

  // AC-5
  it("TM20 a new stream never appends to an older tutor message", async () => {
    const lastTutor: ChatMessage = {
      id: "old",
      role: "tutor",
      content: "ข้อความเก่า",
      input_mode: null,
      attachment_path: null,
      created_at: "2026-08-28T13:50:00Z",
    };
    const t = controlledTransport();
    const { send, bubbles } = setup(t.sendMessage, {
      ...room,
      messages: [...room.messages, lastTutor],
    });
    const tutorsBefore = bubbles().filter((b) => b.getAttribute("data-role") === "tutor").length;

    await send("ตอบ");
    await t.token("tutor", "ใหม่");
    await t.done();

    const tutors = bubbles().filter((b) => b.getAttribute("data-role") === "tutor");
    expect(tutors).toHaveLength(tutorsBefore + 1);
    expect(tutors.some((b) => b.textContent?.includes("ข้อความเก่า") && b.textContent.includes("ใหม่"))).toBe(false);
  });

  // AC-6
  it("TM20 a buddy event becomes one whole buddy bubble", async () => {
    const t = controlledTransport();
    const { send, newBubbles } = setup(t.sendMessage);

    await send("เหนื่อยจัง");
    await t.event("buddy", { text: "เหนื่อยเหมือนกันเลย" });
    await t.done();

    expect(roles(newBubbles())).toEqual(["user", "buddy"]);
    expect(newBubbles()[1].textContent).toContain("เหนื่อยเหมือนกันเลย");
  });

  // AC-7
  it("TM20 skips events this feature does not show without breaking the bubble", async () => {
    const t = controlledTransport();
    const { send, newBubbles, queryByText } = setup(t.sendMessage);

    await send("ตอบ");
    await t.token("tutor", "ถูก");
    await t.event("progress_card", { days_left: 5, passed: 1, total: 4, readiness: 0.25, topics: [] });
    await t.event("problem", { problem_id: "p1", text_latex: "x^2", difficulty: 1, purpose: "check" });
    await t.event("verdict", { verdict: "correct", first_wrong_line: null, error_type: null });
    await t.event("unknown_event", { anything: true });
    await t.token("tutor", "แล้ว");
    await t.done();

    expect(roles(newBubbles())).toEqual(["user", "tutor"]);
    expect(newBubbles()[1].textContent).toContain("ถูกแล้ว");
    expect(queryByText(ERROR_TEXT)).toBeNull();
  });

  // AC-8
  it("TM20 each send gets its own tutor bubble", async () => {
    const t = controlledTransport();
    const { send, newBubbles } = setup(t.sendMessage);

    await send("หนึ่ง");
    await t.token("tutor", "ตอบหนึ่ง");
    await t.done();
    await send("สอง");
    await t.token("tutor", "ตอบสอง");
    await t.done();

    expect(roles(newBubbles())).toEqual(["user", "tutor", "user", "tutor"]);
    expect(newBubbles()[1].textContent).not.toContain("ตอบสอง");
    expect(newBubbles()[3].textContent).toContain("ตอบสอง");
  });
});

describe("ChatRoom streaming math", () => {
  // AC-9
  it("TM08 inline math split across tokens renders as one KaTeX after the stream ends", async () => {
    const t = controlledTransport();
    const { send, newBubbles } = setup(t.sendMessage);

    await send("ตอบ");
    await t.token("tutor", "ลอง $x^2");
    await t.token("tutor", "-49$ ดู");
    await t.done();

    const bubble = newBubbles()[1];
    expect(bubble.querySelectorAll("span.tex > .katex")).toHaveLength(1);
    expect(within(bubble).getByText(/ลอง/)).toBeTruthy();
    expect(within(bubble).getByText(/ดู/)).toBeTruthy();
  });

  // AC-10
  it("TM08 hides an unclosed $ while streaming", async () => {
    const t = controlledTransport();
    const { send, newBubbles } = setup(t.sendMessage);

    await send("ตอบ");
    await t.token("tutor", "ลอง $x^2");

    const bubble = newBubbles()[1];
    expect(bubble.textContent).toContain("ลอง");
    expect(bubble.querySelectorAll(".katex")).toHaveLength(0);
    expect(bubble.textContent).not.toContain("$");
    expect(bubble.textContent).not.toContain("x^2");
  });

  // AC-11
  it("TM08 block math split across tokens is hidden until closed, then renders as block KaTeX", async () => {
    const t = controlledTransport();
    const { send, newBubbles } = setup(t.sendMessage);

    await send("ตอบ");
    await t.token("tutor", "$$a^2-b^2");
    expect(newBubbles()[1].textContent).not.toContain("$$");
    expect(newBubbles()[1].textContent).not.toContain("a^2");

    await t.token("tutor", "=(a-b)(a+b)$$");
    await t.done();
    expect(newBubbles()[1].querySelectorAll("div.tex > .katex-display")).toHaveLength(1);
  });

  // AC-11b
  it("TM08 shows an unpaired $ as text once the stream ends", async () => {
    const t = controlledTransport();
    const { send, newBubbles } = setup(t.sendMessage);

    await send("ตอบ");
    await t.token("tutor", "ราคา $5");
    await t.done();

    expect(newBubbles()[1].textContent).toContain("ราคา $5");
  });
});

describe("ChatRoom streaming state and errors", () => {
  // AC-12
  it("TM20 a draft can be typed while answering but not sent until done", async () => {
    const t = controlledTransport();
    const { send, type, input, sendButton } = setup(t.sendMessage);

    await send("ตอบ");
    await t.token("tutor", "ถูก");
    type("ข้อต่อไป");

    expect(input.value).toBe("ข้อต่อไป");
    expect(sendButton().disabled).toBe(true);
    await act(async () => void fireEvent.keyDown(input, { key: "Enter" }));
    expect(t.sendMessage).toHaveBeenCalledTimes(1);

    await t.done();
    expect(sendButton().disabled).toBe(false);
    await act(async () => void fireEvent.click(sendButton()));
    expect(t.sendMessage).toHaveBeenCalledTimes(2);
    expect(t.calls[1].payload).toEqual({ text: "ข้อต่อไป", image: null });
  });

  // AC-12b
  it("TM20 shows a typing indicator at the end until the first token", async () => {
    const t = controlledTransport();
    const { send, bubbles, getByLabelText, queryByLabelText } = setup(t.sendMessage);

    await send("ตอบ");
    const indicator = getByLabelText("กำลังพิมพ์");
    for (const b of bubbles()) {
      expect(b.compareDocumentPosition(indicator) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    }

    await t.token("tutor", "ถูก");
    expect(queryByLabelText("กำลังพิมพ์")).toBeNull();
  });

  it("TM20 the typing indicator goes away when the stream ends without a token", async () => {
    const t = controlledTransport();
    const { send, getByLabelText, queryByLabelText } = setup(t.sendMessage);

    await send("ตอบ");
    expect(getByLabelText("กำลังพิมพ์")).toBeTruthy();
    await t.done();
    expect(queryByLabelText("กำลังพิมพ์")).toBeNull();
  });

  // AC-13 (uses the fake transport with the error fixture)
  it("TM20 an error event keeps the partial bubble and shows one alert without the server message", async () => {
    const sendMessage = createFakeTransport(sseFixture("tutor_reply_error.txt"), { delayMs: 0 });
    const { send, newBubbles, findByText, queryByText, type, sendButton } = setup(sendMessage);

    await send("ตอบ");
    const alert = await findByText(ERROR_TEXT);

    expect(alert.closest('[role="alert"]')).not.toBeNull();
    expect(queryByText(/provider timeout/)).toBeNull();
    expect(roles(newBubbles())).toEqual(["user", "tutor"]);
    expect(newBubbles()[1].textContent).toContain("ถูก");
    type("อีกที");
    expect(sendButton().disabled).toBe(false);
  });

  // AC-14
  it("TM20 a transport that throws before any event shows the alert and no tutor bubble", async () => {
    const sendMessage = vi.fn(() =>
      (async function* (): AsyncGenerator<SSEEvent> {
        throw new Error("network down");
      })(),
    );
    const { send, newBubbles, findByText, type, sendButton } = setup(sendMessage);

    await send("ตอบ");
    await findByText(ERROR_TEXT);

    expect(roles(newBubbles())).toEqual(["user"]);
    type("อีกที");
    expect(sendButton().disabled).toBe(false);
  });

  // AC-15
  it("TM20 a stream that ends without done is treated as an error", async () => {
    const t = controlledTransport();
    const { send, newBubbles, getByText, type, sendButton } = setup(t.sendMessage);

    await send("ตอบ");
    await t.token("tutor", "ถูก");
    await t.end();

    expect(getByText(ERROR_TEXT).closest('[role="alert"]')).not.toBeNull();
    expect(newBubbles()[1].textContent).toContain("ถูก");
    type("อีกที");
    expect(sendButton().disabled).toBe(false);
  });

  // AC-16
  it("TM20 sending again clears the error alert", async () => {
    const t = controlledTransport();
    const { send, getByText, queryByText } = setup(t.sendMessage);

    await send("ตอบ");
    await t.fail();
    expect(getByText(ERROR_TEXT)).toBeTruthy();

    await send("อีกที");
    expect(queryByText(ERROR_TEXT)).toBeNull();
  });

  // AC-17
  it("TM20 leaving the room mid-stream aborts the request without React errors", async () => {
    const consoleError = vi.spyOn(console, "error");
    const t = controlledTransport();
    const { send, unmount } = setup(t.sendMessage);

    await send("ตอบ");
    await t.token("tutor", "ถูก");
    unmount();
    await t.token("tutor", "แล้ว");

    expect(t.calls[0].signal.aborted).toBe(true);
    expect(consoleError).not.toHaveBeenCalled();
  });

  // AC-18
  it("TM06 sends a photo with a note through the transport", async () => {
    const t = controlledTransport();
    const { container, input, sendButton, newBubbles } = setup(t.sendMessage);
    const photo = new File(["x"], "วิธีทำ.jpg", { type: "image/jpeg" });

    fireEvent.change(container.querySelector('input[type="file"]')!, { target: { files: [photo] } });
    fireEvent.change(input, { target: { value: "ไม่แน่ใจบรรทัด 3" } });
    await act(async () => void fireEvent.click(sendButton()));

    expect(t.calls[0].payload.text).toBe("ไม่แน่ใจบรรทัด 3");
    expect(t.calls[0].payload.image?.name).toBe("วิธีทำ.jpg");
    const user = newBubbles()[0];
    expect(user.getAttribute("data-role")).toBe("user");
    expect(within(user).getByText(/วิธีทำ\.jpg/)).toBeTruthy();
    expect(user.textContent).toContain("ไม่แน่ใจบรรทัด 3");
  });
});

/**
 * jsdom does not lay out, so the log's scroll box is simulated.
 * `top` is clamped like a browser does.
 */
function scrollBox(el: HTMLElement, init: { height: number; client: number; top: number }) {
  const s = { ...init };
  const clamp = (v: number) => Math.max(0, Math.min(v, s.height - s.client));
  Object.defineProperty(el, "scrollHeight", { configurable: true, get: () => s.height });
  Object.defineProperty(el, "clientHeight", { configurable: true, get: () => s.client });
  Object.defineProperty(el, "scrollTop", {
    configurable: true,
    get: () => s.top,
    set: (v: number) => (s.top = clamp(v)),
  });
  el.scrollTo = ((a: ScrollToOptions | number, b?: number) => {
    s.top = clamp(typeof a === "number" ? (b ?? 0) : (a.top ?? s.top));
  }) as typeof el.scrollTo;
  return { s, bottom: () => s.height - s.client };
}

describe("ChatRoom auto-scroll", () => {
  async function streaming() {
    const t = controlledTransport();
    const utils = setup(t.sendMessage);
    const log = utils.getByRole("log");
    const box = scrollBox(log, { height: 1000, client: 400, top: 600 });
    await utils.send("ตอบ");
    await t.token("tutor", "ถูก");
    return { t, log, box, ...utils };
  }

  function scrollUp(log: HTMLElement, box: ReturnType<typeof scrollBox>, distance: number) {
    box.s.top = box.bottom() - distance;
    fireEvent.scroll(log);
  }

  // AC-scroll-1
  it("TM20 follows new tokens when the list is at the bottom", async () => {
    const { t, log, box } = await streaming();
    scrollUp(log, box, 0);

    box.s.height += 200;
    await t.token("tutor", "แล้ว");

    expect(box.s.top).toBe(box.bottom());
  });

  // AC-scroll-2 and AC-scroll-boundary
  it.each([
    { delta: -1, follows: true },
    { delta: 0, follows: true },
    { delta: 1, follows: false },
  ])("TM20 distance NEAR_BOTTOM_PX $delta px from the bottom: follows=$follows", async ({ delta, follows }) => {
    const { t, log, box } = await streaming();
    scrollUp(log, box, NEAR_BOTTOM_PX + delta);
    const before = box.s.top;

    box.s.height += 200;
    await t.token("tutor", "แล้ว");

    expect(box.s.top).toBe(follows ? box.bottom() : before);
  });

  it("TM20 does not pull a user who scrolled far up", async () => {
    const { t, log, box } = await streaming();
    scrollUp(log, box, box.bottom());

    box.s.height += 200;
    await t.token("tutor", "แล้ว");

    expect(box.s.top).toBe(0);
  });

  // AC-scroll-3
  it("TM20 sending a message always scrolls to the bottom", async () => {
    const { t, log, box, send } = await streaming();
    await t.done();
    scrollUp(log, box, box.bottom());

    box.s.height += 100;
    await send("ข้อต่อไป");

    expect(box.s.top).toBe(box.bottom());
  });
});
