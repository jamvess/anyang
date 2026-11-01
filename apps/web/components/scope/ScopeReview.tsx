"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { MessageText } from "@/components/chat/MessageText";
import { apiUrl } from "@/lib/httpTransport";
import { scopeStrings as t } from "./strings";

// Spec: specs/features/scope/scope-review.md · wireframe S12, S38.
// Stars, order and reasons come from the API; this page only shows them (apps/web/CLAUDE.md).

/**
 * Hand-written until the API has these schemas (spec OQ 5–8); then use the generated types.
 * Question `text` uses `$…$` like room messages (OQ 7).
 */
type Question = { id: string; label: string; text: string; map_note: string | null };
type Topic = {
  id: string;
  order: number;
  name: string;
  stars: number | null;
  reason: string;
  source_label: string;
  origin: "doc" | "user";
};
type Scope = {
  prep_name: string;
  days_left: number;
  status: "draft" | "confirmed";
  topics: Topic[];
  unmapped_questions: Question[];
};
type Sources = { excerpts: { material_name: string; page: number; text: string }[]; questions: Question[] };

type Load = { kind: "loading" } | { kind: "ready"; scope: Scope } | { kind: "notFound" } | { kind: "failed" };
type SourcesState = { kind: "loading" } | { kind: "ready"; sources: Sources } | { kind: "failed" };

const MAX_STARS = 3;

async function getJSON<T>(path: string): Promise<T> {
  const res = await fetch(apiUrl(path));
  if (!res.ok) throw Object.assign(new Error(`API ${res.status}`), { status: res.status });
  return res.json();
}

function Stars({ stars }: { stars: number | null }) {
  const known = typeof stars === "number" && stars >= 0 && stars <= MAX_STARS;
  return (
    <span className="text-xs tracking-wider" aria-label={known ? t.stars(stars) : t.starsUnknown}>
      {Array.from({ length: MAX_STARS }, (_, k) =>
        known && k < stars ? (
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
  );
}

function Tag({ children }: { children: string }) {
  return <span className="ml-2 rounded bg-zinc-100 px-1.5 py-0.5 font-mono text-[10px] text-zinc-500">{children}</span>;
}

function QuestionItem({ q }: { q: Question }) {
  return (
    <li data-question-id={q.id} className="flex gap-3 py-1 text-sm">
      <span className="w-40 shrink-0 font-mono text-xs text-zinc-400">{q.label}</span>
      <div className="min-w-0 flex-1">
        <MessageText content={q.text} />
        {q.map_note && <p className="text-xs text-zinc-400">{t.aiNote(q.map_note)}</p>}
      </div>
    </li>
  );
}

function TopicDetail({ id, state, onRetry }: { id: string; state: SourcesState | undefined; onRetry: () => void }) {
  return (
    <div data-topic-detail={id} className="px-4 pb-3 text-sm">
      {(!state || state.kind === "loading") && <p className="text-xs text-zinc-400">{t.sourcesLoading}</p>}
      {state?.kind === "failed" && (
        <p className="text-xs text-red-700">
          {t.sourcesFailed}{" "}
          <button type="button" onClick={onRetry} className="underline">
            {t.retry}
          </button>
        </p>
      )}
      {state?.kind === "ready" && (
        <>
          {state.sources.excerpts.map((e, i) => (
            <div key={i} className="mb-2">
              <p className="font-mono text-xs text-zinc-400">{t.fromSheet(e.material_name, e.page)}</p>
              {/* Sheet text is data from the user's file: plain text, never HTML (ai-orchestration §2.3.9). */}
              <p className="border-l-2 border-zinc-200 pl-2.5 text-xs text-zinc-600">{e.text}</p>
            </div>
          ))}
          {state.sources.questions.length === 0 ? (
            <p className="text-xs text-zinc-400">{t.noQuestions}</p>
          ) : (
            <>
              <p className="mt-2 font-mono text-xs text-zinc-400">{t.questions(state.sources.questions.length)}</p>
              <ul>
                {state.sources.questions.map((q) => (
                  <QuestionItem key={q.id} q={q} />
                ))}
              </ul>
            </>
          )}
        </>
      )}
    </div>
  );
}

export function ScopeReview({ prepId, navigate }: { prepId: string; navigate: (href: string) => void }) {
  const [load, setLoad] = useState<Load>({ kind: "loading" });
  const [attempt, setAttempt] = useState(0);
  const [open, setOpen] = useState<Set<string>>(new Set());
  const [sources, setSources] = useState<Record<string, SourcesState>>({});
  const [confirming, setConfirming] = useState(false);
  const [confirmFailed, setConfirmFailed] = useState(false);
  const room = `/preps/${prepId}/room`;

  useEffect(() => {
    let live = true;
    getJSON<Scope>(`/exam-preps/${prepId}/scope`).then(
      (scope) => live && setLoad({ kind: "ready", scope }),
      (e) => live && setLoad({ kind: e?.status === 404 ? "notFound" : "failed" }),
    );
    return () => {
      live = false;
    };
  }, [prepId, attempt]);

  function fetchSources(id: string) {
    setSources((prev) => ({ ...prev, [id]: { kind: "loading" } }));
    getJSON<Sources>(`/topics/${id}/sources`).then(
      (s) => setSources((prev) => ({ ...prev, [id]: { kind: "ready", sources: s } })),
      () => setSources((prev) => ({ ...prev, [id]: { kind: "failed" } })),
    );
  }

  function toggle(id: string) {
    const opening = !open.has(id);
    setOpen((prev) => {
      const next = new Set(prev);
      if (opening) next.add(id);
      else next.delete(id);
      return next;
    });
    // Loaded once; reopening uses what is already there (AC-10).
    if (opening && !sources[id]) fetchSources(id);
  }

  async function confirm() {
    if (confirming) return;
    setConfirming(true);
    setConfirmFailed(false);
    try {
      const res = await fetch(apiUrl(`/exam-preps/${prepId}/scope/confirm`), { method: "POST" });
      if (!res.ok) throw new Error(`API ${res.status}`);
      navigate(room);
    } catch {
      setConfirmFailed(true);
      setConfirming(false);
    }
  }

  if (load.kind === "loading") return <p className="p-8 text-sm text-zinc-600">{t.loading}</p>;
  if (load.kind === "notFound") {
    return (
      <div className="p-8 text-sm">
        <p className="mb-2">{t.notFound}</p>
        <Link href="/" className="underline">
          {t.backHome}
        </Link>
      </div>
    );
  }
  if (load.kind === "failed") {
    return (
      <div className="p-8 text-sm">
        <p className="mb-2">{t.loadFailed}</p>
        <button type="button" onClick={() => (setLoad({ kind: "loading" }), setAttempt((n) => n + 1))} className="underline">
          {t.retry}
        </button>
      </div>
    );
  }

  const { scope } = load;
  // Zero-star topics (excluded) go last, faded; the rest keep the API order (spec OQ 3).
  const topics = [...scope.topics.filter((x) => x.stars !== 0), ...scope.topics.filter((x) => x.stars === 0)];
  const confirmed = scope.status === "confirmed";

  return (
    <main className="mx-auto max-w-2xl px-8 py-8">
      <h1 className="text-lg font-semibold">{t.title}</h1>
      <p className="mb-4 text-sm text-zinc-500">{t.subtitle(scope.prep_name, scope.days_left)}</p>

      {topics.length === 0 && <p className="text-sm text-zinc-500">{t.noTopics}</p>}
      <ol className="flex flex-col gap-2">
        {topics.map((topic) => {
          const isOpen = open.has(topic.id);
          const excluded = topic.stars === 0;
          return (
            <li
              key={topic.id}
              className={`rounded-xl border bg-white ${isOpen ? "border-indigo-400" : "border-zinc-200"} ${excluded ? "opacity-50" : ""}`}
            >
              <button
                type="button"
                data-topic-id={topic.id}
                aria-expanded={isOpen}
                onClick={() => toggle(topic.id)}
                className="flex w-full items-center justify-between gap-3 px-4 py-3 text-left"
              >
                <span className="text-sm">
                  <span data-topic-name className="font-medium">{`${topic.order} · ${topic.name}`}</span>
                  <span className="ml-2 text-xs text-zinc-400">{`${topic.source_label} · ${topic.reason}`}</span>
                  {topic.origin === "user" && <Tag>{t.tagOutsideDocs}</Tag>}
                  {excluded && <Tag>{t.tagExcluded}</Tag>}
                </span>
                <Stars stars={topic.stars} />
              </button>
              {isOpen && <TopicDetail id={topic.id} state={sources[topic.id]} onRetry={() => fetchSources(topic.id)} />}
            </li>
          );
        })}
      </ol>

      {scope.unmapped_questions.length > 0 && (
        <section
          role="region"
          aria-label={t.unmapped(scope.unmapped_questions.length)}
          className="mt-4 rounded-xl border border-dashed border-zinc-300 px-4 py-3"
        >
          <p className="font-mono text-xs text-zinc-400">{t.unmapped(scope.unmapped_questions.length)}</p>
          <ul>
            {scope.unmapped_questions.map((q) => (
              <QuestionItem key={q.id} q={q} />
            ))}
          </ul>
          <p className="mt-2 text-xs text-zinc-500">{t.unmappedHint}</p>
        </section>
      )}

      {confirmed ? (
        <div className="mt-6 text-sm">
          <p className="mb-1 text-zinc-500">{t.confirmed}</p>
          <Link href={room} className="underline">
            {t.toRoom}
          </Link>
        </div>
      ) : (
        <div className="mt-6">
          <div className="flex gap-2">
            <button type="button" disabled className="rounded-lg border border-zinc-300 px-4 py-2 text-sm disabled:opacity-40">
              {t.edit}
            </button>
            <button
              type="button"
              disabled={confirming || topics.length === 0}
              onClick={confirm}
              className="rounded-lg bg-zinc-900 px-4 py-2 text-sm text-white disabled:opacity-40"
            >
              {t.confirm}
            </button>
          </div>
          <p className="mt-1 text-xs text-zinc-400">{t.editSoon}</p>
          {confirmFailed && (
            <p role="alert" className="mt-1 text-xs text-red-700">
              {t.confirmFailed}
            </p>
          )}
          <p className="mt-2 text-xs text-zinc-400">{t.hint}</p>
        </div>
      )}
    </main>
  );
}
