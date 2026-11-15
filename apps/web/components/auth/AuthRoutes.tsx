"use client";

import { useRouter } from "next/navigation";
import { LoginForm } from "./LoginForm";
import { Logout } from "./Logout";

/** LoginForm and Logout with the app router; tests render them with their own `navigate`. */
export function LoginRoute({ next }: { next?: string }) {
  const router = useRouter();
  return <LoginForm next={next} navigate={(href) => router.replace(href)} />;
}

export function LogoutRoute() {
  const router = useRouter();
  return <Logout navigate={(href) => router.replace(href)} />;
}
