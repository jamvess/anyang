import { cleanup, render } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { ProblemCard, type ProblemData } from "@/components/chat/ProblemCard";
import { breakable } from "@/components/chat/problemLatex";

// Spec: specs/features/tutor/problem-card.md §2 "โจทย์ยาวไม่ล้นการ์ด" (May 22 Nov · #177).
// KaTeX breaks a display line only between its boxes (after a top-level =, +, − or \allowbreak).
// The generator's problems (`\text{หาค่า } \lim …`, prompts/generate_problem/v2.md item 5) have none,
// so the card adds \allowbreak after each \text{} and at the spaces inside it.

const problem = (text_latex: string): ProblemData => ({ problem_id: "p1", text_latex, difficulty: 1, purpose: "probe" });
const boxes = (el: HTMLElement) => el.querySelectorAll(".katex-display .katex-base").length;

afterEach(cleanup);

describe("ProblemCard wrapping", () => {
  it("TM08 a generated problem with Thai words and a limit can break into lines", () => {
    const { getByRole } = render(<ProblemCard problem={problem(String.raw`\text{หาค่า } \lim_{x \to 2} \frac{x^{2}-4}{x-2}`)} />);

    const card = getByRole("region", { name: "โจทย์" });
    expect(card.classList.contains("problem-card")).toBe(true); // the hook of the CSS in globals.css
    expect(card.querySelectorAll("div.tex > .katex-display")).toHaveLength(1);
    expect(boxes(card)).toBeGreaterThan(1);
  });

  it.each([
    [String.raw`\text{หาค่า } \lim_{x \to 2} f(x)`, String.raw`\text{หาค่า}\allowbreak\text{ }\allowbreak \lim_{x \to 2} f(x)`],
    [String.raw`\text{จงหาค่า ลิมิต}x`, String.raw`\text{จงหาค่า}\allowbreak\text{ ลิมิต}\allowbreak x`],
    [String.raw`\text{ถ้า }x=2\text{ แล้ว}`, String.raw`\text{ถ้า}\allowbreak\text{ }\allowbreak x=2\text{ แล้ว}`],
  ])("TM08 breakable(%s) adds \\allowbreak after and inside \\text{}", (input, expected) => {
    expect(breakable(input)).toBe(expected);
  });

  it.each([
    ["no text", "x^2 - 49"],
    ["braces inside the text", String.raw`\text{ค่า {a} คือ}x`],
    ["math inside the text", String.raw`\text{ค่า $x$ คือ}`],
    ["an unclosed text", String.raw`\text{ค่า x`],
    ["a longer command", String.raw`\textbf{ค่า} x`],
  ])("TM08 breakable leaves %s as it is, apart from a break after a whole \\text{}", (_what, input) => {
    const out = breakable(input);
    expect(out.replace(/\\allowbreak ?/g, "")).toBe(input);
  });
});
