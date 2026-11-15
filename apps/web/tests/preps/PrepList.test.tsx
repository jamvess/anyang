import { cleanup, fireEvent, render, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { components } from "@/lib/api";
import { PrepList } from "@/components/preps/PrepList";

// Spec: specs/features/exam-prep/prep-list-page.md §2.1 · AC-1 to AC-7.
// Interfaces expected (built by /implement-feature): components/preps/PrepList.tsx PrepList()
// reads GET /exam-preps through apiFetch; texts in components/preps/strings.ts.

type ExamPrep = components["schemas"]["ExamPrep"];

const API = "http://api.test";

const prep = (id: string, overrides: Partial<ExamPrep> = {}): ExamPrep => ({
  id,
  title: `prep ${id}`,
  exam_date: "2026-12-08",
  days_left: 12,
  daily_minutes: null,
  stage: "materials",
  readiness: null,
  topics_not_passed: null,
  ...overrides,
});

const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });

function mockList(...responses: Array<() => Response>) {
  const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
    expect(String(input)).toBe(`${API}/exam-preps`);
    const next = responses.shift();
    if (!next) throw new Error("no more responses for GET /exam-preps");
    return next();
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

async function open(...responses: Array<() => Response>) {
  const fetchMock = mockList(...responses);
  const utils = render(<PrepList />);
  await waitFor(() => expect(utils.queryByText("กำลังโหลด…")).toBeNull());
  return { ...utils, fetchMock };
}

const cards = (el: HTMLElement) => [...el.querySelectorAll<HTMLElement>("[data-prep-id]")];

beforeEach(() => vi.stubEnv("NEXT_PUBLIC_API_URL", API));
afterEach(() => {
  cleanup();
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
});

describe("PrepList", () => {
  it("CM01 one card per prep, in the API's order, with its stage in Thai (AC-1)", async () => {
    const utils = await open(() =>
      json([
        prep("a", { stage: "tutoring" }),
        prep("b", { stage: "scope" }),
        prep("c", { stage: "processing" }),
        prep("d", { stage: "materials" }),
      ]),
    );

    const shown = cards(utils.container);
    expect(shown.map((c) => c.dataset.prepId)).toEqual(["a", "b", "c", "d"]);
    expect(shown.map((c) => c.textContent)).toEqual([
      expect.stringContaining("prep a"),
      expect.stringContaining("prep b"),
      expect.stringContaining("prep c"),
      expect.stringContaining("prep d"),
    ]);
    expect(shown[0].textContent).toContain("พร้อมติว");
    expect(shown[1].textContent).toContain("รอตรวจขอบเขต");
    expect(shown[2].textContent).toContain("กำลังอ่านไฟล์");
    expect(shown[3].textContent).toContain("รออัปโหลดไฟล์");
  });

  it.each([
    [12, "อีก 12 วัน"],
    [0, "สอบวันนี้"],
    [-3, "สอบผ่านไปแล้ว"],
  ])("CM02 days_left %i reads %s (AC-2)", async (days, text) => {
    const utils = await open(() => json([prep("a", { days_left: days })]));

    expect(cards(utils.container)[0].textContent).toContain(text);
  });

  it("CM01 a prep at scope or tutoring links to its page, the others do not (AC-3)", async () => {
    const utils = await open(() =>
      json([
        prep("a", { stage: "scope" }),
        prep("b", { stage: "tutoring" }),
        prep("c", { stage: "materials" }),
        prep("d", { stage: "processing" }),
      ]),
    );

    const href = (id: string) =>
      utils.container.querySelector(`[data-prep-id="${id}"]`)?.closest("a")?.getAttribute("href") ??
      utils.container.querySelector(`[data-prep-id="${id}"] a`)?.getAttribute("href") ??
      null;
    expect(href("a")).toBe("/preps/a/scope");
    expect(href("b")).toBe("/preps/b/room");
    expect(href("c")).toBeNull();
    expect(href("d")).toBeNull();
  });

  it("PM04 readiness and topics not passed show only when the API gives them (AC-4)", async () => {
    const utils = await open(() =>
      json([prep("a", { readiness: 0.416, topics_not_passed: 5 }), prep("b")]),
    );

    const [a, b] = cards(utils.container);
    expect(a.textContent).toContain("ความพร้อม 42%");
    expect(a.textContent).toContain("ยังไม่ผ่าน 5 หัวข้อ");
    expect(b.textContent).not.toContain("ความพร้อม");
    expect(b.textContent).not.toContain("ยังไม่ผ่าน");
  });

  it("CM01 no prep invites the user to create one (AC-5)", async () => {
    const utils = await open(() => json([]));

    expect(utils.getByText("ยังไม่มีการเตรียมสอบ")).toBeTruthy();
    expect(utils.getByRole("link", { name: "สร้างการเตรียมสอบ" }).getAttribute("href")).toBe("/preps/new");
    expect(cards(utils.container)).toEqual([]);
  });

  it("CM01 a list that cannot be read can be read again (AC-6)", async () => {
    const utils = await open(
      () => json({ error: { code: "db_unavailable", message: "x" } }, 503),
      () => json([prep("a")]),
    );

    expect(utils.getByText("โหลดรายการไม่สำเร็จ")).toBeTruthy();
    fireEvent.click(utils.getByRole("button", { name: "ลองอีกครั้ง" }));

    await waitFor(() => expect(cards(utils.container)).toHaveLength(1));
    expect(utils.fetchMock).toHaveBeenCalledTimes(2);
  });

  it("UM01 there is a link to sign out (AC-7)", async () => {
    const utils = await open(() => json([prep("a")]));

    expect(utils.getByRole("link", { name: "ออกจากระบบ" }).getAttribute("href")).toBe("/logout");
    expect(utils.getByRole("link", { name: "สร้างการเตรียมสอบ" }).getAttribute("href")).toBe("/preps/new");
  });
});
