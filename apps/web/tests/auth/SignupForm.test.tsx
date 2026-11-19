import { act, cleanup, fireEvent, render, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

// Spec: specs/features/platform/web-signup.md §2.1, §2.3 · AC-1 to AC-9. May decided §2 on 2026-11-17.
// Interfaces expected (built by /implement-feature):
// - components/auth/SignupForm.tsx: SignupForm({ next, navigate }) · next is the raw ?next= value
// - lib/supabase.ts createClient() is the only Supabase entry point (mocked here)

const supabase = vi.hoisted(() => ({
  auth: {
    signUp: vi.fn(),
    getSession: vi.fn(),
  },
}));
const broken = vi.hoisted(() => ({ client: false }));
vi.mock("@/lib/supabase", () => ({
  createClient: () => {
    if (broken.client) throw new Error("no Supabase env");
    return supabase;
  },
}));

const EMAIL = "pal@example.com";
const PASSWORD = "secret-1";
const NO_SESSION = { data: { session: null }, error: null };
const SIGNED_UP = { data: { session: { access_token: "t-1" }, user: { id: "u" } }, error: null };
const failure = (code: string) => ({
  data: { session: null, user: null },
  error: Object.assign(new Error(code), { code, status: 422 }),
});

beforeEach(() => {
  broken.client = false;
  supabase.auth.getSession.mockResolvedValue(NO_SESSION);
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

async function openForm(next?: string) {
  const { SignupForm } = await import("@/components/auth/SignupForm");
  const navigate = vi.fn();
  const utils = render(<SignupForm next={next} navigate={navigate} />);
  await act(async () => {}); // the session check on mount
  const field = (label: string) => utils.getByLabelText(label) as HTMLInputElement;
  return { ...utils, navigate, field };
}

type Form = Awaited<ReturnType<typeof openForm>>;

async function fill(utils: Form, email: string, password: string, confirm = password) {
  fireEvent.change(utils.field("อีเมล"), { target: { value: email } });
  fireEvent.change(utils.field("รหัสผ่าน"), { target: { value: password } });
  fireEvent.change(utils.field("ยืนยันรหัสผ่าน"), { target: { value: confirm } });
  await act(async () => void fireEvent.click(utils.getByRole("button", { name: "สมัครสมาชิก" })));
}

function expectKeptEmailClearedPasswords(utils: Form) {
  expect(utils.field("อีเมล").value).toBe(EMAIL);
  expect(utils.field("รหัสผ่าน").value).toBe("");
  expect(utils.field("ยืนยันรหัสผ่าน").value).toBe("");
}

describe("SignupForm", () => {
  it("UM01 signs up with the email and password, then goes home (AC-1)", async () => {
    let finish!: (value: unknown) => void;
    supabase.auth.signUp.mockReturnValue(new Promise((r) => (finish = r)));
    const utils = await openForm();

    await fill(utils, EMAIL, PASSWORD);

    expect(supabase.auth.signUp).toHaveBeenCalledTimes(1);
    expect(supabase.auth.signUp).toHaveBeenCalledWith({ email: EMAIL, password: PASSWORD });
    expect(utils.getByRole("button", { name: "กำลังสมัคร…" })).toHaveProperty("disabled", true);
    await act(async () => finish(SIGNED_UP));
    await waitFor(() => expect(utils.navigate).toHaveBeenCalledWith("/"));
  });

  it.each([
    ["/preps/new", "/preps/new"],
    ["//evil.example", "/"],
  ])("UM01 next %s goes to %s after signing up (AC-2)", async (next, expected) => {
    supabase.auth.signUp.mockResolvedValue(SIGNED_UP);
    const utils = await openForm(next);

    await fill(utils, EMAIL, PASSWORD);

    await waitFor(() => expect(utils.navigate).toHaveBeenCalledWith(expected));
  });

  it("UM01 passwords that differ are caught before Supabase (AC-3)", async () => {
    const utils = await openForm();

    await fill(utils, EMAIL, PASSWORD, "secret-2");

    expect(supabase.auth.signUp).not.toHaveBeenCalled();
    expect(utils.getByRole("alert").textContent).toContain("รหัสผ่านทั้งสองช่องไม่ตรงกัน");
    expectKeptEmailClearedPasswords(utils);
    expect(utils.navigate).not.toHaveBeenCalled();
  });

  it.each([
    ["user_already_exists", "อีเมลนี้มีบัญชีแล้ว"],
    ["email_exists", "อีเมลนี้มีบัญชีแล้ว"],
    ["weak_password", "รหัสผ่านสั้นหรือง่ายเกินไป ลองตั้งใหม่"],
    ["email_address_invalid", "อีเมลนี้ใช้สมัครไม่ได้"],
    ["signup_disabled", "ตอนนี้ปิดรับสมัครอยู่"],
    ["over_request_rate_limit", "สมัครไม่ได้ตอนนี้ ลองใหม่อีกครั้ง"],
  ])("UM01 Supabase code %s shows %s (AC-4)", async (code, message) => {
    supabase.auth.signUp.mockResolvedValue(failure(code));
    const utils = await openForm();

    await fill(utils, EMAIL, PASSWORD);

    await waitFor(() => expect(utils.getByRole("alert").textContent).toContain(message));
    expect(utils.navigate).not.toHaveBeenCalled();
    expectKeptEmailClearedPasswords(utils);
    expect(utils.getByRole("button", { name: "สมัครสมาชิก" })).toHaveProperty("disabled", false);
  });

  it("UM01 a thrown error shows the try-again message (AC-4)", async () => {
    supabase.auth.signUp.mockRejectedValue(new Error("network"));
    const utils = await openForm();

    await fill(utils, EMAIL, PASSWORD);

    await waitFor(() => expect(utils.getByRole("alert").textContent).toContain("สมัครไม่ได้ตอนนี้ ลองใหม่อีกครั้ง"));
    expectKeptEmailClearedPasswords(utils);
    expect(utils.getByRole("button", { name: "สมัครสมาชิก" })).toHaveProperty("disabled", false);
  });

  it("UM01 a taken email links to the login page (AC-5)", async () => {
    supabase.auth.signUp.mockResolvedValue(failure("user_already_exists"));
    const utils = await openForm();

    await fill(utils, EMAIL, PASSWORD);

    const alert = await waitFor(() => utils.getByRole("alert"));
    expect(within(alert).getByRole("link", { name: "เข้าสู่ระบบ" }).getAttribute("href")).toBe("/login");
  });

  it("UM01 signed up without a session asks to confirm the email (AC-6)", async () => {
    supabase.auth.signUp.mockResolvedValue({ data: { session: null, user: { id: "u" } }, error: null });
    const utils = await openForm();

    await fill(utils, EMAIL, PASSWORD);

    const status = await waitFor(() => utils.getByRole("status"));
    expect(status.textContent).toContain("สมัครแล้ว เปิดอีเมลเพื่อยืนยันก่อนเข้าสู่ระบบ");
    expect(utils.getByRole("link", { name: "เข้าสู่ระบบ" })).toBeTruthy();
    expect(utils.queryByRole("button", { name: "สมัครสมาชิก" })).toBeNull();
    expect(utils.navigate).not.toHaveBeenCalled();
  });

  it("UM01 a session on open goes to next without the form (AC-7)", async () => {
    supabase.auth.getSession.mockResolvedValue({ data: { session: { access_token: "t-1" } }, error: null });
    const utils = await openForm("/preps/new");

    await waitFor(() => expect(utils.navigate).toHaveBeenCalledWith("/preps/new"));
    expect(supabase.auth.signUp).not.toHaveBeenCalled();
  });

  it("UM01 no Supabase env still shows the form (AC-7)", async () => {
    broken.client = true;
    const utils = await openForm();

    expect(utils.getByRole("button", { name: "สมัครสมาชิก" })).toBeTruthy();
    expect(utils.navigate).not.toHaveBeenCalled();
  });

  it("NFR-A1 every field has a label and the passwords are new-password fields (AC-8)", async () => {
    const utils = await openForm();

    expect(utils.field("อีเมล").type).toBe("email");
    for (const label of ["รหัสผ่าน", "ยืนยันรหัสผ่าน"]) {
      expect(utils.field(label).type).toBe("password");
      expect(utils.field(label).getAttribute("autocomplete")).toBe("new-password");
    }
    expect(utils.getByRole("button", { name: "สมัครสมาชิก" })).toBeTruthy();
  });

  it.each([
    [undefined, "/login"],
    ["/preps/new", "/login?next=%2Fpreps%2Fnew"],
    ["//evil.example", "/login"],
  ])("UM01 the login link with next %s is %s (AC-9)", async (next, href) => {
    const utils = await openForm(next);

    expect(utils.getByRole("link", { name: "เข้าสู่ระบบ" }).getAttribute("href")).toBe(href);
  });
});
