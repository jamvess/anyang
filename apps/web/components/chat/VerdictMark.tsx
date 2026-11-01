import { roomStrings as t } from "./strings";

// Spec: specs/features/check/verdict-mark.md · payload: api.md "SSE events" verdict, values from check/merge-rules.md.

/** Hand-written until the API schema has `VerdictEvent` (spec OQ 6); then use the generated type. */
export type VerdictData = {
  verdict: string;
  first_wrong_line?: number | null;
  error_type?: string | null;
};

/** False for a verdict with no mark: unknown value, malformed payload, or no_answer (AC-3, AC-4). */
export function hasVerdictMark(verdict: VerdictData): boolean {
  return Object.hasOwn(t.verdicts, verdict?.verdict) && verdict.error_type !== "no_answer";
}

/**
 * One-line check result above the tutor's words (wireframe S16, S22). Every value comes from the
 * API; error_type is never shown (OQ 3) and a no_answer gets no mark (OQ 4).
 */
export function VerdictMark({ verdict }: { verdict: VerdictData }) {
  if (!hasVerdictMark(verdict)) return null;
  const label = t.verdicts[verdict.verdict];
  const correct = verdict.verdict === "correct";
  const line = verdict.first_wrong_line;

  return (
    <p
      role="status"
      aria-label={t.verdict}
      data-verdict={verdict.verdict}
      className={`mt-4 text-xs font-medium ${correct ? "text-emerald-700" : "text-red-700"}`}
    >
      {correct ? "✓" : "✗"} {label}
      {typeof line === "number" && ` · ${t.verdictLine(line)}`}
    </p>
  );
}
