// Shapes of the tutor room data come from the API schema (apps/web/CLAUDE.md:
// no hand-written request types · room-http.md §2). Regenerate with `pnpm gen:api`.

import type { components } from "@/lib/api";
import type { SSEEvent } from "@/lib/sse";

type Schemas = components["schemas"];

/**
 * A message of the room (`GET /sessions/{id}` → `messages`). `card` is optional
 * because messages built in the browser while streaming have none.
 */
export type ChatMessage = Omit<Schemas["Message"], "card"> & { card?: Schemas["Message"]["card"] };

export type MessageRole = ChatMessage["role"];

/** Input limits from `config/ai.yaml` → `guards`, sent by the API with the room. */
export type InputLimits = Schemas["Limits"];

/** Response of `GET /sessions/{id}`; its messages typed like the room's own. */
export type RoomData = Omit<Schemas["Room"], "messages"> & { messages: ChatMessage[] };

export type SendPayload = { text: string | null; image: File | null };

/**
 * Sends one message and yields the SSE events of the reply
 * (spec: specs/features/tutor/chat-streaming.md §2).
 */
export type SendMessage = (payload: SendPayload, signal: AbortSignal) => AsyncIterable<SSEEvent>;
