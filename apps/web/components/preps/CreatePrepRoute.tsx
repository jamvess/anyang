"use client";

import { useRouter } from "next/navigation";
import { useCallback } from "react";
import { CreatePrepForm } from "./CreatePrepForm";

/** CreatePrepForm with the app router; tests render it with their own `navigate`. */
export function CreatePrepRoute() {
  const router = useRouter();
  const navigate = useCallback((href: string) => router.push(href), [router]);
  return <CreatePrepForm navigate={navigate} />;
}
