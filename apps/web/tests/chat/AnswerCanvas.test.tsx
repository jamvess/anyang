import { act, cleanup, fireEvent, render } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { AnswerCanvas } from "@/components/chat/AnswerCanvas";
import type { Background } from "@/components/chat/canvasStrokes";
import room from "../fixtures/room/session-s15.json";
import { draw, installFakeCanvas } from "../helpers/fakeCanvas";

// Spec: specs/features/tutor/answer-canvas.md §2 items 8-13 · AC-9 to AC-14.
// jsdom cannot draw: tests/helpers/fakeCanvas.ts stands in for getContext, toBlob and PointerEvent.

const MB = 1024 * 1024;
const maxImageMb = room.limits.max_image_mb;
let exported = { size: 1000 };

beforeEach(() => {
  exported = installFakeCanvas();
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

function setup({ disabled = false, loadImage }: { disabled?: boolean; loadImage?: (f: File) => Promise<Background> } = {}) {
  const onSend = vi.fn();
  const utils = render(
    <AnswerCanvas onSend={onSend} disabled={disabled} maxImageMb={maxImageMb} loadImage={loadImage} />,
  );
  const canvas = utils.getByLabelText("เขียนวิธีทำตรงนี้") as HTMLCanvasElement;
  const button = (name: string) => utils.getByRole("button", { name }) as HTMLButtonElement;
  const file = utils.container.querySelector('input[type="file"]') as HTMLInputElement;
  return { ...utils, onSend, canvas, button, file };
}

const flush = () => act(async () => void (await new Promise((r) => setTimeout(r, 0))));

describe("AnswerCanvas", () => {
  it("AC-9 TM06 a drawing is sent as คำตอบ.png through the room's send", async () => {
    const { canvas, button, onSend } = setup();
    expect(button("ส่งคำตอบ").disabled).toBe(true);

    draw(canvas);
    expect(button("ส่งคำตอบ").disabled).toBe(false);
    fireEvent.click(button("ส่งคำตอบ"));
    await flush();

    expect(onSend).toHaveBeenCalledTimes(1);
    const payload = onSend.mock.calls[0][0];
    expect(payload.text).toBeNull();
    expect(payload.image).toBeInstanceOf(File);
    expect(payload.image.name).toBe("คำตอบ.png");
    expect(payload.image.type).toBe("image/png");
  });

  it("AC-10 send, undo and clear are off when there is nothing, and send is off while the room is busy", () => {
    const empty = setup();
    expect(empty.button("ส่งคำตอบ").disabled).toBe(true);
    expect(empty.button("ย้อนกลับ").disabled).toBe(true);
    expect(empty.button("ล้าง").disabled).toBe(true);
    draw(empty.canvas);
    expect(empty.button("ย้อนกลับ").disabled).toBe(false);
    expect(empty.button("ล้าง").disabled).toBe(false);
    fireEvent.click(empty.button("ล้าง"));
    expect(empty.button("ส่งคำตอบ").disabled).toBe(true);
    cleanup();

    const busy = setup({ disabled: true });
    draw(busy.canvas);
    expect(busy.button("ส่งคำตอบ").disabled).toBe(true);
  });

  it.each([
    ["one byte over the limit", 1, false],
    ["exactly the limit", 0, true],
  ])("AC-11 TM21 an exported image %s", async (_name, extra, sent) => {
    exported.size = maxImageMb * MB + extra;
    const { canvas, button, onSend, queryByText } = setup();
    draw(canvas);

    fireEvent.click(button("ส่งคำตอบ"));
    await flush();

    expect(onSend).toHaveBeenCalledTimes(sent ? 1 : 0);
    expect(queryByText(`รูปใหญ่เกิน ${maxImageMb} MB`) !== null).toBe(!sent);
  });

  it("AC-12 an image becomes the background; a file that is not an image changes nothing", async () => {
    const background: Background = { image: {} as CanvasImageSource, width: 400, height: 200 };
    const loadImage = vi.fn(async () => background);
    const { file, button, queryByText } = setup({ loadImage });

    fireEvent.change(file, { target: { files: [new File(["x"], "notes.pdf", { type: "application/pdf" })] } });
    await flush();
    expect(queryByText("ใส่ได้เฉพาะรูป")).not.toBeNull();
    expect(loadImage).not.toHaveBeenCalled();
    expect(button("ส่งคำตอบ").disabled).toBe(true);

    fireEvent.change(file, { target: { files: [new File(["x"], "sheet.png", { type: "image/png" })] } });
    await flush();
    expect(loadImage).toHaveBeenCalledTimes(1);
    expect(queryByText("ใส่ได้เฉพาะรูป")).toBeNull();
    expect(button("ส่งคำตอบ").disabled).toBe(false);
  });

  it("AC-12 an image that cannot be opened changes nothing", async () => {
    const loadImage = vi.fn(async () => {
      throw new Error("broken");
    });
    const { file, button, queryByText } = setup({ loadImage });

    fireEvent.change(file, { target: { files: [new File(["x"], "broken.png", { type: "image/png" })] } });
    await flush();

    expect(queryByText("ใส่ได้เฉพาะรูป")).not.toBeNull();
    expect(button("ส่งคำตอบ").disabled).toBe(true);
  });

  it("AC-13 after sending, the drawing stays with a note; drawing again removes the note", async () => {
    const { canvas, button, queryByText } = setup();
    draw(canvas);
    fireEvent.click(button("ส่งคำตอบ"));
    await flush();

    expect(queryByText("ส่งแล้ว · แก้แล้วส่งใหม่ได้")).not.toBeNull();
    expect(button("ส่งคำตอบ").disabled).toBe(false); // still there to send again
    draw(canvas);
    expect(queryByText("ส่งแล้ว · แก้แล้วส่งใหม่ได้")).toBeNull();
  });

  it("AC-14 every control has a label; pen and eraser say which one is on", () => {
    const { button, canvas } = setup();

    for (const name of ["ปากกา", "ยางลบ", "ย้อนกลับ", "ล้าง", "ใส่รูป", "ส่งคำตอบ"]) {
      expect(button(name)).toBeTruthy();
    }
    expect(canvas.getAttribute("aria-label")).toBe("เขียนวิธีทำตรงนี้");
    expect(button("ปากกา").getAttribute("aria-pressed")).toBe("true");
    expect(button("ยางลบ").getAttribute("aria-pressed")).toBe("false");
    fireEvent.click(button("ยางลบ"));
    expect(button("ปากกา").getAttribute("aria-pressed")).toBe("false");
    expect(button("ยางลบ").getAttribute("aria-pressed")).toBe("true");
  });

  it("AC-5 a touch after the pen has drawn does not draw (palm on the screen)", () => {
    const { canvas, button } = setup();
    draw(canvas, "pen");
    fireEvent.click(button("ย้อนกลับ")); // nothing left, but the pen was seen
    expect(button("ส่งคำตอบ").disabled).toBe(true);

    draw(canvas, "touch");

    expect(button("ส่งคำตอบ").disabled).toBe(true);
  });
});

describe("AnswerCanvas · added after /code-review (9 Nov)", () => {
  it("TM06 a double click sends once", async () => {
    const { canvas, button, onSend } = setup();
    draw(canvas);

    fireEvent.click(button("ส่งคำตอบ"));
    fireEvent.click(button("ส่งคำตอบ"));
    await flush();

    expect(onSend).toHaveBeenCalledTimes(1);
  });

  it("TM06 another pointer lifting does not end the pen's stroke", () => {
    const { canvas, button } = setup();
    const pen = (x: number) => ({ pointerType: "pen", isPrimary: true, pointerId: 7, pressure: 0.5, clientX: x, clientY: 10 });
    fireEvent.pointerDown(canvas, pen(10));
    // A palm (another pointer) lifts mid-stroke: the stroke must go on, so nothing is committed yet.
    fireEvent.pointerUp(canvas, { pointerType: "touch", isPrimary: true, pointerId: 9, clientX: 50, clientY: 50 });
    expect(button("ย้อนกลับ").disabled).toBe(true);

    fireEvent.pointerMove(canvas, pen(40));
    fireEvent.pointerUp(canvas, pen(40));

    expect(button("ย้อนกลับ").disabled).toBe(false);
  });

  it("TM06 undo removes the sent note", async () => {
    const { canvas, button, queryByText } = setup();
    draw(canvas);
    fireEvent.click(button("ส่งคำตอบ"));
    await flush();

    fireEvent.click(button("ย้อนกลับ"));

    expect(queryByText("ส่งแล้ว · แก้แล้วส่งใหม่ได้")).toBeNull();
  });
});
