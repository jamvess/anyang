// Shapes of the tutor room data (spec: specs/features/tutor/chat-room-ui.md §3).
// Message fields mirror the `messages` table. In S2 they come from a fixture,
// in S3 from GET /sessions/{id}/messages.

export type MessageRole = "user" | "tutor" | "buddy" | "card" | "system";

export type ChatMessage = {
  id: string;
  role: MessageRole;
  content: string | null;
  input_mode: "text" | "voice" | "image" | null;
  attachment_path: string | null;
  created_at: string;
};

/** Input limits from `config/ai.yaml` → `guards`, sent by the API with the room. */
export type InputLimits = {
  max_message_chars: number;
  max_image_mb: number;
};

export type RoomData = {
  prep_name: string;
  days_left: number;
  user_name: string;
  tutor_name: string;
  buddy_name: string | null;
  limits: InputLimits;
  messages: ChatMessage[];
};

export type SendPayload = { text: string | null; image: File | null };
