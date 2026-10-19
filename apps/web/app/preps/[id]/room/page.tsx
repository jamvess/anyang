import { ChatRoom } from "@/components/chat/ChatRoom";
import type { RoomData } from "@/components/chat/types";
// S2: fixed sample data from wireframe S15–S17. S3 loads the session from the API.
import sample from "@/tests/fixtures/room/session-s15.json";

export default function RoomPage() {
  return <ChatRoom room={sample as RoomData} />;
}
