"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import type { components } from "@/lib/api";
import { MessageText } from "@/components/chat/MessageText";
import { apiFetch } from "@/lib/auth";
import { scopeStrings as t } from "./strings";

// Spec: specs/features/scope/scope-review.md · wireframe S12, S38 · on the API of scope-db.md (§2 "ต่อ API จริง").
// Stars, order and reasons come from the API; this page only shows them (apps/web/CLAUDE.md).

/** Question `text` uses `$…$` like room messages (OQ 7). */
type Question = components["schemas"]["PastQuestion"];
type Scope = components["schemas"]["Scope"];
type Sources = components["schemas"]["TopicSources"];

type Load =
  | { kind: "loading" }
  | { kind: "ready"; scope: Scope }
  | { kind: "notFound" }
  | { kind: "notReady" }
  | { kind: "failed" };
type SourcesState = { kind: "loading" } | { kind: "ready"; sources: Sources } | { kind: "failed" };
type ConfirmError = null | "failed" | "empty";

const MAX_STARS = 3;

/** A refused request: its status and the API's error code (api.md Conventions). */
class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly code: string | null,
  ) {
    super(`API ${status}${code ? ` ${code}` : ""}`);
  }
}

async function errorOf(res: Response): Promise<ApiError> {
  const body = await res.json().catch(() => null);
  return new ApiError(res.status, body?.error?.code ?? null);
}

async function getJSON<T>(path: string, signal?: AbortSignal): Promise<T> {
  const res = await apiFetch(path, { signal });
  if (!res.ok) throw await errorOf(res);
  return res.json();
}

/** 401: `apiFetch` is already on its way to the login page, so the page shows no error (AC-23). */
const toLogin = (e: unknown) => e instanceof ApiError && e.status === 401;

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
  const [confirmError, setConfirmError] = useState<ConfirmError>(null);
  const room = `/preps/${prepId}/room`;

  // Runs again each time Next shows this page again (it hides pages with <Activity>), so a scope
  // confirmed meanwhile is read-only (AC-24); leaving the page aborts the request.
  useEffect(() => {
    const controller = new AbortController();
    getJSON<Scope>(`/exam-preps/${prepId}/scope`, controller.signal).then(
      (scope) => setLoad({ kind: "ready", scope }),
      (e) => {
        if (controller.signal.aborted || toLogin(e)) return;
        if (e instanceof ApiError && e.status === 404) setLoad({ kind: "notFound" });
        else if (e instanceof ApiError && e.code === "scope_not_ready") setLoad({ kind: "notReady" });
        else setLoad({ kind: "failed" });
      },
    );
    return () => controller.abort();
  }, [prepId, attempt]);

  function reload() {
    setLoad({ kind: "loading" });
    setAttempt((n) => n + 1);
  }

  function fetchSources(id: string) {
    setSources((prev) => ({ ...prev, [id]: { kind: "loading" } }));
    getJSON<Sources>(`/topics/${id}/sources`).then(
      (s) => setSources((prev) => ({ ...prev, [id]: { kind: "ready", sources: s } })),
      (e) => toLogin(e) || setSources((prev) => ({ ...prev, [id]: { kind: "failed" } })),
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
    setConfirmError(null);
    try {
      const res = await apiFetch(`/exam-preps/${prepId}/scope/confirm`, { method: "POST" });
      const code = res.ok ? null : (await errorOf(res)).code;
      // Next keeps this page hidden with its state: a later visit must not find the button stuck
      // (self-review PR #139, as the create form).
      setConfirming(false);
      // Confirmed already (another tab, a second click): that is what the user wanted (AC-22).
      if (res.ok || code === "scope_already_confirmed") navigate(room);
      else if (code === "scope_empty") setConfirmError("empty");
      else if (res.status !== 401) setConfirmError("failed");
    } catch {
      setConfirmError("failed");
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
  if (load.kind === "notReady") {
    // api.md sends the user to the progress page (S11) until ingestion is done; it does not exist yet.
    return (
      <div className="flex flex-col items-start gap-2 p-8 text-sm">
        <p>{t.notReady}</p>
        <button type="button" onClick={reload} className="underline">
          {t.retry}
        </button>
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
        <button type="button" onClick={reload} className="underline">
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
          {confirmError && (
            <p role="alert" className="mt-1 text-xs text-red-700">
              {confirmError === "empty" ? t.scopeEmpty : t.confirmFailed}
            </p>
          )}
          <p className="mt-2 text-xs text-zinc-400">{t.hint}</p>
        </div>
      )}
    </main>
  );
}
