"use client";

import Link from "next/link";
import { useEffect, useLayoutEffect, useRef, useState } from "react";
import type { components } from "@/lib/api";
import { ApiError, errorCode, getJSON, isAuthRedirect } from "./api";
import { apiFetch } from "@/lib/auth";
import { POLL_MS } from "./poll";
import { materialStrings as t } from "./strings";

// Spec: specs/features/exam-prep/upload-page.md §2.2, §2.3 · wireframe S11 · api.md v1.11 + v1.16.
// "ลองใหม่" on a failed file or step: specs/features/exam-prep/ingestion-retry.md §2.1.
// Statuses, details and step labels come from the API; this page only shows them.

type Ingestion = components["schemas"]["Ingestion"];
type Status = keyof typeof t.status;

type View =
  | { kind: "loading" }
  | { kind: "notFound" }
  | { kind: "failed" }
  | { kind: "ready"; data: Ingestion; failed: boolean };

/** What a "ลองใหม่" button retries: one file, or the prep's steps. */
type Target = { kind: "file"; id: string } | { kind: "steps" };
const targetKey = (target: Target) => (target.kind === "file" ? `file:${target.id}` : "steps");

const SYMBOL: Record<Status, string> = { queued: "○", pending: "○", running: "◐", done: "✓", failed: "✕" };

function Mark({ status }: { status: Status }) {
  return (
    <span role="img" aria-label={t.status[status]} className="w-4 shrink-0 text-center">
      {SYMBOL[status]}
    </span>
  );
}

export function ProgressPage({ prepId, navigate }: { prepId: string; navigate: (href: string) => void }) {
  const [view, setView] = useState<View>({ kind: "loading" });
  const [attempt, setAttempt] = useState(0);
  // Retries on their way (button disabled) and retries that failed (message under the button).
  const [sending, setSending] = useState<ReadonlySet<string>>(new Set());
  const [refused, setRefused] = useState<ReadonlySet<string>>(new Set());
  // A ready scope that arrives after the user left must not move them (§2.3).
  const visible = useRef(true);
  useLayoutEffect(() => {
    visible.current = true;
    return () => {
      visible.current = false;
    };
  }, []);

  // Asks at once, then every POLL_MS until the scope is ready, nothing was sent, or a poll fails.
  // Hiding the page (Next's <Activity>) stops it; showing it again asks at once (§2.3).
  useEffect(() => {
    const controller = new AbortController();
    let timer: ReturnType<typeof setTimeout> | undefined;
    const run = async () => {
      try {
        const data = await getJSON<Ingestion>(`/exam-preps/${prepId}/ingestion`, controller.signal);
        if (controller.signal.aborted) return;
        setView({ kind: "ready", data, failed: false });
        if (data.scope_ready) {
          if (visible.current) navigate(`/preps/${prepId}/scope`);
          return;
        }
        if (data.files.length === 0) return; // nothing to wait for (§2.2 item 6)
        timer = setTimeout(run, POLL_MS);
      } catch (e) {
        if (controller.signal.aborted || isAuthRedirect(e)) return;
        if (e instanceof ApiError && e.status === 404) setView({ kind: "notFound" });
        // Keep the last result on screen (§2.2 item 7).
        else setView((prev) => (prev.kind === "ready" ? { ...prev, failed: true } : { kind: "failed" }));
      }
    };
    run();
    return () => {
      controller.abort();
      clearTimeout(timer);
    };
  }, [prepId, attempt, navigate]);

  function retry() {
    setView((prev) => (prev.kind === "ready" ? { ...prev, failed: false } : { kind: "loading" }));
    setAttempt((n) => n + 1);
  }

  /** Asks the API at once instead of waiting for the next POLL_MS (ingestion-retry.md §2.1 item 3). */
  const pollNow = () => setAttempt((n) => n + 1);

  async function retryTarget(target: Target) {
    const key = targetKey(target);
    if (sending.has(key)) return;
    const mark = (set: ReadonlySet<string>, on: boolean) => {
      const next = new Set(set);
      if (on) next.add(key);
      else next.delete(key);
      return next;
    };
    setSending((s) => mark(s, true));
    setRefused((s) => mark(s, false));
    const path =
      target.kind === "file" ? `/materials/${target.id}/retry` : `/exam-preps/${prepId}/ingestion/retry`;
    try {
      const res = await apiFetch(path, { method: "POST" });
      // 409 not_failed: someone retried it already · 404: the poll shows what happened to the prep.
      if (res.ok || res.status === 409 || res.status === 404) pollNow();
      else if (!isAuthRedirect(new ApiError(res.status, await errorCode(res)))) setRefused((s) => mark(s, true));
    } catch {
      setRefused((s) => mark(s, true));
    } finally {
      setSending((s) => mark(s, false));
    }
  }

  // A plain function, not a component: a component declared here would be a new type on every
  // render and React would replace the button (losing focus and the element a test holds).
  function retryButton(target: Target, name: string) {
    const key = targetKey(target);
    return (
      <span className="flex flex-col items-start">
        <button
          type="button"
          aria-label={name}
          disabled={sending.has(key)}
          onClick={() => void retryTarget(target)}
          className="text-xs underline disabled:opacity-50"
        >
          {t.retry}
        </button>
        {refused.has(key) && (
          <span role="alert" className="text-xs text-red-700">
            {t.retryFailed}
          </span>
        )}
      </span>
    );
  }

  const home = (
    <Link href="/" className="text-sm text-zinc-600 underline">
      {t.backHome}
    </Link>
  );

  if (view.kind === "notFound") {
    return (
      <div className="flex flex-col items-start gap-2 p-8 text-sm">
        <p>{t.notFound}</p>
        {home}
      </div>
    );
  }

  const data = view.kind === "ready" ? view.data : null;
  const failed = view.kind === "failed" || (view.kind === "ready" && view.failed);
  const nothingSent = data !== null && data.files.length === 0 && !data.scope_ready;
  // A failed file is retried on its row; the steps only when no file failed, on the first failed
  // step (ingestion-retry.md §2.1 items 1–2).
  const fileFailed = data?.files.some((f) => f.status === "failed") ?? false;
  const failedStep = fileFailed ? -1 : (data?.steps.findIndex((s) => s.status === "failed") ?? -1);

  return (
    <main className="mx-auto flex w-full max-w-2xl flex-col gap-4 p-8">
      <div>
        <h1 className="text-lg font-semibold">{t.progressTitle}</h1>
        <p className="text-sm text-zinc-500">{t.progressSubtitle}</p>
      </div>
      {view.kind === "loading" && <p className="text-sm text-zinc-600">{t.loading}</p>}
      {nothingSent && (
        <div className="flex flex-col items-start gap-2 text-sm">
          <p>{t.nothingSent}</p>
          <Link href={`/preps/${prepId}/upload`} className="underline">
            {t.addFiles}
          </Link>
        </div>
      )}
      {data && data.files.length > 0 && (
        <ul className="flex flex-col gap-1 text-sm">
          {data.files.map((f) => (
            <li key={f.material_id} className="flex items-baseline gap-2">
              <Mark status={f.status} />
              <span className="font-medium">{f.file_name}</span>
              {f.status === "failed" ? (
                <>
                  <span className="text-xs text-red-700">{f.error ?? t.readFailed}</span>
                  {retryButton({ kind: "file", id: f.material_id }, t.retryFile(f.file_name))}
                </>
              ) : (
                f.detail && <span className="text-xs text-zinc-500">{f.detail}</span>
              )}
            </li>
          ))}
        </ul>
      )}
      {data && data.steps.length > 0 && (
        <ul className="flex flex-col gap-1 border-t border-zinc-200 pt-3 text-sm">
          {data.steps.map((s, i) => (
            <li key={s.label} className="flex items-baseline gap-2">
              <Mark status={s.status} />
              <span>{s.label}</span>
              {i === failedStep && retryButton({ kind: "steps" }, t.retryStep(s.label))}
            </li>
          ))}
        </ul>
      )}
      {failed && (
        <div className="flex flex-col items-start gap-2 text-sm">
          <p role="alert" className="text-red-700">
            {t.progressFailed}
          </p>
          <button type="button" onClick={retry} className="underline">
            {t.retry}
          </button>
        </div>
      )}
      {home}
    </main>
  );
}
