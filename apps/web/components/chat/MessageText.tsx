import { Tex } from "@/components/math/Tex";

// $$...$$ is block math, $...$ is inline math (spec §2, TM-08).
const MATH = /\$\$([\s\S]+?)\$\$|\$([^$\n]+?)\$/g;

/**
 * While a message is still streaming, drop everything from a `$` that has no
 * closing pair yet, so raw LaTeX never flashes on screen
 * (chat-streaming.md §2). Once the stream ends the full text is shown.
 */
function withoutUnclosedMath(content: string): string {
  let end = 0;
  for (const match of content.matchAll(MATH)) end = match.index + match[0].length;
  const open = content.indexOf("$", end);
  return open === -1 ? content : content.slice(0, open);
}

/**
 * Message text with math rendered by KaTeX. Everything else stays plain text:
 * React escapes it, so HTML in the content is never interpreted.
 */
export function MessageText({ content: full, streaming = false }: { content: string; streaming?: boolean }) {
  const content = streaming ? withoutUnclosedMath(full) : full;
  const parts: React.ReactNode[] = [];
  let last = 0;
  for (const match of content.matchAll(MATH)) {
    if (match.index > last) parts.push(content.slice(last, match.index));
    parts.push(
      match[1] !== undefined ? (
        <Tex key={match.index} math={match[1]} display />
      ) : (
        <Tex key={match.index} math={match[2]} />
      ),
    );
    last = match.index + match[0].length;
  }
  if (last < content.length) parts.push(content.slice(last));

  return <div className="whitespace-pre-wrap break-words">{parts}</div>;
}
