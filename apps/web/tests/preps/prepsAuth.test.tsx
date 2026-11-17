import { cleanup, fireEvent, render, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { CreatePrepForm } from "@/components/preps/CreatePrepForm";
import { PrepList } from "@/components/preps/PrepList";

// Spec: specs/features/exam-prep/prep-list-page.md · AC-12: the list and the form send the
// session's token (through apiFetch · web-login.md §2.3).

vi.mock("@/lib/supabase", () => ({
  createClient: () => ({
    auth: { getSession: async () => ({ data: { session: { access_token: "t-7" } }, error: null }) },
  }),
}));

const API = "http://api.test";

type Call = { url: string; init: RequestInit };
function mockFetch(body: unknown, status = 200) {
  const calls: Call[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL, init: RequestInit = {}) => {
      calls.push({ url: String(input), init });
      return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
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

describe("the prep pages send the token (AC-12)", () => {
  it("SA06 the list reads with the token", async () => {
    const calls = mockFetch([]);

    render(<PrepList />);

    await waitFor(() => expect(calls).toHaveLength(1));
    expect(authOf(calls[0])).toBe("Bearer t-7");
  });

  it("SA06 the form creates with the token", async () => {
    const calls = mockFetch({}, 201);
    const utils = render(<CreatePrepForm navigate={vi.fn()} />);

    fireEvent.change(utils.getByLabelText("ชื่อการสอบ"), { target: { value: "MTH10101" } });
    fireEvent.change(utils.getByLabelText("วันสอบ"), { target: { value: "2026-12-08" } });
    fireEvent.click(utils.getByRole("button", { name: "สร้าง" }));

    await waitFor(() => expect(calls).toHaveLength(1));
    expect(authOf(calls[0])).toBe("Bearer t-7");
  });
});
