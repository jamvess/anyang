import Link from "next/link";
import { withNext } from "@/lib/auth";

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
