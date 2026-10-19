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
