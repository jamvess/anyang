import katex from "katex";

type TexProps = {
  /** LaTeX source, without surrounding $ or $$ delimiters. */
  math: string;
  /** Block (display) math when true, inline math otherwise. */
  display?: boolean;
};

/** The only place math is rendered in the app (see apps/web/CLAUDE.md). */
export function Tex({ math, display = false }: TexProps) {
  // throwOnError=false: a malformed formula from the tutor renders as red
  // source text instead of crashing the chat bubble.
  const html = katex.renderToString(math, {
    displayMode: display,
    throwOnError: false,
    output: "htmlAndMathml",
  });
  const Tag = display ? "div" : "span";
  return <Tag className="tex" dangerouslySetInnerHTML={{ __html: html }} />;
}
