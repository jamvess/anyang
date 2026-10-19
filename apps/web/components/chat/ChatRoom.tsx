"use client";

import Link from "next/link";
import { useState } from "react";
import { Composer } from "./Composer";
import { MessageList } from "./MessageList";
import { roomStrings as t } from "./strings";
import type { ChatMessage, RoomData, SendPayload } from "./types";

/**
 * Tutor room (spec: specs/features/tutor/chat-room-ui.md).
 * S2: sent messages are only appended locally. S3 replaces `send` with
 * POST /sessions/{id}/messages and appends the streamed tutor reply.
 */
export function ChatRoom({ room }: { room: RoomData }) {
  const [messages, setMessages] = useState<ChatMessage[]>(room.messages);

  function send({ text, image }: SendPayload) {
    setMessages((prev) => [
      ...prev,
      {
        id: `local-${prev.length}`,
        role: "user",
        content: text,
        input_mode: image ? "image" : "text",
        attachment_path: image ? image.name : null,
        created_at: new Date().toISOString(),
      },
    ]);
  }

  return (
    <div className="flex min-h-screen flex-col px-8 pb-5">
      <header className="mx-auto flex w-full max-w-2xl items-center justify-between py-4 text-xs text-zinc-400">
        <span>
          <b className="font-medium text-zinc-600">{room.prep_name}</b> · <span>{t.daysLeft(room.days_left)}</span>
        </span>
        <Link href="/" className="hover:text-zinc-600">
          {t.exitRoom}
        </Link>
      </header>
      <main className="mx-auto w-full max-w-2xl flex-1">
        <MessageList
          messages={messages}
          tutorName={room.tutor_name}
          buddyName={room.buddy_name}
          userName={room.user_name}
        />
      </main>
      <div className="sticky bottom-0 bg-white pt-3">
        <Composer limits={room.limits} onSend={send} />
      </div>
    </div>
  );
}
