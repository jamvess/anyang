"use client";

import { type FormEvent, useState } from "react";
import { safeNext } from "@/lib/auth";
import { createClient } from "@/lib/supabase";
import { AuthSwitch } from "./AuthSwitch";
import { authStrings as t } from "./strings";
import { useRedirectIfSignedIn } from "./useRedirectIfSignedIn";

/** Supabase says the email or the password is wrong; other 400s (an unconfirmed email, a bad
 * request) ask to try again instead of blaming the password (self-review PR #138). */
function isWrongCredentials(error: { code?: string }): boolean {
  return error.code === "invalid_credentials";
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
  useRedirectIfSignedIn(target, navigate);

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
      <AuthSwitch question={t.noAccount} label={t.toSignup} path="/signup" next={next} />
    </form>
  );
}
