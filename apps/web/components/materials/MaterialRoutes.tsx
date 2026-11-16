"use client";

import { useRouter } from "next/navigation";
import { useCallback } from "react";
import { ProgressPage } from "./ProgressPage";
import { UploadPage } from "./UploadPage";

// The pages with the app router; tests render them with their own `navigate` (like ScopeReviewRoute).

function usePush() {
  const router = useRouter();
  return useCallback((href: string) => router.push(href), [router]);
}

export function UploadRoute({ prepId }: { prepId: string }) {
  return <UploadPage prepId={prepId} navigate={usePush()} />;
}

export function ProgressRoute({ prepId }: { prepId: string }) {
  return <ProgressPage prepId={prepId} navigate={usePush()} />;
}
