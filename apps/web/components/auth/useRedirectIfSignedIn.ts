"use client";

import { useEffect } from "react";
import { createClient } from "@/lib/supabase";

/**
 * Signed in already: go on to `target` at once (web-login.md §2.1 item 6 · web-signup.md §2.1 item 7).
 * Shared by the login and sign-up forms (self-review PR #144).
 */
export function useRedirectIfSignedIn(target: string, navigate: (href: string) => void) {
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
}
