"use client";

import { useMemo } from "react";
import { ChatRoom } from "@/components/chat/ChatRoom";
import type { RoomData } from "@/components/chat/types";
import { createFakeTransport } from "@/lib/fakeTransport";

// Pause between replayed events so the demo visibly streams. Demo-only, not a learning-model value.
const DEMO_DELAY_MS = 120;

/** Room with the fake transport until POST /sessions/{id}/messages exists (chat-streaming.md §2). */
export function DemoRoom({ room, replySSE }: { room: RoomData; replySSE: string }) {
  const sendMessage = useMemo(() => createFakeTransport(replySSE, { delayMs: DEMO_DELAY_MS }), [replySSE]);
  return <ChatRoom room={room} sendMessage={sendMessage} />;
}
