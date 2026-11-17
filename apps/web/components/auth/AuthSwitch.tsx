import Link from "next/link";
import { safeNext } from "@/lib/auth";

/**
 * `path` with the raw `?next=` passed on, only when it is a safe path other than "/"
 * (specs/features/platform/web-signup.md §2.3).
 */
export function withNext(path: string, next: string | undefined): string {
  const target = safeNext(next);
  return target === "/" ? path : `${path}?next=${encodeURIComponent(target)}`;
}

/** "ยังไม่มีบัญชี? สมัครสมาชิก" under the login form, and the other way round (web-signup.md §2.1 item 8, §2.2). */
export function AuthSwitch({ question, label, path, next }: { question: string; label: string; path: string; next?: string }) {
  return (
    <p className="text-center text-sm text-zinc-600">
      {question}{" "}
      <Link href={withNext(path, next)} className="text-zinc-900 underline">
        {label}
      </Link>
    </p>
  );
}
