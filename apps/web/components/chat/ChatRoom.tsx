"use client";

import Link from "next/link";
import { useEffect, useLayoutEffect, useRef, useState } from "react";
import { Composer, type ComposerHandle } from "./Composer";
import { MessageList } from "./MessageList";
import type { OcrPreviewData, OcrStatus } from "./OcrConfirmCard";
import type { ProblemData } from "./ProblemCard";
import { roomStrings as t } from "./strings";
import { hasVerdictMark, type VerdictData } from "./VerdictMark";
import type { SSEEvent } from "@/lib/sse";
import type { ChatMessage, ConfirmOcr, MessageRole, RoomData, SendMessage, SendPayload } from "./types";

/** How close to the bottom (px) still counts as "following" the stream. A UI value, not a learning-model one. */
export const NEAR_BOTTOM_PX = 80;

// Without a transport the room behaves like S2: the message is shown, nobody answers.
const noReply: SendMessage & ConfirmOcr = async function* () {
  yield { event: "done", data: {} };
};

type Token = { speaker: "tutor" | "buddy"; text: string };

/**
 * Tutor room (specs: chat-room-ui.md, chat-streaming.md).
 * Sends through `sendMessage` and turns the SSE reply into bubbles.
 */
export function ChatRoom({
  room,
  sendMessage = noReply,
  confirmOcr = noReply,
  opening,
  imagesEnabled,
}: {
  room: RoomData;
  sendMessage?: SendMessage;
  /** POST /sessions/{id}/ocr/confirm (ocr-confirm-card.md). */
  confirmOcr?: ConfirmOcr;
  /** Rest of the POST /exam-preps/{id}/sessions stream: the opening message streams in with no user bubble (room-http.md §2). */
  opening?: AsyncIterable<SSEEvent>;
  imagesEnabled?: boolean;
}) {
  const [messages, setMessages] = useState<ChatMessage[]>(room.messages);
  const [busy, setBusy] = useState(false);
  const [typing, setTyping] = useState(false);
  const [streamingId, setStreamingId] = useState<string | null>(null);
  const [failed, setFailed] = useState(false);

  const nextId = useRef(0);
  const abort = useRef<AbortController | null>(null);
  const log = useRef<HTMLElement>(null);
  const stick = useRef(true);
  const composer = useRef<ComposerHandle>(null);
  const busyRef = useRef(false);

  useEffect(() => () => abort.current?.abort(), []);

  // Follow the stream only when the user is already near the bottom (chat-streaming.md §2).
  useLayoutEffect(() => {
    const el = log.current;
    if (el && stick.current) el.scrollTop = el.scrollHeight;
  }, [messages, typing]);

  function onScroll() {
    const el = log.current;
    if (el) stick.current = el.scrollHeight - el.clientHeight - el.scrollTop <= NEAR_BOTTOM_PX;
  }

  function newMessage(role: MessageRole, content: string | null, extra: Partial<ChatMessage> = {}): ChatMessage {
    return {
      id: `local-${nextId.current++}`,
      role,
      content,
      input_mode: null,
      attachment_path: null,
      created_at: new Date().toISOString(),
      ...extra,
    };
  }

  function append(message: ChatMessage) {
    setMessages((prev) => [...prev, message]);
  }

  function setOcrStatus(id: string, status: OcrStatus) {
    setMessages((prev) => prev.map((m) => (m.id === id && m.ocr ? { ...m, ocr: { ...m.ocr, status } } : m)));
  }

  function appendText(id: string, text: string) {
    setMessages((prev) => prev.map((m) => (m.id === id ? { ...m, content: (m.content ?? "") + text } : m)));
  }

  async function send(payload: SendPayload) {
    const { text, image } = payload;
    append(
      newMessage("user", text, {
        input_mode: image ? "image" : "text",
        // Not uploaded yet, so no Storage path (chat-room-ui.md AC-6c).
        attachment_name: image ? image.name : null,
      }),
    );
    stick.current = true;
    const controller = new AbortController();
    abort.current = controller;
    await play(sendMessage(payload, controller.signal), controller.signal);
  }

  /** Sends the confirmed lines; the card locks only when the check reply finishes (ocr-confirm-card.md §2). */
  async function confirm(id: string, lines: string[]) {
    if (busyRef.current) return;
    setOcrStatus(id, "sending");
    const controller = new AbortController();
    abort.current = controller;
    const done = await play(confirmOcr(lines, controller.signal), controller.signal);
    if (!controller.signal.aborted) setOcrStatus(id, done ? "confirmed" : "pending");
  }

  function retake(id: string) {
    setOcrStatus(id, "retaken");
    composer.current?.pickPhoto();
  }

  /** Shows one SSE reply as bubbles (chat-streaming.md §2). Resolves true when it ended with `done`. */
  async function play(events: AsyncIterable<SSEEvent>, signal: AbortSignal): Promise<boolean> {
    busyRef.current = true;
    setFailed(false);
    setBusy(true);
    setTyping(true);

    // The bubble that tokens of the same speaker are appended to, in this stream only.
    let current = null as { id: string; speaker: Token["speaker"] } | null;
    let done = false;
    try {
      for await (const { event, data } of events) {
        if (signal.aborted) return false;
        if (event === "token") {
          const { speaker, text } = data as Token;
          if (current?.speaker === speaker) {
            appendText(current.id, text);
          } else {
            const message = newMessage(speaker, text);
            append(message);
            current = { id: message.id, speaker };
            setStreamingId(message.id);
          }
          setTyping(false);
        } else if (event === "buddy") {
          append(newMessage("buddy", (data as { text: string }).text));
          current = null;
          setStreamingId(null);
          setTyping(false);
        } else if (event === "problem") {
          // Shown as a problem card; the tutor's next tokens start a new bubble (problem-card.md AC-6).
          append(newMessage("card", null, { problem: data as ProblemData }));
          current = null;
          setStreamingId(null);
        } else if (event === "ocr_preview") {
          // Only one card waits at a time: a newer photo replaces older unconfirmed ones (AC-20).
          const preview = data as OcrPreviewData;
          if (preview.lines.length > 0) {
            setMessages((prev) => [
              ...prev.map((m) => (m.ocr?.status === "pending" ? { ...m, ocr: { ...m.ocr, status: "retaken" as const } } : m)),
              newMessage("card", null, { ocr: { preview, status: "pending" } }),
            ]);
          }
          current = null;
          setStreamingId(null);
        } else if (event === "verdict") {
          // Shown above the tutor's words; a verdict with no mark leaves the bubble whole (verdict-mark.md AC-3, AC-4).
          const verdict = data as VerdictData;
          if (hasVerdictMark(verdict)) {
            append(newMessage("card", null, { verdict }));
            current = null;
            setStreamingId(null);
          }
        } else if (event === "progress_card") {
          // Shown as a card; the tutor's next tokens start a new bubble (progress-card.md AC-9).
          append(newMessage("card", null, { card: data as ChatMessage["card"] }));
          current = null;
          setStreamingId(null);
        } else if (event === "done") {
          done = true;
          break;
        } else if (event === "error") {
          break;
        }
        // Other events (session_end, ...) are separate features.
      }
    } catch {
      // A network failure is shown like an error event.
    }
    if (signal.aborted) return false;
    busyRef.current = false;
    setBusy(false);
    setTyping(false);
    setStreamingId(null);
    setFailed(!done);
    return done;
  }

  // The opening stream can be read only once; the ref keeps a second effect run
  // (React Strict Mode) from reading it again. Its owner aborts it on unmount.
  const openingStarted = useRef(false);
  useEffect(() => {
    if (!opening || openingStarted.current) return;
    openingStarted.current = true;
    void play(opening, new AbortController().signal);
    // eslint-disable-next-line react-hooks/exhaustive-deps -- play once per opening stream
  }, [opening]);

  return (
    <div className="flex h-screen flex-col px-8 pb-5">
      <header className="mx-auto flex w-full max-w-2xl items-center justify-between py-4 text-xs text-zinc-400">
        <span>
          <b className="font-medium text-zinc-600">{room.prep_name}</b> · <span>{t.daysLeft(room.days_left)}</span>
        </span>
        <Link href="/" className="hover:text-zinc-600">
          {t.exitRoom}
        </Link>
      </header>
      <main ref={log} role="log" onScroll={onScroll} className="-mx-8 flex-1 overflow-y-auto px-8">
        <div className="mx-auto w-full max-w-2xl pb-3">
          <MessageList
            messages={messages}
            tutorName={room.tutor_name}
            buddyName={room.buddy_name}
            userName={room.user_name}
            streamingId={streamingId}
            typing={typing}
            onOcrConfirm={confirm}
            onOcrRetake={retake}
          />
        </div>
      </main>
      <div className="bg-white pt-3">
        {failed && (
          <p role="alert" className="mx-auto mb-2 w-full max-w-2xl pl-4 text-xs text-red-700">
            {t.sendFailed}
          </p>
        )}
        <Composer
          limits={room.limits}
          onSend={send}
          disabled={busy}
          imagesEnabled={imagesEnabled}
          handle={composer}
        />
      </div>
    </div>
  );
}
