import { cleanup, render } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { MessageText } from "@/components/chat/MessageText";

afterEach(cleanup);

describe("MessageText", () => {
  it("TM08 renders $...$ as inline KaTeX and the rest as plain text", () => {
    const { container, getByText } = render(<MessageText content="ลองข้อนี้ $x^2-49$" />);

    expect(container.querySelectorAll("span.tex > .katex")).toHaveLength(1);
    expect(container.querySelectorAll(".katex-display")).toHaveLength(0);
    expect(getByText(/ลองข้อนี้/)).toBeTruthy();
  });

  it("TM08 renders $$...$$ as block KaTeX", () => {
    const { container } = render(
      <MessageText content="วิธีนี้ใช้ได้ $$a^2-b^2=(a-b)(a+b)$$ ขาดข้อใดก็ใช้ไม่ได้" />,
    );

    expect(container.querySelectorAll("div.tex > .katex-display")).toHaveLength(1);
    expect(container.textContent).toContain("ขาดข้อใดก็ใช้ไม่ได้");
  });

  it("TM08 renders no KaTeX when the content has no $", () => {
    const { container } = render(<MessageText content="ถูก งั้นไม่ต้องปูพื้นแล้ว" />);

    expect(container.querySelectorAll(".katex")).toHaveLength(0);
    expect(container.textContent).toBe("ถูก งั้นไม่ต้องปูพื้นแล้ว");
  });

  it("TM08 shows HTML in content as text, not as elements", () => {
    const { container } = render(<MessageText content="<b>x</b>" />);

    expect(container.querySelector("b")).toBeNull();
    expect(container.textContent).toBe("<b>x</b>");
  });
});

// Spec: specs/features/tutor/math-escape.md (api.md v1.3 Conventions: \$ is a dollar sign)
describe("MessageText · escaped dollar", () => {
  /** TeX source of every KaTeX piece, read from its MathML annotation. */
  const texSources = (container: HTMLElement) =>
    [...container.querySelectorAll('.tex annotation[encoding="application/x-tex"]')].map((a) => a.textContent);
  /** Text outside the KaTeX pieces. */
  const plainText = (container: HTMLElement) => {
    const copy = container.cloneNode(true) as HTMLElement;
    copy.querySelectorAll(".tex").forEach((el) => el.remove());
    return copy.textContent;
  };

  it("TM08 \\$ outside math shows a dollar sign and opens no math", () => {
    const { container } = render(<MessageText content={String.raw`ราคา \$5 และ \$10`} />);

    expect(container.querySelectorAll(".katex")).toHaveLength(0);
    expect(container.textContent).toBe("ราคา $5 และ $10");
  });

  it("TM08 \\$ next to real inline math: the math still renders and the text shows $", () => {
    const { container } = render(<MessageText content={String.raw`จ่าย \$5 แล้วหา $x^2$`} />);

    expect(texSources(container)).toEqual(["x^2"]);
    expect(plainText(container)).toBe("จ่าย $5 แล้วหา ");
  });

  it("TM08 \\$ inside inline math does not close it and goes to KaTeX as is", () => {
    const { container } = render(<MessageText content={String.raw`$\$5 + x$`} />);

    expect(texSources(container)).toEqual([String.raw`\$5 + x`]);
    expect(plainText(container)).not.toContain("\\");
  });

  it("TM08 \\$ inside block math does not close it", () => {
    const { container } = render(<MessageText content={String.raw`$$\$a$$`} />);

    expect(container.querySelectorAll("div.tex > .katex-display")).toHaveLength(1);
    expect(texSources(container)).toEqual([String.raw`\$a`]);
  });

  it("TM08 while streaming, \\$ is not an unclosed $ and stays visible", () => {
    const { container } = render(<MessageText content={String.raw`ราคา \$5`} streaming />);

    expect(container.textContent).toBe("ราคา $5");
  });

  it("TM08 while streaming, a trailing backslash waits for the next token; once done it shows", () => {
    const streaming = render(<MessageText content={"ราคา \\"} streaming />);
    expect(streaming.container.textContent).toBe("ราคา ");
    expect(streaming.container.textContent).not.toContain("\\");
    cleanup();

    const done = render(<MessageText content={"ราคา \\"} />);
    expect(done.container.textContent).toBe("ราคา \\");
  });

  it("TM08 while streaming, a real unclosed $ after \\$ is still hidden", () => {
    const { container } = render(<MessageText content={String.raw`\$5 แล้ว $x`} streaming />);

    expect(container.textContent).toBe("$5 แล้ว ");
    expect(container.textContent).not.toContain("x");
  });

  it("TM08 other backslashes outside math are left as they are", () => {
    const { container } = render(<MessageText content={String.raw`เขียนว่า \frac ได้`} />);

    expect(container.textContent).toBe(String.raw`เขียนว่า \frac ได้`);
  });

  it("TM08 an even run of backslashes before $ leaves a real $ that closes the math", () => {
    // content is: $a \\$ (two backslashes)
    const { container } = render(<MessageText content={"$a \\\\$"} />);

    expect(texSources(container)).toEqual(["a \\\\"]);
  });

  it("TM08 an odd run of backslashes before $ escapes it", () => {
    // content is: ราคา \\\$5 (three backslashes)
    const { container } = render(<MessageText content={"ราคา \\\\\\$5"} />);

    expect(container.querySelectorAll(".katex")).toHaveLength(0);
    expect(container.textContent).toContain("$5");
  });
});
