"use client";

import Link from "next/link";
import { useEffect, useLayoutEffect, useRef, useState } from "react";
import type { components } from "@/lib/api";
import { ApiError, getJSON, isAuthRedirect } from "./api";
import { POLL_MS } from "./poll";
import { materialStrings as t } from "./strings";

// Spec: specs/features/exam-prep/upload-page.md §2.2, §2.3 · wireframe S11 · api.md v1.11 + v1.16.
// Statuses, details and step labels come from the API; this page only shows them.

type Ingestion = components["schemas"]["Ingestion"];
type Status = keyof typeof t.status;

type View =
  | { kind: "loading" }
  | { kind: "notFound" }
  | { kind: "failed" }
  | { kind: "ready"; data: Ingestion; failed: boolean };

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
                <span className="text-xs text-red-700">{f.error ?? t.readFailed}</span>
              ) : (
                f.detail && <span className="text-xs text-zinc-500">{f.detail}</span>
              )}
            </li>
          ))}
        </ul>
      )}
      {data && data.steps.length > 0 && (
        <ul className="flex flex-col gap-1 border-t border-zinc-200 pt-3 text-sm">
          {data.steps.map((s) => (
            <li key={s.label} className="flex items-baseline gap-2">
              <Mark status={s.status} />
              <span>{s.label}</span>
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
