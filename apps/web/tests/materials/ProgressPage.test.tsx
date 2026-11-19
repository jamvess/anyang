import { Activity } from "react";
import { cleanup, fireEvent, render, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ProgressPage } from "@/components/materials/ProgressPage";
import { loginRedirect } from "@/lib/auth";
import { API, PREP, apiError, json, mockApi, pending, polls, type Handler, type Ingestion } from "./helpers";

// Spec: specs/features/exam-prep/upload-page.md §2.2, §2.3 · AC-17 to AC-23 (S11).
// Interfaces expected (built by /implement-feature):
//   components/materials/ProgressPage.tsx  ProgressPage({ prepId, navigate })
//   components/materials/poll.ts           POLL_MS (replaced here by a short one)
// Every request goes to a mocked fetch.

vi.mock("@/components/materials/poll", () => ({ POLL_MS: 20 }));

const INGESTION = `GET /exam-preps/${PREP}/ingestion`;

const ingestion = (overrides: Partial<Ingestion> = {}): Ingestion => ({
  scope_ready: false,
  files: [
    { material_id: "m1", file_name: "sheet-01.pdf", status: "done", detail: "14 หน้า", error: null },
    { material_id: "m2", file_name: "midterm-2567.pdf", status: "running", detail: "กำลังแยกรายข้อ", error: null },
  ],
  steps: [
    { label: "อ่านสิ่งที่คุณเขียนกำกับไว้", status: "done" },
    { label: "หาหัวข้อและลำดับการเรียน", status: "running" },
    { label: "เทียบกับข้อสอบเก่า 2 ชุด", status: "pending" },
  ],
  ...overrides,
});
const reading = () => json(ingestion());
const ready = () => json(ingestion({ scope_ready: true }));

let toLogin: ReturnType<typeof vi.fn<(href: string) => void>>;

beforeEach(() => {
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

function open(route: Handler | Handler[]) {
  const api = mockApi({ [INGESTION]: route });
  const navigate = vi.fn();
  const utils = render(<ProgressPage prepId={PREP} navigate={navigate} />);
  return { ...utils, api, navigate };
}

describe("ProgressPage (S11)", () => {
  // AC-17
  it("CM07 shows each file with its status and detail, and the steps in the API's order", async () => {
    const utils = open(reading);

    expect(await utils.findByText("กำลังอ่านไฟล์ของคุณ")).toBeTruthy();
    expect(await utils.findByText("sheet-01.pdf")).toBeTruthy();
    expect(utils.getByText("14 หน้า")).toBeTruthy();
    expect(utils.getByText("midterm-2567.pdf")).toBeTruthy();
    expect(utils.getByText("กำลังแยกรายข้อ")).toBeTruthy();
    expect(utils.getAllByLabelText("เสร็จแล้ว")).toHaveLength(2); // a file and a step
    expect(utils.getAllByLabelText("กำลังอ่าน")).toHaveLength(2);
    expect(utils.getAllByLabelText("รอ")).toHaveLength(1);
    const text = utils.container.textContent ?? "";
    const order = ["อ่านสิ่งที่คุณเขียนกำกับไว้", "หาหัวข้อและลำดับการเรียน", "เทียบกับข้อสอบเก่า 2 ชุด"].map((l) =>
      text.indexOf(l),
    );
    expect(order.every((at) => at >= 0)).toBe(true);
    expect([...order].sort((a, b) => a - b)).toEqual(order);
  });

  // AC-18
  it("CM07 goes to the scope page once the scope is ready, then stops polling", async () => {
    const utils = open([reading, ready]);

    await waitFor(() => expect(utils.navigate).toHaveBeenCalledWith(`/preps/${PREP}/scope`));
    const seen = utils.api.count(INGESTION);
    await polls(3);
    expect(utils.navigate).toHaveBeenCalledTimes(1);
    expect(utils.api.count(INGESTION)).toBe(seen);
  });

  // AC-19
  it("CM07 a file that could not be read shows the API's message and no retry button", async () => {
    const utils = open(() =>
      json(
        ingestion({
          files: [
            {
              material_id: "m1",
              file_name: "scan.pdf",
              status: "failed",
              detail: null,
              error: "อ่านไฟล์นี้ไม่สำเร็จ ลองใหม่ได้",
            },
          ],
        }),
      ),
    );

    expect(await utils.findByText("อ่านไฟล์นี้ไม่สำเร็จ ลองใหม่ได้")).toBeTruthy();
    expect(utils.getAllByLabelText("ไม่สำเร็จ").length).toBeGreaterThan(0);
    expect(utils.queryByRole("button", { name: "ลองใหม่" })).toBeNull();
  });

  // AC-20
  it("CM07 nothing sent to read says so, links to the upload page and stops polling", async () => {
    const utils = open(() => json(ingestion({ files: [], steps: [] })));

    expect(await utils.findByText("ยังไม่มีไฟล์ที่ส่งให้อ่าน")).toBeTruthy();
    expect(utils.getByRole("link", { name: "ใส่ไฟล์" }).getAttribute("href")).toBe(`/preps/${PREP}/upload`);
    const seen = utils.api.count(INGESTION);
    await polls(3);
    expect(utils.api.count(INGESTION)).toBe(seen);
  });

  // AC-21
  it("CM07 a failed poll keeps the last result, stops, and can go on", async () => {
    const utils = open([reading, apiError(503, "db_unavailable"), ready]);

    expect(await utils.findByText("โหลดความคืบหน้าไม่สำเร็จ")).toBeTruthy();
    expect(utils.getByText("sheet-01.pdf")).toBeTruthy();
    const seen = utils.api.count(INGESTION);
    await polls(3);
    expect(utils.api.count(INGESTION)).toBe(seen);

    fireEvent.click(utils.getByRole("button", { name: "ลองใหม่" }));

    await waitFor(() => expect(utils.navigate).toHaveBeenCalledWith(`/preps/${PREP}/scope`));
  });

  it("CM07 a prep that does not exist says so, with a way home", async () => {
    const utils = open(apiError(404, "not_found"));

    expect(await utils.findByText("ไม่พบการเตรียมสอบนี้")).toBeTruthy();
    expect(utils.getByRole("link", { name: "กลับหน้าหลัก" }).getAttribute("href")).toBe("/");
  });

  it("UM01 a 401 shows no error", async () => {
    const utils = open(apiError(401, "invalid_token"));

    await waitFor(() => expect(toLogin).toHaveBeenCalled());
    await polls(1);
    expect(utils.queryByText("โหลดความคืบหน้าไม่สำเร็จ")).toBeNull();
  });
});

describe("ProgressPage under Next's preserved pages", () => {
  // Next 16 with cacheComponents hides the page it leaves (React <Activity>) and keeps its state.
  function openIn(route: Handler | Handler[]) {
    const api = mockApi({ [INGESTION]: route });
    const navigate = vi.fn();
    const page = (mode: "visible" | "hidden") => (
      <Activity mode={mode}>
        <ProgressPage prepId={PREP} navigate={navigate} />
      </Activity>
    );
    const utils = render(page("visible"));
    return { ...utils, api, navigate, hide: () => utils.rerender(page("hidden")), show: () => utils.rerender(page("visible")) };
  }

  // AC-22
  it("CM07 a hidden page does not poll, and asks at once when shown again", async () => {
    const utils = openIn(reading);
    await utils.findByText("sheet-01.pdf");

    utils.hide();
    const hidden = utils.api.count(INGESTION);
    await polls(3);
    expect(utils.api.count(INGESTION)).toBe(hidden);

    utils.show();

    // Not toBe(hidden + 1): the page polls every 20 ms here, faster than waitFor checks (Jam ok 16 Nov).
    await waitFor(() => expect(utils.api.count(INGESTION)).toBeGreaterThan(hidden));
  });

  // AC-23
  it("CM07 a ready scope that arrives after the page was hidden does not move the user", async () => {
    const late = pending();
    const utils = openIn([reading, late.handler]);
    await utils.findByText("sheet-01.pdf");
    await waitFor(() => expect(utils.api.count(INGESTION)).toBe(2)); // the second poll is on its way

    utils.hide();
    await late.release(ready());
    await polls(1);

    expect(utils.navigate).not.toHaveBeenCalled();
  });
});
