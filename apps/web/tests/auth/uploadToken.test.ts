import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

// Spec: specs/features/platform/web-login.md §2.3 item 4 · AC-13 (added 17 Nov). On APP_ENV=local the
// photo's upload_url is the API's own /dev/uploads, which needs the token when AUTH_REQUIRED=true;
// a Storage signed URL never gets it.

const supabase = vi.hoisted(() => ({ session: null as null | { access_token: string } }));
vi.mock("@/lib/supabase", () => ({
  createClient: () => ({ auth: { getSession: async () => ({ data: { session: supabase.session }, error: null }) } }),
}));

const API = "http://api.test";
const SESSION = "22222222-2222-4222-8222-222222222222";
const PATH = `t/sessions/${SESSION}/a.png`;

type Call = { method: string; url: string; init: RequestInit };

/** /uploads answers with `uploadUrl`; the PUT and /messages succeed. */
function mockApi(uploadUrl: string) {
  const calls: Call[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL, init: RequestInit = {}) => {
      const url = String(input);
      const method = (init.method ?? "GET").toUpperCase();
      calls.push({ method, url, init });
      if (url === `${API}/sessions/${SESSION}/uploads`) {
        return new Response(JSON.stringify({ upload_url: uploadUrl, path: PATH }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      if (method === "PUT") return new Response(null, { status: 200 });
      if (url === `${API}/sessions/${SESSION}/messages`) {
        return new Response("event: done\ndata: {}\n\n", { status: 200, headers: { "Content-Type": "text/event-stream" } });
      }
      throw new Error(`unexpected request ${method} ${url}`);
    }),
  );
  return calls;
}

const put = (calls: Call[]) => calls.find((c) => c.method === "PUT")!;
const header = (call: Call, name: string) => new Headers(call.init.headers).get(name);

async function sendPhoto() {
  const { createHttpTransport } = await import("@/lib/httpTransport");
  const send = createHttpTransport(SESSION);
  const image = new File(["x"], "คำตอบ.png", { type: "image/png" });
  for await (const _ of send({ text: null, image }, new AbortController().signal)) {
    // drain the reply
  }
}

beforeEach(() => {
  vi.stubEnv("NEXT_PUBLIC_API_URL", API);
  supabase.session = { access_token: "t-1" };
});

afterEach(() => {
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
  vi.resetModules();
});

describe("httpTransport · the token on the photo's PUT", () => {
  it("TM06 SA06 an upload URL of the API gets the session's token and the image type (AC-13)", async () => {
    const calls = mockApi(`${API}/dev/uploads/${PATH}`);

    await sendPhoto();

    const call = put(calls);
    expect(call.url).toBe(`${API}/dev/uploads/${PATH}`);
    expect(header(call, "Authorization")).toBe("Bearer t-1");
    expect(header(call, "Content-Type")).toBe("image/png");
  });

  it.each([
    ["a Storage signed URL", `https://storage.example/object/upload/sign/${PATH}?token=abc`],
    ["a URL that only starts with the API's text", `${API}.evil.example/dev/uploads/${PATH}`],
  ])("SA06 %s gets no token (AC-13)", async (_name, uploadUrl) => {
    const calls = mockApi(uploadUrl);

    await sendPhoto();

    expect(header(put(calls), "Authorization")).toBeNull();
  });

  it("SA06 without a session the API's upload URL gets no token either (AC-13)", async () => {
    supabase.session = null;
    const calls = mockApi(`${API}/dev/uploads/${PATH}`);

    await sendPhoto();

    expect(header(put(calls), "Authorization")).toBeNull();
  });
});
