// SSE over POST. EventSource is GET-only, so we read the response body
// ourselves. Event names and payloads: specs/system/api.md "SSE events".

export type SSEEvent = {
  event: string;
  data: unknown;
};

/** Parse a byte stream of `text/event-stream` into events. */
export async function* parseSSE(
  stream: ReadableStream<Uint8Array>,
): AsyncGenerator<SSEEvent> {
  const reader = stream.getReader();
  // stream: true keeps a multi-byte char that is split across chunks intact.
  const decoder = new TextDecoder();
  let buffer = "";
  try {
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      // Normalize CRLF/CR to LF; a trailing \r waits for the next chunk
      // in case it is the first half of a \r\n.
      buffer = (buffer + decoder.decode(value, { stream: true })).replace(
        /\r\n|\r(?!$)/g,
        "\n",
      );
      let end: number;
      while ((end = buffer.indexOf("\n\n")) !== -1) {
        const event = parseBlock(buffer.slice(0, end));
        buffer = buffer.slice(end + 2);
        if (event) yield event;
      }
    }
    const tail = parseBlock((buffer + decoder.decode()).replace(/\r/g, ""));
    if (tail) yield tail;
  } finally {
    reader.releaseLock();
  }
}

function parseBlock(block: string): SSEEvent | null {
  let event = "message";
  const data: string[] = [];
  for (const line of block.split("\n")) {
    if (line === "" || line.startsWith(":")) continue;
    const colon = line.indexOf(":");
    const field = colon === -1 ? line : line.slice(0, colon);
    let value = colon === -1 ? "" : line.slice(colon + 1);
    if (value.startsWith(" ")) value = value.slice(1);
    if (field === "event") event = value;
    else if (field === "data") data.push(value);
  }
  if (data.length === 0) return null;
  const raw = data.join("\n");
  try {
    return { event, data: JSON.parse(raw) };
  } catch {
    return { event, data: raw };
  }
}

/** POST a JSON body and yield the SSE events of the response. */
export async function* postSSE(
  url: string,
  body: unknown,
  init: { headers?: HeadersInit; signal?: AbortSignal } = {},
): AsyncGenerator<SSEEvent> {
  const res = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "text/event-stream",
      ...init.headers,
    },
    body: JSON.stringify(body),
    signal: init.signal,
  });
  if (!res.ok || !res.body) {
    throw new Error(`SSE request failed: ${res.status} ${res.statusText}`);
  }
  yield* parseSSE(res.body);
}
