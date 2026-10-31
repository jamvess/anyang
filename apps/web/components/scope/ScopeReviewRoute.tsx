"use client";

import { useRouter } from "next/navigation";
import { ScopeReview } from "./ScopeReview";

/** ScopeReview with the app router; tests render ScopeReview with their own `navigate`. */
export function ScopeReviewRoute({ prepId }: { prepId: string }) {
  const router = useRouter();
  return <ScopeReview prepId={prepId} navigate={(href) => router.push(href)} />;
}
