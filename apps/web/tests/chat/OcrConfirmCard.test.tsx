import { cleanup, fireEvent, render, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { OcrConfirmCard, type OcrPreviewData } from "@/components/chat/OcrConfirmCard";

// Spec: specs/features/check/ocr-confirm-card.md
const CARD_NAME = "อ่านได้แบบนี้ ถูกไหม";
const OCR3: OcrPreviewData = {
  lines: [
    { latex: "x^2 - 5x + 6", confidence: 0.97 },
    { latex: "= (x - 2)(x + 3)", confidence: 0.91 },
    { latex: "= x^2 + x - 6", confidence: 0.95 },
  ],
};

/** TeX source of every KaTeX piece, read from its MathML annotation. */
const texSources = (el: HTMLElement) =>
  [...el.querySelectorAll('.tex annotation[encoding="application/x-tex"]')].map((a) => a.textContent);

const line = (card: HTMLElement, n: number) => card.querySelector<HTMLElement>(`[data-ocr-line="${n}"]`)!;

function setup(preview: OcrPreviewData = OCR3, status: "pending" | "sending" | "confirmed" | "retaken" = "pending") {
  const onConfirm = vi.fn();
  const onRetake = vi.fn();
  const utils = render(<OcrConfirmCard preview={preview} status={status} onConfirm={onConfirm} onRetake={onRetake} />);
  const card = () => utils.getByRole("region", { name: CARD_NAME });
  const button = (name: string) => within(card()).getByRole("button", { name }) as HTMLButtonElement;
  return { ...utils, card, button, onConfirm, onRetake };
}

afterEach(cleanup);

describe("OcrConfirmCard", () => {
  // AC-1
  it("AM02 shows every line numbered in order as KaTeX with edit, confirm and retake buttons", () => {
    const { card, button } = setup();

    const c = card();
    expect(c.textContent).toContain("ขอเช็คก่อนว่าอ่านถูกมั้ย ที่เขียนมาคือ");
    expect([1, 2, 3].map((n) => texSources(line(c, n)))).toEqual([
      ["x^2 - 5x + 6"],
      ["= (x - 2)(x + 3)"],
      ["= x^2 + x - 6"],
    ]);
    expect([1, 2, 3].map((n) => line(c, n).textContent)).toEqual([
      expect.stringMatching(/^1/),
      expect.stringMatching(/^2/),
      expect.stringMatching(/^3/),
    ]);
    for (const name of ["แก้บรรทัด 1", "แก้บรรทัด 2", "แก้บรรทัด 3", "ถูกแล้ว ตรวจเลย", "ถ่ายใหม่"]) {
      expect(button(name).disabled).toBe(false);
    }
    expect(c.hasAttribute("data-role")).toBe(false);
    expect(c.querySelectorAll("[data-role]")).toHaveLength(0);
  });

  // AC-2
  it("AM02 shows the card even when every line has confidence 1", () => {
    const { card } = setup({ lines: OCR3.lines.map((l) => ({ ...l, confidence: 1 })) });

    expect(card().querySelectorAll("[data-ocr-line]")).toHaveLength(3);
  });

  // AC-3
  it.each([0, 0.5, 1])("AM02 confidence %f of line 2 is not shown or highlighted", (confidence) => {
    const { card } = setup({
      lines: [
        { latex: "a", confidence: 0.97 },
        { latex: "b", confidence },
        { latex: "c", confidence: 0.97 },
      ],
    });

    const c = card();
    const rows = [...c.querySelectorAll<HTMLElement>("[data-ocr-line]")];
    expect(new Set(rows.map((r) => r.className)).size).toBe(1);
    const text = c.cloneNode(true) as HTMLElement;
    text.querySelectorAll(".tex").forEach((el) => el.remove());
    expect(text.textContent).not.toMatch(/0\.97|0\.5|%|confidence|มั่นใจ/);
  });

  // AC-4
  it("AM02 an empty preview shows no card", () => {
    const { queryByRole } = render(
      <OcrConfirmCard preview={{ lines: [] }} status="pending" onConfirm={vi.fn()} onRetake={vi.fn()} />,
    );

    expect(queryByRole("region", { name: CARD_NAME })).toBeNull();
  });

  it("AM02 a single line preview shows one line", () => {
    const { card } = setup({ lines: [{ latex: "x = 3", confidence: 0.9 }] });

    expect(card().querySelectorAll("[data-ocr-line]")).toHaveLength(1);
    expect(texSources(line(card(), 1))).toEqual(["x = 3"]);
  });

  // AC-6
  it("TM08 broken LaTeX in a line still shows the card and the line can be edited", () => {
    const { card, button } = setup({
      lines: [
        { latex: "x^2", confidence: 0.9 },
        { latex: "\\frac{1", confidence: 0.9 },
      ],
    });

    expect(card().querySelectorAll("[data-ocr-line]")).toHaveLength(2);
    fireEvent.click(button("แก้บรรทัด 2"));
    expect(within(card()).getByRole("textbox", { name: "บรรทัด 2" })).toBeTruthy();
  });

  // AC-8
  it("AM03 editing a line opens a box with its LaTeX and a live preview", () => {
    const { card, button } = setup();

    fireEvent.click(button("แก้บรรทัด 2"));
    const box = within(card()).getByRole("textbox", { name: "บรรทัด 2" }) as HTMLInputElement;
    expect(box.value).toBe("= (x - 2)(x + 3)");
    expect(texSources(line(card(), 2))).toEqual(["= (x - 2)(x + 3)"]);

    fireEvent.change(box, { target: { value: "= (x - 2)(x - 3)" } });
    expect(texSources(line(card(), 2))).toEqual(["= (x - 2)(x - 3)"]);
  });

  // AC-9
  it.each([
    ["the save button", (box: HTMLElement, button: (n: string) => HTMLButtonElement) => fireEvent.click(button("บันทึก"))],
    ["Enter", (box: HTMLElement) => fireEvent.keyDown(box, { key: "Enter" })],
  ])("AM03 saving with %s shows the new line with an edited tag", (_how, save) => {
    const { card, button } = setup();

    fireEvent.click(button("แก้บรรทัด 2"));
    const box = within(card()).getByRole("textbox", { name: "บรรทัด 2" });
    fireEvent.change(box, { target: { value: "= (x - 2)(x - 3)" } });
    save(box, button);

    const c = card();
    expect(within(c).queryByRole("textbox")).toBeNull();
    expect(texSources(line(c, 2))).toEqual(["= (x - 2)(x - 3)"]);
    expect(line(c, 2).textContent).toContain("แก้แล้ว");
    expect(line(c, 1).textContent).not.toContain("แก้แล้ว");
    expect(line(c, 3).textContent).not.toContain("แก้แล้ว");
  });

  // AC-10
  it.each([
    ["the cancel button", (box: HTMLElement, button: (n: string) => HTMLButtonElement) => fireEvent.click(button("ยกเลิก"))],
    ["Esc", (box: HTMLElement) => fireEvent.keyDown(box, { key: "Escape" })],
  ])("AM03 cancelling with %s restores the line", (_how, cancel) => {
    const { card, button } = setup();

    fireEvent.click(button("แก้บรรทัด 2"));
    const box = within(card()).getByRole("textbox", { name: "บรรทัด 2" });
    fireEvent.change(box, { target: { value: "= (x - 2)(x - 3)" } });
    cancel(box, button);

    const c = card();
    expect(within(c).queryByRole("textbox")).toBeNull();
    expect(texSources(line(c, 2))).toEqual(["= (x - 2)(x + 3)"]);
    expect(line(c, 2).textContent).not.toContain("แก้แล้ว");
  });

  // AC-11
  it.each(["", "   "])("AM03 a blank line %j cannot be saved", (blank) => {
    const { card, button } = setup();

    fireEvent.click(button("แก้บรรทัด 2"));
    const box = within(card()).getByRole("textbox", { name: "บรรทัด 2" });
    fireEvent.change(box, { target: { value: blank } });

    expect(button("บันทึก").disabled).toBe(true);
    fireEvent.keyDown(box, { key: "Enter" });
    expect(within(card()).getByRole("textbox", { name: "บรรทัด 2" })).toBeTruthy();
  });

  // Decided OQ 2: one line at a time; opening another line saves the open one.
  it("AM03 editing another line saves the line being edited first", () => {
    const { card, button } = setup();

    fireEvent.click(button("แก้บรรทัด 2"));
    fireEvent.change(within(card()).getByRole("textbox", { name: "บรรทัด 2" }), {
      target: { value: "= (x - 2)(x - 3)" },
    });
    fireEvent.click(button("แก้บรรทัด 3"));

    const c = card();
    expect(within(c).getAllByRole("textbox")).toHaveLength(1);
    expect(within(c).getByRole("textbox", { name: "บรรทัด 3" })).toBeTruthy();
    expect(texSources(line(c, 2))).toEqual(["= (x - 2)(x - 3)"]);
    expect(line(c, 2).textContent).toContain("แก้แล้ว");
  });

  // Decided OQ 2: a blank open line is cancelled, not saved, when another line is opened.
  it("AM03 editing another line while the open line is blank cancels the open line", () => {
    const { card, button } = setup();

    fireEvent.click(button("แก้บรรทัด 2"));
    fireEvent.change(within(card()).getByRole("textbox", { name: "บรรทัด 2" }), { target: { value: " " } });
    fireEvent.click(button("แก้บรรทัด 3"));

    expect(texSources(line(card(), 2))).toEqual(["= (x - 2)(x + 3)"]);
    expect(line(card(), 2).textContent).not.toContain("แก้แล้ว");
  });

  // AC-12
  it("AM02 confirm cannot be pressed while a line is being edited", () => {
    const { button, onConfirm } = setup();

    fireEvent.click(button("แก้บรรทัด 1"));
    expect(button("ถูกแล้ว ตรวจเลย").disabled).toBe(true);
    fireEvent.click(button("ถูกแล้ว ตรวจเลย"));
    expect(onConfirm).not.toHaveBeenCalled();
  });

  it("AM02 confirm hands over every line in order, edited lines with their saved value", () => {
    const { card, button, onConfirm } = setup();

    fireEvent.click(button("แก้บรรทัด 2"));
    fireEvent.change(within(card()).getByRole("textbox", { name: "บรรทัด 2" }), {
      target: { value: "= (x - 2)(x - 3)" },
    });
    fireEvent.click(button("บันทึก"));
    fireEvent.click(button("ถูกแล้ว ตรวจเลย"));

    expect(onConfirm).toHaveBeenCalledTimes(1);
    expect(onConfirm).toHaveBeenCalledWith(["x^2 - 5x + 6", "= (x - 2)(x - 3)", "= x^2 + x - 6"]);
  });

  it("AM02 retake calls onRetake and not onConfirm", () => {
    const { button, onConfirm, onRetake } = setup();

    fireEvent.click(button("ถ่ายใหม่"));

    expect(onRetake).toHaveBeenCalledTimes(1);
    expect(onConfirm).not.toHaveBeenCalled();
  });

  it("AM02 while sending every button in the card is disabled", () => {
    const { card } = setup(OCR3, "sending");

    const buttons = within(card()).getAllByRole("button") as HTMLButtonElement[];
    expect(buttons.length).toBeGreaterThan(0);
    expect(buttons.every((b) => b.disabled)).toBe(true);
  });

  it.each([
    ["confirmed", "ยืนยันแล้ว"],
    ["retaken", "ส่งรูปใหม่ได้เลย"],
  ] as const)("AM02 a %s card has no buttons and says %s", (status, note) => {
    const { card } = setup(OCR3, status);

    expect(within(card()).queryAllByRole("button")).toHaveLength(0);
    expect(card().textContent).toContain(note);
    expect(card().querySelectorAll("[data-ocr-line]")).toHaveLength(3);
  });

  // AC-22
  it("TM06 the card has no answer choice buttons, only its own controls", () => {
    const { card, button } = setup();

    fireEvent.click(button("แก้บรรทัด 1"));
    const names = within(card())
      .getAllByRole("button")
      .map((b) => b.getAttribute("aria-label") ?? b.textContent?.trim());
    const allowed = /^(แก้บรรทัด \d+|บันทึก|ยกเลิก|ถูกแล้ว ตรวจเลย|ถ่ายใหม่)$/;
    expect(names.every((n) => allowed.test(n ?? ""))).toBe(true);
  });
});
