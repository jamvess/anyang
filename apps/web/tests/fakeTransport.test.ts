import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import { createFakeTransport } from "@/lib/fakeTransport";
import type { SSEEvent } from "@/lib/sse";

const fixture = (name: string) =>
  readFileSync(join(__dirname, "fixtures", "sse", name), "utf8");

const payload = { text: "(x-7)(x+7)", image: null };

describe("lib/fakeTransport", () => {
  it("TM20 replays the events of an SSE fixture in order, ending with done", async () => {
    const send = createFakeTransport(fixture("tutor_reply.txt"), { delayMs: 0 });

    const events: SSEEvent[] = [];
    for await (const e of send(payload, new AbortController().signal)) events.push(e);

    expect(events.map((e) => e.event)).toEqual([
      "token",
      "token",
      "token",
      "token",
      "token",
      "token",
      "token",
      "done",
    ]);
    expect(events[0].data).toEqual({ speaker: "tutor", text: "ถูกแล้ว " });
    expect(events[3].data).toMatchObject({ speaker: "buddy" });
  });

  it("TM20 stops yielding once the signal is aborted", async () => {
    const send = createFakeTransport(fixture("tutor_reply.txt"), { delayMs: 0 });
    const controller = new AbortController();

    const events: SSEEvent[] = [];
    for await (const e of send(payload, controller.signal)) {
      events.push(e);
      controller.abort();
    }

    expect(events).toHaveLength(1);
  });
});
