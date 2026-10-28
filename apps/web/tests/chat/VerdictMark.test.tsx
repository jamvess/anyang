import { cleanup, render } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { VerdictMark, type VerdictData } from "@/components/chat/VerdictMark";

// Spec: specs/features/check/verdict-mark.md
const NAME = "ผลตรวจ";
const ERROR_TYPES = ["calculation", "sign", "wrong_method", "concept", "prerequisite", "no_answer"];
// English names and the Thai words a label might use; none may appear in the mark (AC-2).
const ERROR_WORDS = /calculation|sign|wrong_method|wrong method|concept|prerequisite|คำนวณ|เครื่องหมาย|วิธี|แนวคิด|พื้นฐาน/;

const mark = (verdict: unknown) => render(<VerdictMark verdict={verdict as VerdictData} />);

afterEach(cleanup);

describe("VerdictMark", () => {
  // AC-1
  it.each([
    ["correct", null, null, "✓ ถูก"],
    ["correct_with_flaw", 3, "sign", "✗ คำตอบสุดท้ายถูก แต่มีบรรทัดที่ผิด · บรรทัด 3"],
    ["incomplete", null, "concept", "✗ ค่าถูก แต่ยังไม่อยู่ในรูปที่โจทย์ถาม"],
    ["incorrect", 2, "sign", "✗ ยังไม่ถูก · บรรทัด 2"],
    ["incorrect", 1, "calculation", "✗ ยังไม่ถูก · บรรทัด 1"],
    ["incorrect", null, "concept", "✗ ยังไม่ถูก"],
  ])("AM05 %s line %s (%s) reads %j", (verdict, first_wrong_line, error_type, text) => {
    const { getByRole } = mark({ verdict, first_wrong_line, error_type });

    const el = getByRole("status", { name: NAME });
    expect(el.getAttribute("data-verdict")).toBe(verdict);
    expect(el.textContent?.replace(/\s+/g, " ").trim()).toBe(text);
  });

  it("AM05 a missing first_wrong_line adds no line number", () => {
    const { getByRole } = mark({ verdict: "incorrect", error_type: "sign" });

    expect(getByRole("status", { name: NAME }).textContent).not.toMatch(/บรรทัด/);
  });

  // AC-2
  it.each(ERROR_TYPES.filter((e) => e !== "no_answer"))("AM06 error type %s is not shown", (error_type) => {
    const { getByRole } = mark({ verdict: "incorrect", first_wrong_line: 2, error_type });

    expect(getByRole("status", { name: NAME }).textContent).not.toMatch(ERROR_WORDS);
  });

  // AC-3
  it("AM06 no_answer shows no mark", () => {
    const { queryByRole } = mark({ verdict: "incorrect", first_wrong_line: null, error_type: "no_answer" });

    expect(queryByRole("status", { name: NAME })).toBeNull();
  });

  // AC-4
  it.each([[{ verdict: "maybe", first_wrong_line: null, error_type: null }], [{}]])(
    "TM20 an unknown or malformed verdict %j shows no mark",
    (payload) => {
      const { queryByRole } = mark(payload);

      expect(queryByRole("status", { name: NAME })).toBeNull();
    },
  );

  // AC-5
  it.each(["correct", "correct_with_flaw", "incomplete", "incorrect"])("TM06 a %s mark has no buttons and no data-role", (verdict) => {
    const { getByRole } = mark({ verdict, first_wrong_line: 2, error_type: "sign" });

    const el = getByRole("status", { name: NAME });
    expect(el.querySelectorAll("button")).toHaveLength(0);
    expect(el.hasAttribute("data-role")).toBe(false);
  });
});
