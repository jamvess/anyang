import { readFileSync } from "node:fs";
import { join } from "node:path";
import type { RoomData } from "@/components/chat/types";
// S2–S3: fixed sample data from wireframe S15–S17 and a recorded reply.
// Replaced by the session API once POST /sessions/{id}/messages exists.
import sample from "@/tests/fixtures/room/session-s15.json";
import { DemoRoom } from "./DemoRoom";

// Read at build time: the page has no dynamic data, so Next prerenders it.
const replySSE = readFileSync(join(process.cwd(), "tests", "fixtures", "sse", "tutor_reply.txt"), "utf8");

export default function RoomPage() {
  return <DemoRoom room={sample as RoomData} replySSE={replySSE} />;
}
