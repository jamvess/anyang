import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

// Spec: specs/features/platform/web-login.md §2.3 · AC-7 to AC-10.
// Interfaces expected (built by /implement-feature), in lib/auth.ts:
// - authHeaders(): Promise<Record<string, string>> · {} with no session or no Supabase env
// - apiFetch(path, init?) = fetch(apiUrl(path)) with authHeaders(); a 401 goes to /login?next=
// - apiSSE(path, body, { signal }) = postSSE to the API with authHeaders(); a 401 goes to /login
// - loginRedirect.go(href): how the browser leaves for /login (replaced in tests)

const supabase = vi.hoisted(() => ({
  session: null as null | { access_token: string },
  broken: false,
}));
vi.mock("@/lib/supabase", () => ({
  createClient: () => {
    if (supabase.broken) throw new Error("NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY must be set");
    return { auth: { getSession: async () => ({ data: { session: supabase.session }, error: null }) } };
  },
}));

const API = "http://api.test";
const sse = (text: string, status = 200) =>
  new Response(text, { status, headers: { "Content-Type": "text/event-stream" } });

type Call = { url: string; init: RequestInit };
function mockFetch(respond: (url: string) => Response) {
  const calls: Call[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL, init: RequestInit = {}) => {
      calls.push({ url: String(input), init });
      return respond(String(input));
    }),
  );
  return calls;
}
const authOf = (call: Call) => new Headers(call.init.headers).get("Authorization");

beforeEach(() => {
  vi.stubEnv("NEXT_PUBLIC_API_URL", API);
  supabase.session = { access_token: "t-1" };
  supabase.broken = false;
  window.history.pushState({}, "", "/");
});

afterEach(() => {
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
  vi.resetModules();
});

async function auth() {
  const mod = await import("@/lib/auth");
  mod.loginRedirect.go = vi.fn();
  return mod;
}

describe("lib/auth", () => {
  it("SA06 apiFetch sends the session's token to the API and keeps the caller's headers (AC-7)", async () => {
    const calls = mockFetch(() => new Response("[]"));
    const { apiFetch } = await auth();

    await apiFetch("/exam-preps", { method: "POST", headers: { "Content-Type": "application/json" } });

    expect(calls[0].url).toBe(`${API}/exam-preps`);
    expect(calls[0].init.method).toBe("POST");
    expect(authOf(calls[0])).toBe("Bearer t-1");
    expect(new Headers(calls[0].init.headers).get("Content-Type")).toBe("application/json");
  });

  it("SA06 no session sends no Authorization (AC-7)", async () => {
    supabase.session = null;
    const calls = mockFetch(() => new Response("[]"));
    const { apiFetch, authHeaders } = await auth();

    await apiFetch("/exam-preps");

    expect(authOf(calls[0])).toBeNull();
    expect(await authHeaders()).toEqual({});
  });

  it("api.md Auth: no Supabase env (dev, tests) gives no headers and the API is still called (AC-8)", async () => {
    supabase.broken = true;
    const calls = mockFetch(() => new Response("[]"));
    const { apiFetch, authHeaders } = await auth();

    expect(await authHeaders()).toEqual({});
    const res = await apiFetch("/exam-preps");

    expect(res.status).toBe(200);
    expect(authOf(calls[0])).toBeNull();
  });

  it("UM01 a 401 goes to the login page with this page as next, and returns the response (AC-9)", async () => {
    window.history.pushState({}, "", "/preps/p1/scope?tab=2");
    mockFetch(() => new Response(JSON.stringify({ error: { code: "invalid_token" } }), { status: 401 }));
    const { apiFetch, loginRedirect } = await auth();

    const res = await apiFetch("/exam-preps/p1/scope");

    expect(res.status).toBe(401);
    expect(loginRedirect.go).toHaveBeenCalledWith(`/login?next=${encodeURIComponent("/preps/p1/scope?tab=2")}`);
  });

  it("SA06 apiSSE sends the token and yields the events (AC-10)", async () => {
    const calls = mockFetch(() => sse('event: done\ndata: {}\n\n'));
    const { apiSSE } = await auth();

    const events = [];
    for await (const e of apiSSE("/sessions/s1/messages", { text: "hi" })) events.push(e.event);

    expect(calls[0].url).toBe(`${API}/sessions/s1/messages`);
    expect(authOf(calls[0])).toBe("Bearer t-1");
    expect(new Headers(calls[0].init.headers).get("Accept")).toBe("text/event-stream");
    expect(events).toEqual(["done"]);
  });

  it("UM01 a 401 on a stream goes to the login page and the stream fails (AC-9)", async () => {
    window.history.pushState({}, "", "/preps/p1/room");
    mockFetch(() => sse("", 401));
    const { apiSSE, loginRedirect } = await auth();

    const stream = apiSSE("/exam-preps/p1/sessions", {});

    await expect(stream.next()).rejects.toThrow();
    expect(loginRedirect.go).toHaveBeenCalledWith(`/login?next=${encodeURIComponent("/preps/p1/room")}`);
  });
});

describe("the API calls of the pages carry the token (AC-10)", () => {
  it("SA06 the room transport: messages, the upload ticket and the handwriting confirm, but not the PUT to Storage", async () => {
    const calls = mockFetch((url) => {
      if (url.endsWith("/uploads")) {
        return new Response(JSON.stringify({ upload_url: "https://storage.test/put", path: "t/s/p.jpg" }), {
          headers: { "Content-Type": "application/json" },
        });
      }
      if (url.startsWith("https://storage.test")) return new Response(null, { status: 200 });
      return sse('event: done\ndata: {}\n\n');
    });
    await auth();
    const { createHttpOcrConfirm, createHttpTransport } = await import("@/lib/httpTransport");

    const drain = async (events: AsyncIterable<unknown>) => {
      for await (const event of events) void event;
    };
    const signal = new AbortController().signal;
    await drain(createHttpTransport("s1")({ text: "x^2", image: null }, signal));
    const photo = new File(["jpeg"], "a.jpg", { type: "image/jpeg" });
    await drain(createHttpTransport("s1")({ text: null, image: photo }, signal));
    await drain(createHttpOcrConfirm("s1")(["x"], signal));

    const byUrl = (part: string) => calls.filter((c) => c.url.includes(part));
    expect(byUrl("/sessions/s1/messages").map(authOf)).toEqual(["Bearer t-1", "Bearer t-1"]);
    expect(byUrl("/sessions/s1/uploads").map(authOf)).toEqual(["Bearer t-1"]);
    expect(byUrl("/sessions/s1/ocr/confirm").map(authOf)).toEqual(["Bearer t-1"]);
    expect(byUrl("storage.test").map(authOf)).toEqual([null]);
  });
});


// --- added by the self-review of PR #138 -----------------------------------------------------

describe("lib/auth after the self-review", () => {
  it.each(["/\t/evil.example", "/\n/evil.example", "/\r/evil.example", "/%00"])(
    "SA06 a next with a control character %j stays on the site",
    async (next) => {
      const { safeNext } = await import("@/lib/auth");

      expect(safeNext(next)).toBe(next === "/%00" ? "/%00" : "/");
    },
  );

  it("UM01 a 401 drops the session of this browser before the login page, so it does not loop", async () => {
    const signOut = vi.fn(async () => ({ error: null }));
    vi.doMock("@/lib/supabase", () => ({
      createClient: () => ({
        auth: {
          getSession: async () => ({ data: { session: { access_token: "t-old" } }, error: null }),
          signOut,
        },
      }),
    }));
    mockFetch(() => new Response("{}", { status: 401 }));
    const { apiFetch, loginRedirect } = await auth();

    await apiFetch("/exam-preps");

    expect(signOut).toHaveBeenCalledWith({ scope: "local" });
    expect(loginRedirect.go).toHaveBeenCalled();
    vi.doUnmock("@/lib/supabase");
  });
});
