import { Tex } from "@/components/math/Tex";
import { roomStrings as t } from "./strings";

// Spec: specs/features/tutor/problem-card.md · payload: api.md "SSE events" problem (no answer in it).

export type ProblemData = {
  problem_id: string;
  /** Plain LaTeX without $ delimiters (api.md Conventions). */
  text_latex: string;
  difficulty: number;
  purpose: string;
};

/** The problem the tutor gives. No answer buttons (TM-06), no timer (TM-14), no difficulty or purpose shown. */
export function ProblemCard({ problem }: { problem: ProblemData }) {
  if (!problem.text_latex) return null;
  return (
    <div
      role="region"
      aria-label={t.problem}
      data-problem-id={problem.problem_id}
      className="mt-4 rounded-xl border border-zinc-200 bg-white px-4 py-3"
    >
      <p className="font-mono text-xs uppercase tracking-wide text-zinc-400">{t.problem}</p>
      <Tex math={problem.text_latex} display />
    </div>
  );
}
