"use client";

import { useRouter } from "next/navigation";
import { useCallback } from "react";
import { LoginForm } from "./LoginForm";
import { Logout } from "./Logout";

/** LoginForm and Logout with the app router; tests render them with their own `navigate`. */
export function LoginRoute({ next }: { next?: string }) {
  const router = useRouter();
  // Stable, so the session check on mount does not run again at every keystroke (self-review).
  const navigate = useCallback((href: string) => router.replace(href), [router]);
  return <LoginForm next={next} navigate={navigate} />;
}

export function LogoutRoute() {
  const router = useRouter();
  const navigate = useCallback((href: string) => router.replace(href), [router]);
  return <Logout navigate={navigate} />;
}
