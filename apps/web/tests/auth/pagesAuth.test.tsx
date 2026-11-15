import { cleanup, fireEvent, render, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { TutorRoom } from "@/components/chat/TutorRoom";
import { ScopeReview } from "@/components/scope/ScopeReview";
import roomFixture from "../fixtures/room/session-s15.json";
import scopeFixture from "../fixtures/scope/scope-s12.json";

// Spec: specs/features/platform/web-login.md §2.3 items 2-3 · AC-10: the scope page and the
// tutor room send the session's token on every API request.

vi.mock("@/lib/supabase", () => ({
  createClient: () => ({
    auth: { getSession: async () => ({ data: { session: { access_token: "t-9" } }, error: null }) },
  }),
}));

const API = "http://api.test";
const PREP = "11111111-1111-4111-8111-111111111111";
const SESSION = "22222222-2222-4222-8222-222222222222";

const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });

type Call = { key: string; init: RequestInit };
function mockApi(routes: Record<string, () => Response>) {
  const calls: Call[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL, init: RequestInit = {}) => {
      const key = `${(init.method ?? "GET").toUpperCase()} ${String(input).replace(API, "")}`;
      calls.push({ key, init });
      const route = routes[key];
      if (!route) throw new Error(`unexpected request ${key}`);
      return route();
    }),
  );
  return calls;
}
const authOf = (call: Call) => new Headers(call.init.headers).get("Authorization");

beforeEach(() => vi.stubEnv("NEXT_PUBLIC_API_URL", API));
afterEach(() => {
  cleanup();
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
});

describe("the pages send the token", () => {
  it("SA06 the scope page reads and confirms with the token (AC-10)", async () => {
    const calls = mockApi({
      [`GET /exam-preps/${PREP}/scope`]: () => json(scopeFixture),
      [`POST /exam-preps/${PREP}/scope/confirm`]: () => json({ scope_version_id: SESSION, version: 1 }),
    });
    const navigate = vi.fn();
    const utils = render(<ScopeReview prepId={PREP} navigate={navigate} />);

    fireEvent.click(await utils.findByRole("button", { name: "ยืนยันขอบเขตนี้" }));

    await waitFor(() => expect(navigate).toHaveBeenCalled());
    expect(calls.map((c) => [c.key, authOf(c)])).toEqual([
      [`GET /exam-preps/${PREP}/scope`, "Bearer t-9"],
      [`POST /exam-preps/${PREP}/scope/confirm`, "Bearer t-9"],
    ]);
  });

  it("SA06 the tutor room opens with the token (AC-10)", async () => {
    const calls = mockApi({
      [`GET /exam-preps/${PREP}/sessions/active`]: () => json({ session_id: SESSION }),
      [`GET /sessions/${SESSION}`]: () =>
        json({ ...roomFixture, session_id: SESSION, messages: roomFixture.messages.slice(1, 2) }),
    });

    render(<TutorRoom prepId={PREP} />);

    await waitFor(() => expect(calls).toHaveLength(2));
    expect(calls.map(authOf)).toEqual(["Bearer t-9", "Bearer t-9"]);
  });
});
