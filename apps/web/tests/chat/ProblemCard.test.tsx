import { cleanup, render } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { ProblemCard, type ProblemData } from "@/components/chat/ProblemCard";

// Spec: specs/features/tutor/problem-card.md
const PROBLEM: ProblemData = { problem_id: "p1", text_latex: "x^2 - 49", difficulty: 1, purpose: "probe" };

/** TeX source of every KaTeX piece, read from its MathML annotation. */
const texSources = (el: HTMLElement) =>
  [...el.querySelectorAll('.tex annotation[encoding="application/x-tex"]')].map((a) => a.textContent);

afterEach(cleanup);

describe("ProblemCard", () => {
  it("TM08 shows the problem as a region named โจทย์ with one block KaTeX of text_latex", () => {
    const { getByRole } = render(<ProblemCard problem={PROBLEM} />);

    const card = getByRole("region", { name: "โจทย์" });
    expect(card.querySelectorAll("div.tex > .katex-display")).toHaveLength(1);
    expect(texSources(card)).toEqual(["x^2 - 49"]);
    expect(card.getAttribute("data-problem-id")).toBe("p1");
  });

  it("TM04 does not show difficulty or purpose", () => {
    const { getByRole } = render(<ProblemCard problem={{ ...PROBLEM, difficulty: 3, purpose: "practice" }} />);

    const card = getByRole("region");
    const header = card.cloneNode(true) as HTMLElement;
    header.querySelectorAll(".tex").forEach((el) => el.remove());
    expect(header.textContent).not.toMatch(/3|practice|probe|ยาก/);
  });

  it("TM06 has no buttons", () => {
    const { getByRole } = render(<ProblemCard problem={PROBLEM} />);

    expect(getByRole("region").querySelectorAll("button")).toHaveLength(0);
  });

  it("TM04 an empty text_latex shows no card", () => {
    const { queryByRole } = render(<ProblemCard problem={{ ...PROBLEM, text_latex: "" }} />);

    expect(queryByRole("region")).toBeNull();
  });

  it("TM04 broken LaTeX still shows the card instead of crashing", () => {
    const { getByRole } = render(<ProblemCard problem={{ ...PROBLEM, text_latex: "\\frac{1" }} />);

    expect(getByRole("region", { name: "โจทย์" })).toBeTruthy();
  });
});
