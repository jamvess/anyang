import { act, cleanup, render } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

// Spec: specs/features/platform/web-signup.md §2.2, §2.3 · AC-10. The login tests of
// LoginForm.test.tsx stay as they are.

const supabase = vi.hoisted(() => ({
  auth: { signInWithPassword: vi.fn(), getSession: vi.fn() },
}));
vi.mock("@/lib/supabase", () => ({ createClient: () => supabase }));

beforeEach(() => {
  supabase.auth.getSession.mockResolvedValue({ data: { session: null }, error: null });
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe("LoginForm · link to sign up", () => {
  it.each([
    [undefined, "/signup"],
    ["/preps/new", "/signup?next=%2Fpreps%2Fnew"],
    ["https://evil.example", "/signup"],
  ])("UM01 the sign-up link with next %s is %s (AC-10)", async (next, href) => {
    const { LoginForm } = await import("@/components/auth/LoginForm");
    const utils = render(<LoginForm next={next} navigate={vi.fn()} />);
    await act(async () => {});

    expect(utils.getByText("ยังไม่มีบัญชี?", { exact: false })).toBeTruthy();
    expect(utils.getByRole("link", { name: "สมัครสมาชิก" }).getAttribute("href")).toBe(href);
  });
});
