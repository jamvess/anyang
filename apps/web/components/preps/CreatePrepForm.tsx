"use client";

import Link from "next/link";
import { type FormEvent, useLayoutEffect, useRef, useState } from "react";
import type { components } from "@/lib/api";
import { apiFetch } from "@/lib/auth";
import { prepStrings as t } from "./strings";

type CreateExamPrepRequest = components["schemas"]["CreateExamPrepRequest"];

/** The Thai message for a refused create (spec §2.2 item 4); the API decides the rules. */
async function messageOf(res: Response): Promise<string> {
  if (res.status !== 422) return t.saveFailed;
  const body = await res.json().catch(() => null);
  return body?.error?.code === "exam_date_past" ? t.examDatePast : t.invalid;
}

/**
 * Create an exam prep (S08 · spec: specs/features/exam-prep/prep-list-page.md §2.2). Tests pass
 * their own `navigate`. No rule of the API is checked again here, beyond the fields' own limits.
 */
export function CreatePrepForm({ navigate }: { navigate: (href: string) => void }) {
  const [title, setTitle] = useState("");
  const [examDate, setExamDate] = useState("");
  const [minutes, setMinutes] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  // Next keeps a page it leaves hidden (React <Activity>, `cacheComponents`), with its state. A
  // create that ends after the user left must not pull them back (self-review PR #139).
  const visible = useRef(true);
  useLayoutEffect(() => {
    visible.current = true;
    return () => {
      visible.current = false;
    };
  }, []);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy) return;
    setBusy(true);
    setError(null);
    const body: CreateExamPrepRequest = { title, exam_date: examDate };
    if (minutes.trim() !== "") body.daily_minutes = Number(minutes);
    try {
      const res = await apiFetch("/exam-preps", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (res.ok) {
        // A fresh form for the next visit: the hidden page keeps its state (browser check, 15 Nov:
        // the second create stayed on "กำลังสร้าง…"). Then back to the list (no upload page yet).
        setTitle("");
        setExamDate("");
        setMinutes("");
        setBusy(false);
        if (visible.current) navigate("/");
        return;
      }
      // 401: apiFetch is already on its way to the login page (web-login.md §2.3).
      if (res.status !== 401) setError(await messageOf(res));
    } catch {
      setError(t.saveFailed);
    }
    setBusy(false);
  }

  return (
    <form onSubmit={submit} className="mx-auto flex w-full max-w-sm flex-col gap-4 p-8">
      <h1 className="text-xl font-semibold text-zinc-900">{t.formTitle}</h1>
      <label className="flex flex-col gap-1 text-sm text-zinc-700">
        {t.name}
        <input
          type="text"
          required
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          className="rounded-md border border-zinc-300 px-3 py-2 text-base text-zinc-900"
        />
      </label>
      <label className="flex flex-col gap-1 text-sm text-zinc-700">
        {t.examDate}
        <input
          type="date"
          required
          value={examDate}
          onChange={(e) => setExamDate(e.target.value)}
          className="rounded-md border border-zinc-300 px-3 py-2 text-base text-zinc-900"
        />
      </label>
      <label className="flex flex-col gap-1 text-sm text-zinc-700">
        {t.dailyMinutes}
        <input
          type="number"
          min={1}
          max={1440}
          value={minutes}
          onChange={(e) => setMinutes(e.target.value)}
          className="rounded-md border border-zinc-300 px-3 py-2 text-base text-zinc-900"
        />
      </label>
      {error && (
        <p role="alert" className="text-sm text-red-700">
          {error}
        </p>
      )}
      <div className="flex items-center gap-4">
        <button
          type="submit"
          disabled={busy}
          className="rounded-md bg-zinc-900 px-4 py-2 text-white disabled:opacity-60"
        >
          {busy ? t.submitting : t.submit}
        </button>
        <Link href="/" className="text-sm text-zinc-600 underline">
          {t.cancel}
        </Link>
      </div>
    </form>
  );
}
