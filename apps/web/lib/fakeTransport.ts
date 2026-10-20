// Stand-in for POST /sessions/{id}/messages until the API exists
// (spec: specs/features/tutor/chat-streaming.md §2). Replays a recorded
// SSE text through parseSSE, one event block per chunk, so the room sees
// the same events the real stream would send.

import type { SendMessage } from "@/components/chat/types";
import { parseSSE } from "./sse";

type Options = {
  /** Pause between chunks so streaming is visible on screen. Tests use 0. */
  delayMs?: number;
};

function chunks(text: string): ReadableStream<Uint8Array> {
  const encoder = new TextEncoder();
  const blocks = text.split(/(?<=\n\n)/);
  let i = 0;
  return new ReadableStream({
    pull(controller) {
      if (i >= blocks.length) return controller.close();
      controller.enqueue(encoder.encode(blocks[i++]));
    },
  });
}

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

export function createFakeTransport(sseText: string, { delayMs = 0 }: Options = {}): SendMessage {
  return async function* fakeSend(_payload, signal) {
    for await (const event of parseSSE(chunks(sseText))) {
      if (signal.aborted) return;
      if (delayMs > 0) await sleep(delayMs);
      if (signal.aborted) return;
      yield event;
    }
  };
}
