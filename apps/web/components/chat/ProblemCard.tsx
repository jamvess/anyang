import { Tex } from "@/components/math/Tex";
import type { components } from "@/lib/api";
import { roomStrings as t } from "./strings";

// Spec: specs/features/tutor/problem-card.md · payload: api.md "SSE events" problem (no answer in it).

/** Generated from the API schema (`pnpm gen:api`). `text_latex` is plain LaTeX without $ (api.md Conventions). */
export type ProblemData = components["schemas"]["ProblemEvent"];

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
