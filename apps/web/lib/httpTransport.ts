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

/**
 * Gets a signed URL from POST /sessions/{id}/uploads, PUTs the photo there and returns its path
 * for `image_path` (specs/features/tutor/room-photo-send.md §2). Any failure throws, so nothing
 * more is sent and the room shows its send error.
 */
async function uploadPhoto(sessionId: string, image: File, signal: AbortSignal): Promise<string> {
  const request: components["schemas"]["UploadRequest"] = {
    kind: "image",
    content_type: image.type,
    file_name: image.name,
    size_bytes: image.size,
  };
  const res = await fetch(apiUrl(`/sessions/${sessionId}/uploads`), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
    signal,
  });
  if (!res.ok) throw new Error(`upload request failed: ${res.status}`);
  const ticket: components["schemas"]["UploadTicket"] = await res.json();

  // The stub's URL cannot be used (spec OQ 2). Delete this check when /uploads talks to Storage.
  if (res.headers.get("X-Stub") !== "true") {
    const put = await fetch(ticket.upload_url, {
      method: "PUT",
      headers: { "Content-Type": image.type },
      body: image,
      signal,
    });
    if (!put.ok) throw new Error(`upload failed: ${put.status}`);
  }
  return ticket.path;
}

/** Sends the message to POST /sessions/{id}/messages, the photo first if any, and yields the SSE reply. */
export function createHttpTransport(sessionId: string): SendMessage {
  return async function* send({ text, image }, signal) {
    const body: components["schemas"]["SendMessageRequest"] = image
      ? { ...(text !== null && { text }), image_path: await uploadPhoto(sessionId, image, signal) }
      : { text };
    yield* postSSE(apiUrl(`/sessions/${sessionId}/messages`), body, { signal });
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
