// Tutor room over HTTP (spec: specs/features/tutor/room-http.md).
// Paths and bodies: specs/system/api.md "ห้องติว".

import type { ConfirmOcr, SendMessage } from "@/components/chat/types";
import type { components } from "./api";
import { postSSE } from "./sse";

/**
 * Base URL of the API. Read per call, not at module load, so `next build`
 * works without the env (same as lib/supabase.ts).
 */
export function apiUrl(path: string): string {
  const base = process.env.NEXT_PUBLIC_API_URL;
  if (!base) throw new Error("NEXT_PUBLIC_API_URL must be set");
  return `${base.replace(/\/$/, "")}${path}`;
}

/** Sends `{text}` to POST /sessions/{id}/messages and yields the SSE reply. */
export function createHttpTransport(sessionId: string): SendMessage {
  return function send(payload, signal) {
    // Images are blocked in the Composer until /uploads exists (room-http.md §2).
    const body: components["schemas"]["SendMessageRequest"] = { text: payload.text };
    return postSSE(apiUrl(`/sessions/${sessionId}/messages`), body, { signal });
  };
}

/**
 * Sends the confirmed lines to POST /sessions/{id}/ocr/confirm and yields the SSE reply.
 * Hand-written body until the API has `OcrConfirmRequest` (ocr-confirm-card.md OQ 5).
 */
export function createHttpOcrConfirm(sessionId: string): ConfirmOcr {
  return function confirm(lines, signal) {
    return postSSE(apiUrl(`/sessions/${sessionId}/ocr/confirm`), { lines }, { signal });
  };
}
