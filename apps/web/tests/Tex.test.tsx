import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Tex } from "@/components/math/Tex";

describe("Tex", () => {
  it("TM08 renders inline and block LaTeX with KaTeX", () => {
    const { container } = render(
      <p>
        <Tex math="x^2" />
        <Tex math="\frac{a}{b}" display />
      </p>,
    );

    const inline = container.querySelector("span.tex > .katex");
    const block = container.querySelector("div.tex > .katex-display");
    expect(inline).not.toBeNull();
    expect(block).not.toBeNull();
    expect(block!.querySelector(".mfrac")).not.toBeNull();
    // MathML copy for screen readers
    expect(container.querySelectorAll("math")).toHaveLength(2);
  });
});
