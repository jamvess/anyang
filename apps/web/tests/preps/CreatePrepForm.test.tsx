import { act, cleanup, fireEvent, render, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { CreatePrepForm } from "@/components/preps/CreatePrepForm";

// Spec: specs/features/exam-prep/prep-list-page.md §2.2 · AC-8 to AC-11.
// Interfaces expected (built by /implement-feature): components/preps/CreatePrepForm.tsx
// CreatePrepForm({ navigate }) posts to POST /exam-preps through apiFetch.

const API = "http://api.test";

const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
const created = () =>
  json(
    {
      id: "p1",
      title: "MTH10101",
      exam_date: "2026-12-08",
      days_left: 23,
      daily_minutes: 60,
      stage: "materials",
      readiness: null,
      topics_not_passed: null,
    },
    201,
  );

type Call = { url: string; init: RequestInit };
function mockPost(respond: () => Response | Promise<Response>) {
  const calls: Call[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL, init: RequestInit = {}) => {
      calls.push({ url: String(input), init });
      return respond();
    }),
  );
  return calls;
}

function openForm() {
  const navigate = vi.fn();
  const utils = render(<CreatePrepForm navigate={navigate} />);
  return { ...utils, navigate };
}

function fill(utils: ReturnType<typeof openForm>, minutes?: string) {
  fireEvent.change(utils.getByLabelText("ชื่อการสอบ"), { target: { value: "MTH10101" } });
  fireEvent.change(utils.getByLabelText("วันสอบ"), { target: { value: "2026-12-08" } });
  if (minutes !== undefined) {
    fireEvent.change(utils.getByLabelText("เวลาต่อวัน (นาที)"), { target: { value: minutes } });
  }
  fireEvent.click(utils.getByRole("button", { name: "สร้าง" }));
}

beforeEach(() => vi.stubEnv("NEXT_PUBLIC_API_URL", API));
afterEach(() => {
  cleanup();
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
});

describe("CreatePrepForm", () => {
  it("CM01 creates the prep with what was typed, then goes home (AC-8)", async () => {
    let finish!: (r: Response) => void;
    const calls = mockPost(() => new Promise((r) => (finish = r)));
    const utils = openForm();

    fill(utils, "60");

    await waitFor(() => expect(calls).toHaveLength(1));
    expect(calls[0].url).toBe(`${API}/exam-preps`);
    expect(calls[0].init.method).toBe("POST");
    expect(new Headers(calls[0].init.headers).get("Content-Type")).toBe("application/json");
    expect(JSON.parse(String(calls[0].init.body))).toEqual({
      title: "MTH10101",
      exam_date: "2026-12-08",
      daily_minutes: 60,
    });
    expect(utils.getByRole("button", { name: "กำลังสร้าง…" })).toHaveProperty("disabled", true);
    await act(async () => finish(created()));
    await waitFor(() => expect(utils.navigate).toHaveBeenCalledWith("/"));
  });

  it("CM01 no daily minutes sends none (AC-9)", async () => {
    const calls = mockPost(created);
    const utils = openForm();

    fill(utils);

    await waitFor(() => expect(calls).toHaveLength(1));
    expect(JSON.parse(String(calls[0].init.body))).toEqual({ title: "MTH10101", exam_date: "2026-12-08" });
  });

  it.each([
    ["a past exam date", () => json({ error: { code: "exam_date_past", message: "x" } }, 422), "วันสอบต้องไม่ก่อนวันนี้"],
    [
      "an invalid body",
      () => json({ error: { code: "validation_error", message: "x" } }, 422),
      "ตรวจชื่อ วันสอบ และเวลาต่อวันอีกครั้ง",
    ],
    ["the database down", () => json({ error: { code: "db_unavailable", message: "x" } }, 503), "บันทึกไม่ได้ตอนนี้ ลองใหม่อีกครั้ง"],
  ])("CM01 %s shows a Thai message and keeps the form (AC-10)", async (_case, respond, text) => {
    mockPost(respond);
    const utils = openForm();

    fill(utils, "60");

    const alert = await utils.findByRole("alert");
    expect(alert.textContent).toBe(text);
    expect(utils.navigate).not.toHaveBeenCalled();
    expect((utils.getByLabelText("ชื่อการสอบ") as HTMLInputElement).value).toBe("MTH10101");
    expect((utils.getByLabelText("วันสอบ") as HTMLInputElement).value).toBe("2026-12-08");
    expect((utils.getByLabelText("เวลาต่อวัน (นาที)") as HTMLInputElement).value).toBe("60");
    expect(utils.getByRole("button", { name: "สร้าง" })).toHaveProperty("disabled", false);
  });

  it("CM01 a network failure is the save message too (AC-10)", async () => {
    mockPost(() => {
      throw new TypeError("Failed to fetch");
    });
    const utils = openForm();

    fill(utils);

    expect((await utils.findByRole("alert")).textContent).toBe("บันทึกไม่ได้ตอนนี้ ลองใหม่อีกครั้ง");
  });

  it("CM01 every field has a label and the browser's own limits (AC-11)", () => {
    const utils = openForm();

    expect(utils.getByLabelText("ชื่อการสอบ")).toHaveProperty("required", true);
    const date = utils.getByLabelText("วันสอบ");
    expect(date.getAttribute("type")).toBe("date");
    expect(date).toHaveProperty("required", true);
    const minutes = utils.getByLabelText("เวลาต่อวัน (นาที)");
    expect(minutes.getAttribute("type")).toBe("number");
    expect(minutes).toHaveProperty("required", false);
    expect(minutes.getAttribute("min")).toBe("1");
    expect(minutes.getAttribute("max")).toBe("1440");
    expect(utils.getByRole("link", { name: "ยกเลิก" }).getAttribute("href")).toBe("/");
  });
});


// --- added by the self-review of PR #139 -----------------------------------------------------

describe("CreatePrepForm under Next's preserved pages", () => {
  it("CM01 a page hidden after a create comes back as a fresh, usable form", async () => {
    // Next 16 with cacheComponents hides the page it leaves (React <Activity>) and keeps its state:
    // in the browser check (15 Nov) the second create stayed on "กำลังสร้าง…".
    const { Activity } = await import("react");
    mockPost(created);
    const navigate = vi.fn();
    const utils = render(
      <Activity mode="visible">
        <CreatePrepForm navigate={navigate} />
      </Activity>,
    );
    fireEvent.change(utils.getByLabelText("ชื่อการสอบ"), { target: { value: "MTH10101" } });
    fireEvent.change(utils.getByLabelText("วันสอบ"), { target: { value: "2026-12-08" } });
    fireEvent.click(utils.getByRole("button", { name: "สร้าง" }));
    await waitFor(() => expect(navigate).toHaveBeenCalledWith("/"));

    utils.rerender(
      <Activity mode="hidden">
        <CreatePrepForm navigate={navigate} />
      </Activity>,
    );
    utils.rerender(
      <Activity mode="visible">
        <CreatePrepForm navigate={navigate} />
      </Activity>,
    );

    expect(utils.getByRole("button", { name: "สร้าง" })).toHaveProperty("disabled", false);
    expect((utils.getByLabelText("ชื่อการสอบ") as HTMLInputElement).value).toBe("");
    expect((utils.getByLabelText("วันสอบ") as HTMLInputElement).value).toBe("");
  });

  it("CM01 a create that ends after the user left does not pull them back", async () => {
    const { Activity } = await import("react");
    let finish!: (r: Response) => void;
    const calls = mockPost(() => new Promise((r) => (finish = r)));
    const navigate = vi.fn();
    const utils = render(
      <Activity mode="visible">
        <CreatePrepForm navigate={navigate} />
      </Activity>,
    );
    fireEvent.change(utils.getByLabelText("ชื่อการสอบ"), { target: { value: "MTH10101" } });
    fireEvent.change(utils.getByLabelText("วันสอบ"), { target: { value: "2026-12-08" } });
    fireEvent.click(utils.getByRole("button", { name: "สร้าง" }));
    await waitFor(() => expect(calls).toHaveLength(1)); // the POST is on its way

    utils.rerender(
      <Activity mode="hidden">
        <CreatePrepForm navigate={navigate} />
      </Activity>,
    );
    await act(async () => finish(created()));

    expect(navigate).not.toHaveBeenCalled();
  });

  it("UM01 a 401 shows no error: the login page is on its way", async () => {
    mockPost(() => json({ error: { code: "invalid_token", message: "x" } }, 401));
    const utils = openForm();

    fill(utils);

    await waitFor(() => expect(utils.getByRole("button", { name: "สร้าง" })).toHaveProperty("disabled", false));
    expect(utils.queryByRole("alert")).toBeNull();
  });
});
