import { cleanup, fireEvent, render, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { UploadPage } from "@/components/materials/UploadPage";
import { loginRedirect } from "@/lib/auth";
import {
  API,
  PREP,
  apiError,
  file,
  json,
  material,
  mockApi,
  pending,
  polls,
  type Handler,
} from "./helpers";

// Spec: specs/features/exam-prep/upload-page.md §2.1 · AC-1 to AC-16 (S09 + S10 short).
// Interfaces expected (built by /implement-feature):
//   components/materials/UploadPage.tsx  UploadPage({ prepId, navigate })
//   components/materials/poll.ts         POLL_MS (replaced here by a short one)
//   each chosen file is a row with [data-file-row]
// Every request goes to a mocked fetch.

vi.mock("@/components/materials/poll", () => ({ POLL_MS: 20 }));
vi.mock("@/lib/supabase", () => ({
  createClient: () => ({
    auth: {
      getSession: async () => ({ data: { session: { access_token: "t-7" } }, error: null }),
      signOut: async () => ({ error: null }),
    },
  }),
}));

const LIST = `GET /exam-preps/${PREP}/materials`;
const CREATE = `POST /exam-preps/${PREP}/materials`;
const CONFIRM = `POST /exam-preps/${PREP}/materials/confirm`;
const uploaded = (id: string) => `POST /materials/${id}/uploaded`;
const storage = (id: string) => `https://storage.test/${id}`;
const put = (id: string) => `PUT ${storage(id)}`;

const ticket =
  (id: string, stub = false): Handler =>
  () =>
    json({ material_id: id, upload_url: storage(id), path: `t/${PREP}/${id}` }, 200, stub ? { "X-Stub": "true" } : {});
const ok = () => new Response(null, { status: 200 });
const accepted = (id: string) => () => json(material(id), 202);

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

async function open(routes: Record<string, Handler | Handler[]>) {
  const api = mockApi({ [LIST]: () => json([]), ...routes });
  const navigate = vi.fn();
  const utils = render(<UploadPage prepId={PREP} navigate={navigate} />);
  await waitFor(() => expect(api.count(LIST)).toBeGreaterThan(0));
  return { ...utils, api, navigate };
}

const picker = (el: HTMLElement) => within(el).getByLabelText("เลือกไฟล์") as HTMLInputElement;
const choose = (el: HTMLElement, ...files: File[]) => fireEvent.change(picker(el), { target: { files } });
const rows = (el: HTMLElement) => [...el.querySelectorAll<HTMLElement>("[data-file-row]")];
const send = (el: HTMLElement) => fireEvent.click(within(el).getByRole("button", { name: "ส่งทั้งหมดให้ AI อ่าน" }));

describe("UploadPage · choosing files (S09)", () => {
  // AC-1
  it("CM03 an empty prep starts with a multi-file picker and nothing to send", async () => {
    const { container, findByText, getByRole } = await open({});

    expect(await findByText("ใส่สิ่งที่จะใช้สอบ")).toBeTruthy();
    const input = picker(container);
    expect(input.type).toBe("file");
    expect(input.multiple).toBe(true);
    for (const type of [".pdf", ".pptx", ".docx", "image/*"]) expect(input.accept).toContain(type);
    expect(getByRole("button", { name: "ส่งทั้งหมดให้ AI อ่าน" })).toHaveProperty("disabled", true);
  });

  // AC-2
  it("CM03 files chosen in two rounds are listed in order with their size, and one can be removed", async () => {
    const { container, findByText, getAllByRole } = await open({});
    await findByText("ใส่สิ่งที่จะใช้สอบ");

    choose(container, file("sheet-01.pdf", 2_400_000, "application/pdf"), file("โน้ต.jpg", 900_000, "image/jpeg"));
    choose(container, file("midterm.pdf", 1_000, "application/pdf"));

    expect(rows(container).map((r) => r.textContent)).toEqual([
      expect.stringContaining("sheet-01.pdf"),
      expect.stringContaining("โน้ต.jpg"),
      expect.stringContaining("midterm.pdf"),
    ]);
    expect(rows(container)[0].textContent).toContain("2.3 MB");
    expect(rows(container)[1].textContent).toContain("879 KB");

    fireEvent.click(getAllByRole("button", { name: "เอาออก" })[0]);

    expect(rows(container).map((r) => r.textContent)).toEqual([
      expect.stringContaining("โน้ต.jpg"),
      expect.stringContaining("midterm.pdf"),
    ]);
  });

  // AC-boundary (sizes)
  it.each([
    [1_048_575, "1024 KB"],
    [1_048_576, "1.0 MB"],
  ])("CM03 a file of %i bytes shows %s", async (size, text) => {
    const { container, findByText } = await open({});
    await findByText("ใส่สิ่งที่จะใช้สอบ");

    choose(container, file("a.pdf", size, "application/pdf"));

    expect(rows(container)[0].textContent).toContain(text);
  });
});

describe("UploadPage · sending (S09)", () => {
  // AC-3
  it("CM03 sends one file after the other: ticket, PUT to the signed URL, uploaded", async () => {
    const first = pending();
    const a = file("sheet-01.pdf", 2_400_000, "application/pdf");
    const b = file("โน้ต.jpg", 900_000, "image/jpeg");
    const utils = await open({
      [CREATE]: [first.handler, ticket("m2")],
      [put("m1")]: ok,
      [put("m2")]: ok,
      [uploaded("m1")]: accepted("m1"),
      [uploaded("m2")]: accepted("m2"),
      [LIST]: [() => json([]), () => json([material("m1"), material("m2")])],
    });
    await utils.findByText("ใส่สิ่งที่จะใช้สอบ");
    choose(utils.container, a, b);

    send(utils.container);

    await waitFor(() => expect(utils.api.count(CREATE)).toBe(1));
    expect(utils.getByRole("button", { name: "ส่งทั้งหมดให้ AI อ่าน" })).toHaveProperty("disabled", true);
    expect(rows(utils.container)[0].textContent).toContain("กำลังอัปโหลด…");
    await first.release(ticket("m1")() as Response);

    await waitFor(() => expect(utils.api.count(uploaded("m2"))).toBe(1));
    expect(utils.api.keys().filter((k) => k !== LIST)).toEqual([
      CREATE,
      put("m1"),
      uploaded("m1"),
      CREATE,
      put("m2"),
      uploaded("m2"),
    ]);
    const creates = utils.api.calls.filter((c) => c.key === CREATE);
    expect(JSON.parse(String(creates[0].init.body))).toEqual({
      file_name: "sheet-01.pdf",
      content_type: "application/pdf",
      size_bytes: 2_400_000,
    });
    expect(new Headers(creates[0].init.headers).get("Authorization")).toBe("Bearer t-7");
    const putA = utils.api.calls.find((c) => c.key === put("m1"))!;
    expect(putA.init.body).toBe(a);
    expect(new Headers(putA.init.headers).get("Content-Type")).toBe("application/pdf");
    expect(new Headers(putA.init.headers).get("Authorization")).toBeNull();
    const done = utils.api.calls.find((c) => c.key === uploaded("m1"))!;
    expect(JSON.parse(String(done.init.body))).toEqual({});
  });

  // AC-4
  it("CM03 a stub ticket (X-Stub) skips the PUT and still reports the upload", async () => {
    const utils = await open({
      [CREATE]: ticket("m1", true),
      [uploaded("m1")]: accepted("m1"),
      [LIST]: [() => json([]), () => json([material("m1")])],
    });
    await utils.findByText("ใส่สิ่งที่จะใช้สอบ");
    choose(utils.container, file("sheet-01.pdf", 2_400_000, "application/pdf"));

    send(utils.container);

    await waitFor(() => expect(utils.api.count(uploaded("m1"))).toBe(1));
    expect(utils.api.count(put("m1"))).toBe(0);
  });

  // AC-5
  it("CM03 a file without a type is sent as application/octet-stream", async () => {
    const utils = await open({
      [CREATE]: ticket("m1", true),
      [uploaded("m1")]: accepted("m1"),
      [LIST]: [() => json([]), () => json([material("m1")])],
    });
    await utils.findByText("ใส่สิ่งที่จะใช้สอบ");
    choose(utils.container, file("scan.heic", 500_000, ""));

    send(utils.container);

    await waitFor(() => expect(utils.api.count(CREATE)).toBe(1));
    const body = JSON.parse(String(utils.api.calls.find((c) => c.key === CREATE)!.init.body));
    expect(body.content_type).toBe("application/octet-stream");
  });

  // AC-6
  it("CM03 refused files say why, the others go on, and the messages stay on the next step", async () => {
    const utils = await open({
      [CREATE]: [apiError(422, "unsupported_type"), apiError(422, "file_too_large"), ticket("m3")],
      [put("m3")]: ok,
      [uploaded("m3")]: accepted("m3"),
      [LIST]: [() => json([]), () => json([material("m3")])],
    });
    await utils.findByText("ใส่สิ่งที่จะใช้สอบ");
    choose(
      utils.container,
      file("a.zip", 1_000, "application/zip"),
      file("huge.pdf", 90_000_000, "application/pdf"),
      file("sheet.pdf", 1_000, "application/pdf"),
    );

    send(utils.container);

    expect(await utils.findByText("AI เดาไว้แบบนี้")).toBeTruthy();
    expect(utils.api.count(CREATE)).toBe(3);
    expect(utils.api.keys().filter((k) => k.startsWith("PUT"))).toEqual([put("m3")]);
    expect(utils.getByText("ไฟล์ชนิดนี้ยังไม่รองรับ")).toBeTruthy();
    expect(utils.getByText("ไฟล์ใหญ่เกินไป")).toBeTruthy();
  });

  // AC-7
  it.each([
    ["the storage refusing", () => new Response(null, { status: 403 })],
    [
      "the network failing",
      () => {
        throw new TypeError("Failed to fetch");
      },
    ],
  ])("CM03 a PUT failing (%s) says the upload failed and reports nothing", async (_case, putResponse) => {
    const utils = await open({ [CREATE]: ticket("m1"), [put("m1")]: putResponse });
    await utils.findByText("ใส่สิ่งที่จะใช้สอบ");
    choose(utils.container, file("sheet.pdf", 1_000, "application/pdf"));

    send(utils.container);

    expect(await utils.findByText("อัปโหลดไม่สำเร็จ")).toBeTruthy();
    expect(utils.api.count(uploaded("m1"))).toBe(0);
  });

  // AC-8
  it("CM03 when every file fails the page stays, and a second send retries what did not go", async () => {
    const utils = await open({
      [CREATE]: [apiError(422, "unsupported_type"), apiError(422, "unsupported_type"), ticket("m2", true)],
      [uploaded("m2")]: accepted("m2"),
      [LIST]: [() => json([]), () => json([material("m2")])],
    });
    await utils.findByText("ใส่สิ่งที่จะใช้สอบ");
    choose(utils.container, file("a.zip", 1_000, "application/zip"));
    send(utils.container);
    expect(await utils.findByText("ไฟล์ชนิดนี้ยังไม่รองรับ")).toBeTruthy();
    expect(utils.getByText("ใส่สิ่งที่จะใช้สอบ")).toBeTruthy();
    expect(utils.getByRole("button", { name: "เอาออก" })).toHaveProperty("disabled", false);

    choose(utils.container, file("sheet.pdf", 1_000, "application/pdf"));
    send(utils.container);

    await waitFor(() => expect(utils.api.count(CREATE)).toBe(3));
    const names = utils.api.calls.filter((c) => c.key === CREATE).map((c) => JSON.parse(String(c.init.body)).file_name);
    expect(names).toEqual(["a.zip", "a.zip", "sheet.pdf"]);
  });

  // AC-9
  it("UM01 a 401 stops the sending and shows no error", async () => {
    const utils = await open({ [CREATE]: apiError(401, "invalid_token") });
    await utils.findByText("ใส่สิ่งที่จะใช้สอบ");
    choose(utils.container, file("a.pdf", 1_000, "application/pdf"), file("b.pdf", 1_000, "application/pdf"));

    send(utils.container);

    await waitFor(() => expect(toLogin).toHaveBeenCalled());
    await polls(2);
    expect(utils.api.count(CREATE)).toBe(1);
    expect(utils.queryByText("อัปโหลดไม่สำเร็จ")).toBeNull();
  });
});

describe("UploadPage · the kinds AI guessed (S10 short)", () => {
  // AC-10
  it("CM06 polls until AI has looked at the file, then shows its kind and confidence and stops", async () => {
    const utils = await open({
      [CREATE]: ticket("m1", true),
      [uploaded("m1")]: accepted("m1"),
      [LIST]: [
        () => json([]),
        () => json([material("m1", { file_name: "midterm-2566.pdf" })]),
        () =>
          json([
            material("m1", {
              file_name: "midterm-2566.pdf",
              status: "classified",
              kind: "past_exam",
              kind_confidence: 0.934,
            }),
          ]),
      ],
    });
    await utils.findByText("ใส่สิ่งที่จะใช้สอบ");
    choose(utils.container, file("midterm-2566.pdf", 1_000, "application/pdf"));
    send(utils.container);

    expect(await utils.findByText("AI กำลังดูไฟล์…")).toBeTruthy();
    expect(utils.getByRole("button", { name: "ยืนยันแล้วเริ่มประมวลผล" })).toHaveProperty("disabled", true);

    expect(await utils.findByText("ข้อสอบเก่า")).toBeTruthy();
    expect(utils.getByText("มั่นใจ 93%")).toBeTruthy();
    expect(utils.getByRole("button", { name: "ยืนยันแล้วเริ่มประมวลผล" })).toHaveProperty("disabled", false);
    const seen = utils.api.count(LIST);
    await polls(3);
    expect(utils.api.count(LIST)).toBe(seen);
  });

  // AC-11 + AC-boundary (confidence)
  it.each([
    ["sheet", 0.5, "ชีทเรียน", "มั่นใจ 50%"],
    ["slides", 0, "สไลด์", "มั่นใจ 0%"],
    ["past_exam", 1, "ข้อสอบเก่า", "มั่นใจ 100%"],
    ["notes", 0.935, "โน้ต", "มั่นใจ 94%"],
    ["other", 0.934, "อื่นๆ", "มั่นใจ 93%"],
  ] as const)("CM06 kind %s at %f shows %s · %s", async (kind, confidence, label, sure) => {
    const utils = await open({
      [LIST]: () => json([material("m1", { status: "classified", kind, kind_confidence: confidence })]),
    });

    expect(await utils.findByText(label)).toBeTruthy();
    expect(utils.getByText(sure)).toBeTruthy();
  });

  it("CM06 no confidence shows no confidence", async () => {
    const utils = await open({
      [LIST]: () => json([material("m1", { status: "classified", kind: "sheet", kind_confidence: null })]),
    });

    expect(await utils.findByText("ชีทเรียน")).toBeTruthy();
    expect(utils.queryByText(/มั่นใจ/)).toBeNull();
  });

  // AC-12 + AC-15
  it("CM06 confirms the AI's kinds of the classified files and goes to the reading page", async () => {
    const utils = await open({
      [LIST]: () =>
        json([
          material("m1", { file_name: "sheet.pdf", status: "classified", kind: "sheet", kind_confidence: 0.8 }),
          material("m2", { file_name: "broken.pdf", status: "failed", error: "เปิดไฟล์นี้ไม่ได้" }),
          material("m3", { file_name: "old.pdf", status: "ready", kind: "sheet", kind_confirmed: true }),
        ]),
      [CONFIRM]: () => json({ queued: 1 }, 202),
    });
    expect(await utils.findByText("AI เดาไว้แบบนี้")).toBeTruthy();
    expect(utils.getByText("เปิดไฟล์นี้ไม่ได้")).toBeTruthy();
    expect(utils.queryByText("old.pdf")).toBeNull();

    fireEvent.click(utils.getByRole("button", { name: "ยืนยันแล้วเริ่มประมวลผล" }));

    await waitFor(() => expect(utils.navigate).toHaveBeenCalledWith(`/preps/${PREP}/progress`));
    const confirms = utils.api.calls.filter((c) => c.key === CONFIRM);
    expect(confirms).toHaveLength(1);
    expect(JSON.parse(String(confirms[0].init.body))).toEqual({ materials: [{ id: "m1", kind: "sheet" }] });
  });

  // AC-13
  it("CM06 a file not classified yet at confirm reloads the list, with no error", async () => {
    const classified = () => json([material("m1", { status: "classified", kind: "sheet", kind_confidence: 0.8 })]);
    const utils = await open({ [LIST]: classified, [CONFIRM]: apiError(409, "not_classified") });
    await utils.findByText("ชีทเรียน");
    const before = utils.api.count(LIST);

    fireEvent.click(utils.getByRole("button", { name: "ยืนยันแล้วเริ่มประมวลผล" }));

    await waitFor(() => expect(utils.api.count(LIST)).toBeGreaterThan(before));
    expect(utils.queryByText("เริ่มอ่านไฟล์ไม่สำเร็จ ลองอีกครั้งนะ")).toBeNull();
    expect(utils.navigate).not.toHaveBeenCalled();
  });

  it("CM06 a failed confirm says so and can be pressed again", async () => {
    const utils = await open({
      [LIST]: () => json([material("m1", { status: "classified", kind: "sheet", kind_confidence: 0.8 })]),
      [CONFIRM]: apiError(503, "db_unavailable"),
    });
    await utils.findByText("ชีทเรียน");

    fireEvent.click(utils.getByRole("button", { name: "ยืนยันแล้วเริ่มประมวลผล" }));

    expect(await utils.findByText("เริ่มอ่านไฟล์ไม่สำเร็จ ลองอีกครั้งนะ")).toBeTruthy();
    expect(utils.getByRole("button", { name: "ยืนยันแล้วเริ่มประมวลผล" })).toHaveProperty("disabled", false);
  });

  it("UM01 a 401 at confirm shows no error", async () => {
    const utils = await open({
      [LIST]: () => json([material("m1", { status: "classified", kind: "sheet", kind_confidence: 0.8 })]),
      [CONFIRM]: apiError(401, "invalid_token"),
    });
    await utils.findByText("ชีทเรียน");

    fireEvent.click(utils.getByRole("button", { name: "ยืนยันแล้วเริ่มประมวลผล" }));

    await waitFor(() => expect(toLogin).toHaveBeenCalled());
    await polls(1);
    expect(utils.queryByText("เริ่มอ่านไฟล์ไม่สำเร็จ ลองอีกครั้งนะ")).toBeNull();
    expect(utils.navigate).not.toHaveBeenCalled();
  });

  // AC-14
  it("CM06 when no file could be read the user can start over with new files", async () => {
    const utils = await open({
      [LIST]: () => json([material("m1", { status: "failed", error: "เปิดไฟล์นี้ไม่ได้" })]),
    });

    expect(await utils.findByText("ไม่มีไฟล์ที่อ่านได้")).toBeTruthy();
    fireEvent.click(utils.getByRole("button", { name: "ใส่ไฟล์ใหม่" }));

    expect(utils.getByText("ใส่สิ่งที่จะใช้สอบ")).toBeTruthy();
    expect(rows(utils.container)).toHaveLength(0);
  });
});

describe("UploadPage · opening", () => {
  // AC-15
  it("CM07 a prep whose files are all confirmed starts at choosing files", async () => {
    const utils = await open({
      [LIST]: () => json([material("m1", { status: "ready", kind: "sheet", kind_confirmed: true })]),
    });

    expect(await utils.findByText("ใส่สิ่งที่จะใช้สอบ")).toBeTruthy();
  });

  // AC-16
  it("CM07 a prep that does not exist says so, with a way home", async () => {
    const utils = await open({ [LIST]: apiError(404, "not_found") });

    expect(await utils.findByText("ไม่พบการเตรียมสอบนี้")).toBeTruthy();
    expect(utils.getByRole("link", { name: "กลับหน้าหลัก" }).getAttribute("href")).toBe("/");
  });

  it("CM07 a list that cannot be read can be read again", async () => {
    const utils = await open({ [LIST]: [apiError(503, "db_unavailable"), () => json([])] });

    expect(await utils.findByText("โหลดไฟล์ไม่สำเร็จ")).toBeTruthy();
    fireEvent.click(utils.getByRole("button", { name: "ลองใหม่" }));

    expect(await utils.findByText("ใส่สิ่งที่จะใช้สอบ")).toBeTruthy();
  });

  it("UM01 a 401 on opening shows no error", async () => {
    const utils = await open({ [LIST]: apiError(401, "invalid_token") });

    await waitFor(() => expect(toLogin).toHaveBeenCalled());
    await polls(1);
    expect(utils.queryByText("โหลดไฟล์ไม่สำเร็จ")).toBeNull();
  });
});


// --- added by the self-review of PR #142 -----------------------------------------------------

describe("UploadPage after a send and under Next's preserved pages", () => {
  it("CM06 right after a send, before the list arrives, nothing says no file could be read", async () => {
    const list = pending();
    const utils = await open({
      [CREATE]: ticket("m1", true),
      [uploaded("m1")]: accepted("m1"),
      [LIST]: [() => json([]), list.handler],
    });
    await utils.findByText("ใส่สิ่งที่จะใช้สอบ");
    choose(utils.container, file("sheet.pdf", 1_000, "application/pdf"));

    send(utils.container);

    expect(await utils.findByText("AI เดาไว้แบบนี้")).toBeTruthy();
    expect(utils.queryByText("ไม่มีไฟล์ที่อ่านได้")).toBeNull();
    expect(utils.queryByRole("button", { name: "ใส่ไฟล์ใหม่" })).toBeNull();
    expect(utils.getByRole("button", { name: "ยืนยันแล้วเริ่มประมวลผล" })).toHaveProperty("disabled", true);
    await list.release(json([material("m1")]));
    expect(await utils.findByText("AI กำลังดูไฟล์…")).toBeTruthy();
  });

  it("CM07 a page shown again after a confirm starts at choosing files", async () => {
    const { Activity } = await import("react");
    const api = mockApi({
      [LIST]: [
        () => json([material("m1", { status: "classified", kind: "sheet", kind_confidence: 0.8 })]),
        () => json([material("m1", { status: "confirmed", kind: "sheet", kind_confirmed: true })]),
      ],
      [CONFIRM]: () => json({ queued: 1 }, 202),
    });
    const navigate = vi.fn();
    const page = (mode: "visible" | "hidden") => (
      <Activity mode={mode}>
        <UploadPage prepId={PREP} navigate={navigate} />
      </Activity>
    );
    const utils = render(page("visible"));
    fireEvent.click(await utils.findByRole("button", { name: "ยืนยันแล้วเริ่มประมวลผล" }));
    await waitFor(() => expect(navigate).toHaveBeenCalledWith(`/preps/${PREP}/progress`));

    utils.rerender(page("hidden"));
    utils.rerender(page("visible"));

    expect(await utils.findByText("ใส่สิ่งที่จะใช้สอบ")).toBeTruthy();
    expect(utils.queryByText("ไม่มีไฟล์ที่อ่านได้")).toBeNull();
    expect(api.count(LIST)).toBe(2);
  });
});
