import { Tex } from "@/components/math/Tex";

// $$...$$ is block math, $...$ is inline math (spec §2, TM-08).
const MATH = /\$\$([\s\S]+?)\$\$|\$([^$\n]+?)\$/g;

/**
 * Message text with math rendered by KaTeX. Everything else stays plain text:
 * React escapes it, so HTML in the content is never interpreted.
 */
export function MessageText({ content }: { content: string }) {
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
