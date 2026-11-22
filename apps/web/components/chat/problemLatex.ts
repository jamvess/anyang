// Spec: specs/features/tutor/problem-card.md §2 "โจทย์ยาวไม่ล้นการ์ด" (May 22 Nov · #177).

const TEXT = "\\text{";
const BREAK = "\\allowbreak";

/**
 * `text_latex` with places where KaTeX may break the line: after each `\text{…}` (when something
 * follows) and at the spaces inside it. KaTeX breaks a display line only between its boxes, and a
 * generated problem such as `\text{หาค่า } \lim_{x \to 2} …` (prompts/generate_problem/v2.md item 5)
 * is one box. A `\text{}` holding braces, `$` or a command is kept whole; an unclosed one is left
 * as it is. The rendered maths is the same, only where lines may end changes.
 */
export function breakable(latex: string): string {
  let out = "";
  let at = 0;
  while (at < latex.length) {
    const start = latex.indexOf(TEXT, at);
    if (start < 0) break;
    const close = closingBrace(latex, start + TEXT.length);
    if (close < 0) break;
    const content = latex.slice(start + TEXT.length, close);
    out += latex.slice(at, start);
    out += /[{}$\\]/.test(content)
      ? `${TEXT}${content}}`
      : content
          .split(/(?= )/)
          .map((piece) => `${TEXT}${piece}}`)
          .join(BREAK);
    at = close + 1;
    if (at < latex.length) out += /[A-Za-z]/.test(latex[at]) ? `${BREAK} ` : BREAK;
  }
  return out + latex.slice(at);
}

/** Index of the `}` that closes the group whose content starts at `from`, or -1. */
function closingBrace(latex: string, from: number): number {
  let depth = 1;
  for (let i = from; i < latex.length; i++) {
    if (latex[i] === "\\") i++;
    else if (latex[i] === "{") depth++;
    else if (latex[i] === "}" && --depth === 0) return i;
  }
  return -1;
}
