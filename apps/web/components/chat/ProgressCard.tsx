"use client";

import { useState } from "react";
import type { components } from "@/lib/api";
import { roomStrings as t } from "./strings";

// Spec: specs/features/tutor/progress-card.md · payload: api.md v1.4 "SSE events" progress_card.
// Every number comes from the API; this component only formats them (apps/web/CLAUDE.md).

/** Generated from the API schema (`pnpm gen:api`), not hand-written. */
export type ProgressCardData = components["schemas"]["ProgressCardEvent"];

/** Topics shown before the "more" button (wireframe S15). A UI value, not a learning-model one. */
export const PROGRESS_CARD_VISIBLE_TOPICS = 6;

const MAX_STARS = 3;

function Tag({ children }: { children: string }) {
  return <span className="ml-2 rounded bg-zinc-100 px-1.5 py-0.5 font-mono text-[10px] text-zinc-500">{children}</span>;
}

export function ProgressCard({ card }: { card: ProgressCardData }) {
  const [expanded, setExpanded] = useState(false);
  const hidden = card.topics.length - PROGRESS_CARD_VISIBLE_TOPICS;
  const shown = expanded || hidden <= 0 ? card.topics : card.topics.slice(0, PROGRESS_CARD_VISIBLE_TOPICS);

  return (
    <div role="group" aria-label={t.progress} className="mt-4 rounded-xl border border-zinc-200 bg-white p-4 text-sm">
      <div className="mb-2 flex items-center justify-between text-xs">
        <span className="font-mono uppercase tracking-wide text-zinc-400">{t.progress}</span>
        <span className="text-zinc-500">{t.daysLeft(card.days_left)}</span>
      </div>
      <div className="mb-1 flex gap-7">
        <div>
          <p className="text-xs text-zinc-500">{t.progressPassedLabel}</p>
          <p className="font-medium">{t.progressPassed(card.passed, card.total)}</p>
        </div>
        <div>
          <p className="text-xs text-zinc-500">{t.progressReadinessLabel}</p>
          <p className="font-medium">{Math.round(card.readiness * 100)}%</p>
        </div>
      </div>
      <p className="mb-2 text-xs text-zinc-400">{t.progressExplain}</p>
      <ul>
        {shown.map((topic) => (
          <li key={topic.id} data-topic className="flex items-center gap-2 border-b border-zinc-100 py-2 last:border-0">
            <span className="flex-1">
              <span data-topic-name>{topic.name}</span>
              {topic.review_due && <Tag>{t.tagReviewDue}</Tag>}
              {topic.origin === "user" && <Tag>{t.tagOutsideDocs}</Tag>}
            </span>
            <span className="text-xs tracking-wider" aria-label={`${topic.stars} ดาว`}>
              {Array.from({ length: MAX_STARS }, (_, k) =>
                k < topic.stars ? (
                  <span key={k} data-star-on className="text-amber-600">
                    ★
                  </span>
                ) : (
                  <span key={k} className="text-zinc-200">
                    ★
                  </span>
                ),
              )}
            </span>
            <span data-topic-level className="w-16 text-right text-xs text-zinc-500">
              {t.levels[topic.level] ?? t.levelUnknown}
            </span>
          </li>
        ))}
      </ul>
      {!expanded && hidden > 0 && (
        <button type="button" onClick={() => setExpanded(true)} className="mt-2 text-xs text-zinc-500 hover:text-zinc-700">
          {t.progressMore(hidden)}
        </button>
      )}
    </div>
  );
}
