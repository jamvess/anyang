"use client";

import Link from "next/link";
import { type FormEvent, type ReactNode, useEffect, useState } from "react";
import { safeNext } from "@/lib/auth";
import { createClient } from "@/lib/supabase";
import { AuthSwitch, withNext } from "./AuthSwitch";
import { authStrings as t } from "./strings";

const INPUT = "rounded-md border border-zinc-300 px-3 py-2 text-base text-zinc-900";

/** Supabase Auth error codes → the message shown (spec §2.1 item 5); any other code asks to try again. */
const MESSAGES: Record<string, string> = {
  user_already_exists: t.emailTaken,
  email_exists: t.emailTaken,
  weak_password: t.weakPassword,
  email_address_invalid: t.emailInvalid,
  signup_disabled: t.signupDisabled,
};

/**
 * Email + password sign-up (spec: specs/features/platform/web-signup.md §2.1). The password rule
 * belongs to Supabase (§2.1 item 6): no length is checked here. `next` is the raw `?next=` value.
 */
export function SignupForm({ next, navigate }: { next?: string; navigate: (href: string) => void }) {
  const target = safeNext(next);
  const loginHref = withNext("/login", next);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [checkEmail, setCheckEmail] = useState(false);

  // Signed in already: go on at once (§2.1 item 7).
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

  /** Shows the message, keeps the email and clears both passwords (§2.1 item 5). */
  function fail(message: string) {
    setError(message);
    setPassword("");
    setConfirm("");
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy) return;
    setError(null);
    if (password !== confirm) {
      fail(t.passwordMismatch);
      return;
    }
    setBusy(true);
    try {
      const { data, error: failure } = await createClient().auth.signUp({ email, password });
      if (!failure) {
        // Confirm email is off on anyang-dev, so a session comes back (§2.1 item 3); without one the email must be confirmed (item 4).
        if (data.session) navigate(target);
        else setCheckEmail(true);
        return;
      }
      fail(MESSAGES[failure.code ?? ""] ?? t.signupFailed);
    } catch {
      fail(t.signupFailed);
    } finally {
      setBusy(false);
    }
  }

  if (checkEmail) {
    return (
      <div className="mx-auto flex w-full max-w-sm flex-col gap-4 p-8">
        <h1 className="text-xl font-semibold text-zinc-900">{t.signupTitle}</h1>
        <p role="status" className="text-sm text-zinc-700">
          {t.checkEmail}
        </p>
        <Link href={loginHref} className="text-sm text-zinc-900 underline">
          {t.toLogin}
        </Link>
      </div>
    );
  }

  const field = (label: string, input: ReactNode) => (
    <label className="flex flex-col gap-1 text-sm text-zinc-700">
      {label}
      {input}
    </label>
  );

  return (
    <form onSubmit={submit} className="mx-auto flex w-full max-w-sm flex-col gap-4 p-8">
      <h1 className="text-xl font-semibold text-zinc-900">{t.signupTitle}</h1>
      {field(
        t.email,
        <input type="email" required autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} className={INPUT} />,
      )}
      {field(
        t.password,
        <input type="password" required autoComplete="new-password" value={password} onChange={(e) => setPassword(e.target.value)} className={INPUT} />,
      )}
      {field(
        t.confirmPassword,
        <input type="password" required autoComplete="new-password" value={confirm} onChange={(e) => setConfirm(e.target.value)} className={INPUT} />,
      )}
      {error && (
        <p role="alert" className="text-sm text-red-700">
          {error}
          {error === t.emailTaken && (
            // A taken email: the way on is to sign in (wireframe S29 · AC-5).
            <>
              {" "}
              <Link href={loginHref} className="underline">
                {t.toLogin}
              </Link>
            </>
          )}
        </p>
      )}
      <button type="submit" disabled={busy} className="rounded-md bg-zinc-900 px-4 py-2 text-white disabled:opacity-60">
        {busy ? t.signupSubmitting : t.signupSubmit}
      </button>
      <AuthSwitch question={t.haveAccount} label={t.toLogin} path="/login" next={next} />
    </form>
  );
}
