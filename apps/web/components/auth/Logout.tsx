"use client";

import { useEffect } from "react";
import { createClient } from "@/lib/supabase";
import { authStrings as t } from "./strings";

/**
 * Signs out, then goes to the login page, even when sign-out fails (the client drops the session
 * in the cookie anyway · spec: specs/features/platform/web-login.md §2.2).
 */
export function Logout({ navigate }: { navigate: (href: string) => void }) {
  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        // This browser only: the student's other devices stay signed in (self-review PR #138).
        await createClient().auth.signOut({ scope: "local" });
      } catch {
        // Go to the login page all the same.
      }
      if (alive) navigate("/login");
    })();
    return () => {
      alive = false;
    };
  }, [navigate]);

  return <p className="p-8 text-sm text-zinc-600">{t.loggingOut}</p>;
}
