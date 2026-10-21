import { Tex } from "@/components/math/Tex";

// $$...$$ is block math, $...$ is inline math (spec §2, TM-08). A `$` behind an
// odd run of backslashes is a dollar sign, not a delimiter (api.md v1.3
// Conventions · math-escape.md §2).

type Part = { text: string } | { math: string; display: boolean };

/** True when the `$` at `i` is escaped: an odd number of backslashes right before it. */
function escaped(s: string, i: number): boolean {
  let n = 0;
  while (i - n - 1 >= 0 && s[i - n - 1] === "\\") n++;
  return n % 2 === 1;
}

const isDelimiter = (s: string, i: number) => s[i] === "$" && !escaped(s, i);

/** Index of the `$$` closing block math opened at `start`, or -1. Needs at least one char inside. */
function closeBlock(s: string, start: number): number {
  for (let j = start + 3; j < s.length - 1; j++) {
    if (s[j] === "$" && s[j + 1] === "$" && !escaped(s, j)) return j;
  }
  return -1;
}

/** Index of the `$` closing inline math opened at `start`, or -1. Stays on one line, at least one char inside. */
function closeInline(s: string, start: number): number {
  for (let j = start + 1; j < s.length; j++) {
    if (s[j] === "\n") return -1;
    if (s[j] === "$" && !escaped(s, j)) return j > start + 1 ? j : -1;
  }
  return -1;
}

/**
 * Splits content into text and math. While streaming, everything from a `$`
 * that has no closing pair yet is dropped, and so is a trailing backslash that
 * may be the first half of `\$`, so raw LaTeX never flashes on screen
 * (chat-streaming.md §2). Once the stream ends the full text is shown.
 */
function parse(content: string, streaming: boolean): Part[] {
  const parts: Part[] = [];
  let text = "";
  const flush = () => {
    if (text) parts.push({ text });
    text = "";
  };

  let i = 0;
  while (i < content.length) {
    const c = content[i];
    if (c === "$" && escaped(content, i)) {
      // `\$` → "$": drop the backslash that escapes it.
      text = text.slice(0, -1) + "$";
      i++;
      continue;
    }
    if (isDelimiter(content, i)) {
      if (content[i + 1] === "$") {
        const end = closeBlock(content, i);
        if (end !== -1) {
          flush();
          parts.push({ math: content.slice(i + 2, end), display: true });
          i = end + 2;
          continue;
        }
      } else {
        const end = closeInline(content, i);
        if (end !== -1) {
          flush();
          parts.push({ math: content.slice(i + 1, end), display: false });
          i = end + 1;
          continue;
        }
      }
      if (streaming && !hasLaterMath(content, i + 1)) break;
    }
    text += c;
    i++;
  }

  if (streaming && i === content.length && escaped(content + "$", content.length)) {
    text = text.slice(0, -1);
  }
  flush();
  return parts;
}

/** Whether a complete math piece starts after `from` (then an earlier lone `$` is just a character). */
function hasLaterMath(s: string, from: number): boolean {
  for (let j = from; j < s.length; j++) {
    if (!isDelimiter(s, j)) continue;
    if (s[j + 1] === "$" ? closeBlock(s, j) !== -1 : closeInline(s, j) !== -1) return true;
  }
  return false;
}

/**
 * Message text with math rendered by KaTeX. Everything else stays plain text:
 * React escapes it, so HTML in the content is never interpreted.
 */
export function MessageText({ content, streaming = false }: { content: string; streaming?: boolean }) {
  return (
    <div className="whitespace-pre-wrap break-words">
      {parse(content, streaming).map((part, k) =>
        "text" in part ? part.text : <Tex key={k} math={part.math} display={part.display} />,
      )}
    </div>
  );
}
