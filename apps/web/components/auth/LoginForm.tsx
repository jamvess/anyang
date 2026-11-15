"use client";

import { type FormEvent, useEffect, useState } from "react";
import { safeNext } from "@/lib/auth";
import { createClient } from "@/lib/supabase";
import { authStrings as t } from "./strings";

/** Supabase says the email or the password is wrong (the other errors ask to try again). */
function isWrongCredentials(error: { code?: string; status?: number }): boolean {
  return error.code === "invalid_credentials" || error.status === 400;
}

/**
 * Email + password sign-in (spec: specs/features/platform/web-login.md §2.1). `next` is the raw
 * `?next=` value; only a path of this site is followed. Tests pass their own `navigate`.
 */
export function LoginForm({ next, navigate }: { next?: string; navigate: (href: string) => void }) {
  const target = safeNext(next);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Signed in already: go on at once (§2.1 item 6).
  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const { data } = await createClient().auth.getSession();
        if (alive && data.session) navigate(target);
      } catch {
        // No Supabase env (a dev machine on the stubs): stay on the form.
      }
    })();
    return () => {
      alive = false;
    };
  }, [navigate, target]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy) return;
    setBusy(true);
    setError(null);
    try {
      const { error: failure } = await createClient().auth.signInWithPassword({ email, password });
      if (!failure) {
        navigate(target);
        return;
      }
      setError(isWrongCredentials(failure) ? t.wrongCredentials : t.failed);
    } catch {
      setError(t.failed);
    }
    setPassword("");
    setBusy(false);
  }

  return (
    <form onSubmit={submit} className="mx-auto flex w-full max-w-sm flex-col gap-4 p-8">
      <h1 className="text-xl font-semibold text-zinc-900">{t.title}</h1>
      <label className="flex flex-col gap-1 text-sm text-zinc-700">
        {t.email}
        <input
          type="email"
          required
          autoComplete="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="rounded-md border border-zinc-300 px-3 py-2 text-base text-zinc-900"
        />
      </label>
      <label className="flex flex-col gap-1 text-sm text-zinc-700">
        {t.password}
        <input
          type="password"
          required
          autoComplete="current-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="rounded-md border border-zinc-300 px-3 py-2 text-base text-zinc-900"
        />
      </label>
      {error && (
        <p role="alert" className="text-sm text-red-700">
          {error}
        </p>
      )}
      <button
        type="submit"
        disabled={busy}
        className="rounded-md bg-zinc-900 px-4 py-2 text-white disabled:opacity-60"
      >
        {busy ? t.submitting : t.submit}
      </button>
    </form>
  );
}
