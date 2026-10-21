"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { apiUrl, createHttpTransport } from "@/lib/httpTransport";
import { postSSE, type SSEEvent } from "@/lib/sse";
import { ChatRoom } from "./ChatRoom";
import { roomStrings as t } from "./strings";
import type { RoomData } from "./types";

type State =
  | { kind: "loading" }
  | { kind: "ready"; room: RoomData; opening?: AsyncIterable<SSEEvent> }
  | { kind: "notFound" }
  | { kind: "failed" };

/** A non-2xx answer of the API, with `error.code` when the body has one (api.md Conventions). */
class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly code: string | undefined,
  ) {
    super(`API ${status} ${code ?? ""}`);
  }
}

async function getJSON<T>(path: string, signal: AbortSignal): Promise<T> {
  const res = await fetch(apiUrl(path), { signal });
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new ApiError(res.status, body?.error?.code);
  }
  return res.json();
}

/**
 * Opens the room of an exam prep (spec: specs/features/tutor/room-http.md):
 * resume the open session, or start one and stream its opening message in.
 */
async function openRoom(prepId: string, signal: AbortSignal): Promise<Extract<State, { kind: "ready" }>> {
  try {
    const { session_id } = await getJSON<{ session_id: string }>(`/exam-preps/${prepId}/sessions/active`, signal);
    return { kind: "ready", room: await getJSON<RoomData>(`/sessions/${session_id}`, signal) };
  } catch (e) {
    if (!(e instanceof ApiError && e.status === 404 && e.code === "no_active_session")) throw e;
  }

  const stream = postSSE(apiUrl(`/exam-preps/${prepId}/sessions`), {}, { signal });
  const first = await stream.next();
  if (first.done || first.value.event !== "session") throw new Error("session stream did not start with `session`");
  const { session_id } = first.value.data as { session_id: string };
  const room = await getJSON<RoomData>(`/sessions/${session_id}`, signal);
  // The rest of the same stream (opening message, done) is played by ChatRoom.
  return { kind: "ready", room, opening: { [Symbol.asyncIterator]: () => stream } };
}

export function TutorRoom({ prepId }: { prepId: string }) {
  const [state, setState] = useState<State>({ kind: "loading" });
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    // Aborting on cleanup also cancels the opening stream when the room is left.
    const controller = new AbortController();
    openRoom(prepId, controller.signal).then(
      (ready) => !controller.signal.aborted && setState(ready),
      (e) => {
        if (controller.signal.aborted) return;
        const notFound = e instanceof ApiError && e.status === 404;
        setState({ kind: notFound ? "notFound" : "failed" });
      },
    );
    return () => controller.abort();
  }, [prepId, attempt]);

  const sessionId = state.kind === "ready" ? state.room.session_id : null;
  const sendMessage = useMemo(() => (sessionId ? createHttpTransport(sessionId) : undefined), [sessionId]);

  if (state.kind === "ready") {
    return <ChatRoom room={state.room} sendMessage={sendMessage} opening={state.opening} imagesEnabled={false} />;
  }

  return (
    <div className="flex h-screen flex-col items-center justify-center gap-3 px-8 text-sm text-zinc-600">
      {state.kind === "loading" ? (
        <p>{t.loading}</p>
      ) : (
        <>
          <p role="alert">{state.kind === "notFound" ? t.prepNotFound : t.loadFailed}</p>
          <div className="flex items-center gap-4">
            {state.kind === "failed" && (
              <button
                type="button"
                onClick={() => {
                  setState({ kind: "loading" });
                  setAttempt((n) => n + 1);
                }}
                className="rounded-full bg-zinc-900 px-4 py-1.5 text-white"
              >
                {t.retry}
              </button>
            )}
            <Link href="/" className="text-zinc-500 hover:text-zinc-700">
              {t.backHome}
            </Link>
          </div>
        </>
      )}
    </div>
  );
}
