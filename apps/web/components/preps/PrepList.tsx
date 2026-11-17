"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import type { components } from "@/lib/api";
import { apiFetch } from "@/lib/auth";
import { prepStrings as t } from "./strings";

type ExamPrep = components["schemas"]["ExamPrep"];
type Load = { kind: "loading" } | { kind: "ready"; preps: ExamPrep[] } | { kind: "failed" };

/** Where a card goes, by its stage (spec §2.1 item 5 · upload-page.md §2.4). */
export function prepHref(prep: ExamPrep): string | null {
  switch (prep.stage) {
    case "materials":
      return `/preps/${prep.id}/upload`;
    case "processing":
      return `/preps/${prep.id}/progress`;
    case "scope":
      return `/preps/${prep.id}/scope`;
    case "tutoring":
      return `/preps/${prep.id}/room`;
    default:
      return null;
  }
}

function daysText(days: number): string {
  if (days >= 1) return t.daysLeft(days);
  return days === 0 ? t.examToday : t.examPassed;
}

function Card({ prep }: { prep: ExamPrep }) {
  const body = (
    <div className="flex flex-col gap-1 rounded-lg border border-zinc-200 p-4">
      <span className="font-medium text-zinc-900">{prep.title}</span>
      <span className="text-sm text-zinc-600">{daysText(prep.days_left)}</span>
      <span className="text-sm text-zinc-600">{t.stage[prep.stage]}</span>
      {prep.readiness !== null && (
        <span className="text-sm text-zinc-600">{t.readiness(Math.round(prep.readiness * 100))}</span>
      )}
      {prep.topics_not_passed !== null && (
        <span className="text-sm text-zinc-600">{t.notPassed(prep.topics_not_passed)}</span>
      )}
    </div>
  );
  const href = prepHref(prep);
  return (
    <li data-prep-id={prep.id}>
      {href ? (
        <Link href={href} className="block hover:bg-zinc-50">
          {body}
        </Link>
      ) : (
        body
      )}
    </li>
  );
}

/** The exam preps of the user, from GET /exam-preps (spec: specs/features/exam-prep/prep-list-page.md §2.1). */
export function PrepList() {
  const [load, setLoad] = useState<Load>({ kind: "loading" });
  const [attempt, setAttempt] = useState(0);

  // Runs again each time the page is shown (Next hides pages with <Activity>), so a prep created
  // meanwhile appears; leaving the page aborts the request.
  useEffect(() => {
    const controller = new AbortController();
    (async () => {
      try {
        const res = await apiFetch("/exam-preps", { signal: controller.signal });
        if (res.status === 401) return; // apiFetch is on its way to the login page
        if (!res.ok) throw new Error(`API ${res.status}`);
        const preps: ExamPrep[] = await res.json();
        setLoad({ kind: "ready", preps });
      } catch {
        if (!controller.signal.aborted) setLoad({ kind: "failed" });
      }
    })();
    return () => controller.abort();
  }, [attempt]);

  function retry() {
    setLoad({ kind: "loading" });
    setAttempt((n) => n + 1);
  }

  return (
    <main className="mx-auto flex w-full max-w-2xl flex-col gap-4 p-8">
      <header className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-zinc-900">{t.title}</h1>
        <Link href="/logout" className="text-sm text-zinc-600 underline">
          {t.logout}
        </Link>
      </header>
      {load.kind === "loading" && <p className="text-sm text-zinc-600">{t.loading}</p>}
      {load.kind === "failed" && (
        <div className="flex flex-col items-start gap-2">
          <p role="alert" className="text-sm text-red-700">
            {t.loadFailed}
          </p>
          <button type="button" onClick={retry} className="rounded-md border border-zinc-300 px-3 py-1 text-sm">
            {t.retry}
          </button>
        </div>
      )}
      {load.kind === "ready" && (
        <>
          <Link href="/preps/new" className="self-start rounded-md bg-zinc-900 px-4 py-2 text-white">
            {t.create}
          </Link>
          {load.preps.length === 0 ? (
            <p className="text-sm text-zinc-600">{t.empty}</p>
          ) : (
            <ul className="flex flex-col gap-3">
              {load.preps.map((prep) => (
                <Card key={prep.id} prep={prep} />
              ))}
            </ul>
          )}
        </>
      )}
    </main>
  );
}
