import { cleanup, fireEvent, render, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ProgressPage } from "@/components/materials/ProgressPage";
import { loginRedirect } from "@/lib/auth";
import { API, PREP, apiError, json, mockApi, pending, polls, type Handler, type Ingestion } from "./helpers";

// Spec: specs/features/exam-prep/ingestion-retry.md §2.1 · AC-1 to AC-10 (S11 "ลองใหม่").
// Interfaces expected (built by /implement-feature):
//   components/materials/ProgressPage.tsx  a "ลองใหม่" button on a failed file, and on the first failed
//                                          step when no file failed; POST .../retry, then poll at once
// POLL_MS is long here by default, so the only quick poll after a retry is the one the click makes.

const timing = vi.hoisted(() => ({ pollMs: 60_000 }));
vi.mock("@/components/materials/poll", () => ({
  get POLL_MS() {
    return timing.pollMs;
  },
}));

const INGESTION = `GET /exam-preps/${PREP}/ingestion`;
const RETRY_FILE = "POST /materials/m1/retry";
const RETRY_STEPS = `POST /exam-preps/${PREP}/ingestion/retry`;
const TOPICS = "หาหัวข้อและลำดับการเรียน";
const EXAMS = "เทียบกับข้อสอบเก่า 2 ชุด";

type FileRow = Ingestion["files"][number];
type Step = Ingestion["steps"][number];

const scan = (status: FileRow["status"]): FileRow => ({
  material_id: "m1",
  file_name: "scan.pdf",
  status,
  detail: null,
  error: status === "failed" ? "อ่านไฟล์นี้ไม่สำเร็จ ลองใหม่ได้" : null,
});
const sheet: FileRow = { material_id: "m2", file_name: "sheet-01.pdf", status: "done", detail: "14 หน้า", error: null };
const steps = (notes: Step["status"], topics: Step["status"], exams: Step["status"]): Step[] => [
  { label: "อ่านสิ่งที่คุณเขียนกำกับไว้", status: notes },
  { label: TOPICS, status: topics },
  { label: EXAMS, status: exams },
];

const fileFailed = () =>
  json({ scope_ready: false, files: [scan("failed"), sheet], steps: steps("failed", "pending", "pending") });
const fileRunning = () =>
  json({ scope_ready: false, files: [scan("running"), sheet], steps: steps("running", "pending", "pending") });
const topicsFailed = () =>
  json({ scope_ready: false, files: [scan("done"), sheet], steps: steps("done", "failed", "pending") });
const ready = () => json({ scope_ready: true, files: [scan("done"), sheet], steps: steps("done", "done", "done") });
const accepted = () => new Response(null, { status: 202 });
const materialBack = () =>
  json(
    {
      id: "m1",
      file_name: "scan.pdf",
      kind: "sheet",
      kind_confidence: 0.9,
      kind_confirmed: true,
      user_note: null,
      status: "confirmed",
      error: null,
    },
    202,
  );

const FILE_BUTTON = "ลองอ่าน scan.pdf ใหม่";
const STEP_BUTTON = `ลองขั้น ${TOPICS} ใหม่`;
const RETRY_FAILED = "ลองใหม่ไม่สำเร็จ ลองอีกครั้งได้";

let toLogin: ReturnType<typeof vi.fn<(href: string) => void>>;

beforeEach(() => {
  timing.pollMs = 60_000;
  vi.stubEnv("NEXT_PUBLIC_API_URL", API);
  toLogin = vi.fn<(href: string) => void>();
  vi.spyOn(loginRedirect, "go").mockImplementation(toLogin);
});

afterEach(() => {
  cleanup();
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

function open(routes: Record<string, Handler | Handler[]>) {
  const api = mockApi(routes);
  const navigate = vi.fn();
  const utils = render(<ProgressPage prepId={PREP} navigate={navigate} />);
  return { ...utils, api, navigate };
}

describe("ProgressPage retry (S11 · ingestion-retry.md)", () => {
  // AC-1
  it("CM07 a failed file has a retry button named for the file, showing ลองใหม่", async () => {
    const utils = open({ [INGESTION]: fileFailed });

    const button = await utils.findByRole("button", { name: FILE_BUTTON });
    expect(button.textContent).toBe("ลองใหม่");
    expect(utils.queryByRole("button", { name: "ลองใหม่" })).toBeNull();
  });

  // AC-2
  it("CM07 retrying a file posts once with no body, polls at once, and the button goes when it runs", async () => {
    const utils = open({ [INGESTION]: [fileFailed, fileRunning], [RETRY_FILE]: materialBack });
    fireEvent.click(await utils.findByRole("button", { name: FILE_BUTTON }));

    await waitFor(() => expect(utils.api.count(INGESTION)).toBe(2)); // long before POLL_MS
    expect(utils.api.count(RETRY_FILE)).toBe(1);
    expect(utils.api.calls.find((c) => c.key === RETRY_FILE)?.init.body ?? null).toBeNull();
    expect(utils.api.keys().indexOf(RETRY_FILE)).toBeLessThan(utils.api.keys().lastIndexOf(INGESTION));
    await waitFor(() => expect(utils.queryByRole("button", { name: FILE_BUTTON })).toBeNull());
    expect(utils.getAllByLabelText("กำลังอ่าน").length).toBeGreaterThan(0);
  });

  // AC-3
  it("CM07 the button is disabled while the retry is on its way, so a second click sends nothing", async () => {
    const late = pending();
    const utils = open({ [INGESTION]: fileFailed, [RETRY_FILE]: late.handler });
    const button = await utils.findByRole("button", { name: FILE_BUTTON });

    fireEvent.click(button);
    await waitFor(() => expect((button as HTMLButtonElement).disabled).toBe(true));
    fireEvent.click(button);

    expect(utils.api.count(RETRY_FILE)).toBe(1);
    await late.release(materialBack());
  });

  // AC-4
  it("CM07 a failed step with no failed file can be retried, and the page goes on to the scope", async () => {
    const utils = open({ [INGESTION]: [topicsFailed, ready], [RETRY_STEPS]: accepted });

    fireEvent.click(await utils.findByRole("button", { name: STEP_BUTTON }));

    await waitFor(() => expect(utils.navigate).toHaveBeenCalledWith(`/preps/${PREP}/scope`));
    expect(utils.api.count(RETRY_STEPS)).toBe(1);
    expect(utils.api.calls.find((c) => c.key === RETRY_STEPS)?.init.body ?? null).toBeNull();
  });

  // AC-5
  it("CM07 while a file failed, only the file has a button, not the steps", async () => {
    const utils = open({ [INGESTION]: fileFailed });

    await utils.findByRole("button", { name: FILE_BUTTON });
    expect(utils.queryAllByRole("button", { name: /^ลองขั้น / })).toHaveLength(0);
  });

  // AC-6
  it("CM07 two failed steps get one button, on the first", async () => {
    const both = () =>
      json({ scope_ready: false, files: [scan("done"), sheet], steps: steps("done", "failed", "failed") });
    const utils = open({ [INGESTION]: both });

    await utils.findByRole("button", { name: STEP_BUTTON });
    expect(utils.getAllByRole("button", { name: /^ลองขั้น / })).toHaveLength(1);
    expect(utils.queryByRole("button", { name: `ลองขั้น ${EXAMS} ใหม่` })).toBeNull();
  });

  // AC-7
  it.each([
    ["a file", FILE_BUTTON, RETRY_FILE, fileFailed],
    ["a step", STEP_BUTTON, RETRY_STEPS, topicsFailed],
  ])("CM07 409 not_failed on %s shows no error and polls at once", async (_what, name, route, first) => {
    const utils = open({ [INGESTION]: [first, fileRunning], [route]: apiError(409, "not_failed") });

    fireEvent.click(await utils.findByRole("button", { name }));

    await waitFor(() => expect(utils.api.count(INGESTION)).toBe(2));
    expect(utils.queryByText(RETRY_FAILED)).toBeNull();
  });

  // AC-8
  it.each([
    ["503", apiError(503, "db_unavailable")],
    [
      "a network error",
      () => {
        throw new TypeError("Failed to fetch");
      },
    ],
  ])("CM07 a retry that fails with %s says so and can be pressed again, and polling goes on", async (_what, fail) => {
    timing.pollMs = 20;
    const utils = open({ [INGESTION]: fileFailed, [RETRY_FILE]: [fail, materialBack] });

    fireEvent.click(await utils.findByRole("button", { name: FILE_BUTTON }));
    expect(await utils.findByText(RETRY_FAILED)).toBeTruthy();
    const seen = utils.api.count(INGESTION);
    await polls(3);
    expect(utils.api.count(INGESTION)).toBeGreaterThan(seen);

    const button = utils.getByRole("button", { name: FILE_BUTTON }) as HTMLButtonElement;
    expect(button.disabled).toBe(false);
    fireEvent.click(button);

    await waitFor(() => expect(utils.api.count(RETRY_FILE)).toBe(2));
    await waitFor(() => expect(utils.queryByText(RETRY_FAILED)).toBeNull());
  });

  // AC-9
  it("CM07 a 401 on retry shows no retry error", async () => {
    const utils = open({ [INGESTION]: fileFailed, [RETRY_FILE]: apiError(401, "invalid_token") });

    fireEvent.click(await utils.findByRole("button", { name: FILE_BUTTON }));

    await waitFor(() => expect(toLogin).toHaveBeenCalled());
    await polls(1);
    expect(utils.queryByText(RETRY_FAILED)).toBeNull();
  });

  // AC-10
  it("CM07 a file still failed after a 202 can be retried again", async () => {
    const utils = open({ [INGESTION]: fileFailed, [RETRY_FILE]: materialBack });

    fireEvent.click(await utils.findByRole("button", { name: FILE_BUTTON }));
    await waitFor(() => expect(utils.api.count(INGESTION)).toBe(2));

    await waitFor(() =>
      expect((utils.getByRole("button", { name: FILE_BUTTON }) as HTMLButtonElement).disabled).toBe(false),
    );
    fireEvent.click(utils.getByRole("button", { name: FILE_BUTTON }));
    await waitFor(() => expect(utils.api.count(RETRY_FILE)).toBe(2));
  });
});
