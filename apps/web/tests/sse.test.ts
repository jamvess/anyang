import { readFileSync } from "node:fs";
import { join } from "node:path";
import { afterEach, describe, expect, it, vi } from "vitest";
import { postSSE, type SSEEvent } from "@/lib/sse";

const fixture = (name: string) =>
  readFileSync(join(__dirname, "fixtures", "sse", name), "utf8");

/** Stream `text` in small chunks so events and multi-byte Thai chars split. */
function chunked(text: string, size = 7): ReadableStream<Uint8Array> {
  const bytes = new TextEncoder().encode(text);
  let i = 0;
  return new ReadableStream({
    pull(controller) {
      if (i >= bytes.length) return controller.close();
      controller.enqueue(bytes.slice(i, (i += size)));
    },
  });
}

afterEach(() => vi.unstubAllGlobals());

describe("lib/sse", () => {
  it("api.md SSE: POSTs JSON and yields events in order until done", async () => {
    const fetchMock = vi.fn(
      async () => new Response(chunked(fixture("session_start.txt"))),
    );
    vi.stubGlobal("fetch", fetchMock);

    const events: SSEEvent[] = [];
    for await (const e of postSSE("/exam-preps/x/sessions", { a: 1 })) {
      events.push(e);
    }

    expect(fetchMock).toHaveBeenCalledWith(
      "/exam-preps/x/sessions",
      expect.objectContaining({ method: "POST", body: '{"a":1}' }),
    );
    expect(events.map((e) => e.event)).toEqual([
      "progress_card",
      "token",
      "problem",
      "done",
    ]);
    expect(events[1].data).toEqual({ speaker: "tutor", text: "สวัสดี" });
    expect(events[2].data).toMatchObject({ text_latex: "\\int_0^1 x\\,dx" });
  });
});
