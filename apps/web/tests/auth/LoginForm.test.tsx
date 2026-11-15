import { act, cleanup, fireEvent, render, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

// Spec: specs/features/platform/web-login.md §2.1, §2.2 · AC-1 to AC-6, AC-11.
// Interfaces expected (built by /implement-feature):
// - components/auth/LoginForm.tsx: LoginForm({ next, navigate }) · next is the raw ?next= value
// - components/auth/Logout.tsx: Logout({ navigate }) signs out on mount, then goes to /login
// - lib/supabase.ts createClient() is the only Supabase entry point (mocked here)

const supabase = vi.hoisted(() => ({
  auth: {
    signInWithPassword: vi.fn(),
    getSession: vi.fn(),
    signOut: vi.fn(),
  },
}));
vi.mock("@/lib/supabase", () => ({ createClient: () => supabase }));

const NO_SESSION = { data: { session: null }, error: null };
const SIGNED_IN = { data: { session: { access_token: "t-1" }, user: { id: "u" } }, error: null };
const WRONG = {
  data: { session: null, user: null },
  error: Object.assign(new Error("Invalid login credentials"), { code: "invalid_credentials", status: 400 }),
};

beforeEach(() => {
  supabase.auth.getSession.mockResolvedValue(NO_SESSION);
  supabase.auth.signOut.mockResolvedValue({ error: null });
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

async function openForm(next?: string) {
  const { LoginForm } = await import("@/components/auth/LoginForm");
  const navigate = vi.fn();
  const utils = render(<LoginForm next={next} navigate={navigate} />);
  await act(async () => {}); // the session check on mount
  return { ...utils, navigate };
}

function fill(utils: Awaited<ReturnType<typeof openForm>>, email: string, password: string) {
  fireEvent.change(utils.getByLabelText("อีเมล"), { target: { value: email } });
  fireEvent.change(utils.getByLabelText("รหัสผ่าน"), { target: { value: password } });
  fireEvent.click(utils.getByRole("button", { name: "เข้าสู่ระบบ" }));
}

describe("LoginForm", () => {
  it("UM01 signs in with the email and password and goes to next (AC-1)", async () => {
    let finish!: (value: unknown) => void;
    supabase.auth.signInWithPassword.mockReturnValue(new Promise((r) => (finish = r)));
    const utils = await openForm("/preps/p1/scope");

    fill(utils, "pal@example.com", "secret-1");

    expect(supabase.auth.signInWithPassword).toHaveBeenCalledWith({
      email: "pal@example.com",
      password: "secret-1",
    });
    const busy = utils.getByRole("button", { name: "กำลังเข้าสู่ระบบ…" });
    expect(busy).toHaveProperty("disabled", true);
    await act(async () => finish(SIGNED_IN));
    await waitFor(() => expect(utils.navigate).toHaveBeenCalledWith("/preps/p1/scope"));
  });

  it.each([
    [undefined, "/"],
    ["/preps/p1/room", "/preps/p1/room"],
    ["https://evil.example", "/"],
    ["//evil.example", "/"],
    ["/\\evil.example", "/"],
  ])("SA06 next %s goes to %s, only inside the site (AC-2)", async (next, expected) => {
    supabase.auth.signInWithPassword.mockResolvedValue(SIGNED_IN);
    const utils = await openForm(next);

    fill(utils, "pal@example.com", "secret-1");

    await waitFor(() => expect(utils.navigate).toHaveBeenCalledWith(expected));
  });

  it("UM01 a wrong password says so, keeps the email and clears the password (AC-3)", async () => {
    supabase.auth.signInWithPassword.mockResolvedValue(WRONG);
    const utils = await openForm();

    fill(utils, "pal@example.com", "wrong");

    const alert = await utils.findByRole("alert");
    expect(alert.textContent).toBe("อีเมลหรือรหัสผ่านไม่ถูกต้อง");
    expect(utils.navigate).not.toHaveBeenCalled();
    expect((utils.getByLabelText("อีเมล") as HTMLInputElement).value).toBe("pal@example.com");
    expect((utils.getByLabelText("รหัสผ่าน") as HTMLInputElement).value).toBe("");
    expect(utils.getByRole("button", { name: "เข้าสู่ระบบ" })).toHaveProperty("disabled", false);
  });

  it("UM01 any other failure asks to try again (AC-4)", async () => {
    supabase.auth.signInWithPassword.mockRejectedValue(new TypeError("Failed to fetch"));
    const utils = await openForm();

    fill(utils, "pal@example.com", "secret-1");

    const alert = await utils.findByRole("alert");
    expect(alert.textContent).toBe("เข้าสู่ระบบไม่ได้ตอนนี้ ลองใหม่อีกครั้ง");
  });

  it("UM01 a user who is signed in already goes to next at once (AC-5)", async () => {
    supabase.auth.getSession.mockResolvedValue(SIGNED_IN);

    const utils = await openForm("/preps/p1/room");

    await waitFor(() => expect(utils.navigate).toHaveBeenCalledWith("/preps/p1/room"));
    expect(supabase.auth.signInWithPassword).not.toHaveBeenCalled();
  });

  it("UM01 every field and the button have labels (AC-6)", async () => {
    const utils = await openForm();

    expect(utils.getByLabelText("อีเมล").getAttribute("type")).toBe("email");
    expect(utils.getByLabelText("รหัสผ่าน").getAttribute("type")).toBe("password");
    expect(utils.getByLabelText("อีเมล")).toHaveProperty("required", true);
    expect(utils.getByLabelText("รหัสผ่าน")).toHaveProperty("required", true);
    expect(utils.getByRole("button", { name: "เข้าสู่ระบบ" })).toBeTruthy();
  });
});

describe("Logout", () => {
  it.each([
    ["signs out", () => supabase.auth.signOut.mockResolvedValue({ error: null })],
    ["fails", () => supabase.auth.signOut.mockRejectedValue(new Error("down"))],
  ])("UM01 /logout goes to /login when sign-out %s (AC-11)", async (_name, arrange) => {
    arrange();
    const { Logout } = await import("@/components/auth/Logout");
    const navigate = vi.fn();

    render(<Logout navigate={navigate} />);

    await waitFor(() => expect(navigate).toHaveBeenCalledWith("/login"));
    expect(supabase.auth.signOut).toHaveBeenCalled();
  });
});
