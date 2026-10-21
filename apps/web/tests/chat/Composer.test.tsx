import { cleanup, fireEvent, render } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { Composer } from "@/components/chat/Composer";
import room from "../fixtures/room/session-s15.json";

// Limits come with the room data (spec §2), here from the fixture.
const limits = room.limits;
const MB = 1024 * 1024;

afterEach(cleanup);

function setup() {
  const onSend = vi.fn();
  const utils = render(<Composer limits={limits} onSend={onSend} />);
  const input = utils.getByLabelText("พิมพ์ตอบ") as HTMLTextAreaElement;
  const send = utils.getByRole("button", { name: "ส่ง" }) as HTMLButtonElement;
  const file = utils.container.querySelector('input[type="file"]') as HTMLInputElement;
  return { ...utils, onSend, input, send, file };
}

function image(name: string, size: number, type = "image/jpeg"): File {
  const f = new File(["x"], name, { type });
  Object.defineProperty(f, "size", { value: size });
  return f;
}

describe("Composer", () => {
  it("TM06 has only the attach and send buttons, no answer choice buttons", () => {
    const { getAllByRole } = setup();

    const names = getAllByRole("button").map((b) => b.getAttribute("aria-label") ?? b.textContent);
    expect(names.sort()).toEqual(["ส่ง", "แนบรูป"].sort());
  });

  it.each(["", "   ", " \n \n "])("TM06 send is disabled for empty or blank text %j", (text) => {
    const { input, send } = setup();

    fireEvent.change(input, { target: { value: text } });
    expect(send.disabled).toBe(true);
  });

  it("TM06 sends the typed text and clears the input", () => {
    const { input, send, onSend } = setup();

    fireEvent.change(input, { target: { value: "(x-7)(x+7)" } });
    fireEvent.click(send);

    expect(onSend).toHaveBeenCalledTimes(1);
    expect(onSend).toHaveBeenCalledWith({ text: "(x-7)(x+7)", image: null });
    expect(input.value).toBe("");
  });

  it("TM06 Enter sends, Shift+Enter does not", () => {
    const { input, onSend } = setup();
    fireEvent.change(input, { target: { value: "ใช่ๆ" } });

    const shiftNotPrevented = fireEvent.keyDown(input, { key: "Enter", shiftKey: true });
    expect(shiftNotPrevented).toBe(true); // browser inserts the newline
    expect(onSend).not.toHaveBeenCalled();

    const enterNotPrevented = fireEvent.keyDown(input, { key: "Enter" });
    expect(enterNotPrevented).toBe(false);
    expect(onSend).toHaveBeenCalledWith({ text: "ใช่ๆ", image: null });
  });

  it.each([
    { delta: -1, allowed: true },
    { delta: 0, allowed: true },
    { delta: 1, allowed: false },
  ])("TM21 text of max_message_chars $delta chars: allowed=$allowed", ({ delta, allowed }) => {
    const { input, send, queryByText } = setup();
    const max = limits.max_message_chars;

    fireEvent.change(input, { target: { value: "ก".repeat(max + delta) } });

    expect(send.disabled).toBe(!allowed);
    const warning = queryByText(`ข้อความยาวเกิน ${max} ตัวอักษร`);
    expect(warning === null).toBe(allowed);
  });

  it("TM06 attaching a photo shows its name and a remove button, send is enabled with empty text", () => {
    const { file, send, getByText, getByRole } = setup();

    fireEvent.change(file, { target: { files: [image("วิธีทำ.jpg", 200_000)] } });

    expect(getByText("วิธีทำ.jpg")).toBeTruthy();
    expect(getByRole("button", { name: "เอารูปออก" })).toBeTruthy();
    expect(send.disabled).toBe(false);
  });

  it("TM06 sends the photo alone and clears the attachment", () => {
    const { file, send, onSend, queryByText } = setup();
    const photo = image("วิธีทำ.jpg", 200_000);

    fireEvent.change(file, { target: { files: [photo] } });
    fireEvent.click(send);

    expect(onSend).toHaveBeenCalledWith({ text: null, image: photo });
    expect(queryByText("วิธีทำ.jpg")).toBeNull();
  });

  it("TM06 sends the photo together with a note", () => {
    const { file, input, send, onSend } = setup();
    const photo = image("วิธีทำ.jpg", 200_000);

    fireEvent.change(file, { target: { files: [photo] } });
    fireEvent.change(input, { target: { value: "ไม่แน่ใจบรรทัด 3" } });
    fireEvent.click(send);

    expect(onSend).toHaveBeenCalledWith({ text: "ไม่แน่ใจบรรทัด 3", image: photo });
  });

  it("TM06 removing the photo disables send again when the text is empty", () => {
    const { file, send, getByRole, queryByText } = setup();

    fireEvent.change(file, { target: { files: [image("วิธีทำ.jpg", 200_000)] } });
    fireEvent.click(getByRole("button", { name: "เอารูปออก" }));

    expect(queryByText("วิธีทำ.jpg")).toBeNull();
    expect(send.disabled).toBe(true);
  });

  it("TM21 does not attach a file that is not an image and says only photos are allowed", () => {
    const { file, send, queryByText, getByText } = setup();

    fireEvent.change(file, {
      target: { files: [image("ชีท.pdf", 200_000, "application/pdf")] },
    });

    expect(queryByText("ชีท.pdf")).toBeNull();
    expect(getByText("แนบได้เฉพาะรูป")).toBeTruthy();
    expect(send.disabled).toBe(true);
  });

  it.each([
    { delta: -1, allowed: true },
    { delta: 0, allowed: true },
    { delta: 1, allowed: false },
  ])("TM21 photo of max_image_mb $delta bytes: allowed=$allowed", ({ delta, allowed }) => {
    const { file, queryByText } = setup();
    const max = limits.max_image_mb;

    fireEvent.change(file, { target: { files: [image("วิธีทำ.jpg", max * MB + delta)] } });

    expect(queryByText("วิธีทำ.jpg") !== null).toBe(allowed);
    expect(queryByText(`รูปใหญ่เกิน ${max} MB`) === null).toBe(allowed);
  });

  it("TM06 input and buttons are reachable by their labels", () => {
    const { getByLabelText, getByRole } = setup();

    expect(getByLabelText("พิมพ์ตอบ").tagName).toBe("TEXTAREA");
    expect(getByRole("button", { name: "แนบรูป" })).toBeTruthy();
    expect(getByRole("button", { name: "ส่ง" })).toBeTruthy();
  });
});

// Spec: specs/features/tutor/room-http.md AC-12, AC-13
describe("Composer · imagesEnabled", () => {
  it("TM06 without imagesEnabled a photo attaches as before", () => {
    const { file, getByText, getByRole } = setup();

    fireEvent.change(file, { target: { files: [image("วิธีทำ.jpg", 1000)] } });

    expect(getByText("วิธีทำ.jpg")).toBeTruthy();
    expect(getByRole("button", { name: "เอารูปออก" })).toBeTruthy();
  });

  it("TM06 with imagesEnabled={false} a photo is not attached and the reason is shown", () => {
    const onSend = vi.fn();
    const utils = render(<Composer limits={limits} onSend={onSend} imagesEnabled={false} />);
    const file = utils.container.querySelector('input[type="file"]') as HTMLInputElement;

    fireEvent.change(file, { target: { files: [image("วิธีทำ.jpg", 1000)] } });

    expect(utils.getByText("ตอนนี้ยังส่งรูปไม่ได้ พิมพ์คำตอบมาก่อนนะ")).toBeTruthy();
    expect(utils.queryByText("วิธีทำ.jpg")).toBeNull();
    expect((utils.getByRole("button", { name: "ส่ง" }) as HTMLButtonElement).disabled).toBe(true);
    expect(utils.getByRole("button", { name: "แนบรูป" })).toBeTruthy();
  });
});
