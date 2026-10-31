import { act, cleanup, fireEvent, render, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ScopeReview } from "@/components/scope/ScopeReview";
import scopeFixture from "../fixtures/scope/scope-s12.json";
import sourcesFixture from "../fixtures/scope/sources-t3.json";

// Spec: specs/features/scope/scope-review.md · fixtures from wireframe S12 and S38 · every request goes to a mocked fetch.
const API = "http://api.test";
const PREP = "11111111-1111-4111-8111-111111111111";
const SCOPE_PATH = `/exam-preps/${PREP}/scope`;
const CONFIRM_PATH = `/exam-preps/${PREP}/scope/confirm`;
const sourcesPath = (topic: string) => `/topics/${topic}/sources`;

type Topic = (typeof scopeFixture.topics)[number];
const scope = (overrides: Record<string, unknown> = {}) => ({ ...scopeFixture, ...overrides });
const withTopics = (topics: Partial<Topic>[]) => scope({ topics });

const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });

type Handler = () => Response | Promise<Response>;

/** fetch mock routed by "METHOD path"; a route may be a list used one response per call. */
function mockApi(routes: Record<string, Handler | Handler[]>) {
  const calls: string[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL, init: RequestInit = {}) => {
      const key = `${(init.method ?? "GET").toUpperCase()} ${String(input).replace(API, "")}`;
      calls.push(key);
      const route = routes[key];
      if (!route) throw new Error(`unexpected request ${key}`);
      const handler = Array.isArray(route) ? route.shift() : route;
      if (!handler) throw new Error(`no more responses for ${key}`);
      return handler();
    }),
  );
  return { count: (key: string) => calls.filter((c) => c === key).length };
}

/** A response the test releases by hand. */
function pending() {
  let release!: (r: Response) => void;
  const promise = new Promise<Response>((r) => (release = r));
  return { handler: () => promise, release: (r: Response) => act(async () => release(r)) };
}

async function open(routes: Record<string, Handler | Handler[]> = {}) {
  const api = mockApi({ [`GET ${SCOPE_PATH}`]: () => json(scopeFixture), ...routes });
  const navigate = vi.fn();
  const utils = render(<ScopeReview prepId={PREP} navigate={navigate} />);
  await waitFor(() => expect(utils.queryByText("กำลังโหลดขอบเขต…")).toBeNull());
  return { ...utils, api, navigate };
}

/** Topic rows (the toggle buttons) in screen order. */
const rows = (el: HTMLElement) => [...el.querySelectorAll<HTMLElement>("[data-topic-id]")];
const row = (el: HTMLElement, id: string) => el.querySelector<HTMLElement>(`[data-topic-id="${id}"]`)!;
const filledStars = (r: HTMLElement) => r.querySelectorAll("[data-star-on]").length;
const texSources = (el: HTMLElement) =>
  [...el.querySelectorAll('.tex annotation[encoding="application/x-tex"]')].map((a) => a.textContent);

beforeEach(() => {
  vi.stubEnv("NEXT_PUBLIC_API_URL", API);
});

afterEach(() => {
  cleanup();
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
});

describe("ScopeReview list", () => {
  // header
  it("SM02 shows the title and the prep line from the API", async () => {
    const { getByText } = await open();

    expect(getByText("ตรวจขอบเขตก่อนเริ่ม")).toBeTruthy();
    expect(getByText("Factorization · สอบใน 5 วัน · AI เรียงลำดับให้แล้ว")).toBeTruthy();
  });

  // AC-1
  it("SM02 lists the topics in the API order with the API's numbers", async () => {
    const { container } = await open();

    expect(rows(container).map((r) => r.querySelector("[data-topic-name]")?.textContent)).toEqual([
      "1 · คูณพหุนาม",
      "2 · ดึงตัวประกอบร่วม",
      "3 · ผลต่างกำลังสอง",
      "5 · แยก x²+bx+c",
      "7 · การจัดกลุ่ม",
      "9 · กำลังสาม",
    ]);
  });

  // AC-2
  it("SM03 fills stars from the API with a star label", async () => {
    const { container } = await open();

    expect(rows(container).map(filledStars)).toEqual([2, 3, 3, 3, 2, 1]);
    expect(row(container, "t3").querySelector('[aria-label="3 ดาว"]')).toBeTruthy();
  });

  // AC-3
  it.each([[4], [null]])("SM03 stars %s shows no filled star and a dash label", async (stars) => {
    const { container } = await open({
      [`GET ${SCOPE_PATH}`]: () => json(withTopics([{ ...scopeFixture.topics[0], stars } as Partial<Topic>])),
    });

    const r = row(container, "t1");
    expect(filledStars(r)).toBe(0);
    expect(r.querySelector('[aria-label="—"]')).toBeTruthy();
  });

  // AC-3b
  it("SM03 a zero-star topic moves to the end, faded, tagged ตัดออก, and still opens", async () => {
    const topics = scopeFixture.topics.map((t) => (t.id === "t5" ? { ...t, stars: 0 } : t));
    const { container } = await open({
      [`GET ${SCOPE_PATH}`]: () => json(withTopics(topics)),
      [`GET ${sourcesPath("t5")}`]: () => json(sourcesFixture),
    });

    expect(rows(container).map((r) => r.getAttribute("data-topic-id"))).toEqual(["t1", "t2", "t3", "t7", "t9", "t5"]);
    const cut = row(container, "t5");
    expect(cut.textContent).toContain("ตัดออก");
    expect(filledStars(cut)).toBe(0);
    expect(cut.querySelector('[aria-label="0 ดาว"]')).toBeTruthy();
    expect(row(container, "t3").textContent).not.toContain("ตัดออก");

    await act(async () => void fireEvent.click(cut));
    expect(cut.getAttribute("aria-expanded")).toBe("true");
  });

  // AC-4
  it("SM04 each row shows the source label and the reason from the API", async () => {
    const { container } = await open();

    expect(row(container, "t3").textContent).toContain("ch3 น.5–6 · ออกทุกชุด");
    expect(row(container, "t9").textContent).toContain("ch3 น.14 เชิงอรรถ · ไม่เคยออก");
  });

  // AC-5
  it("SM03 a user-added topic is tagged นอกเอกสาร and document topics are not", async () => {
    const topics = [...scopeFixture.topics, { ...scopeFixture.topics[0], id: "u1", order: 10, name: "สมการกำลังสอง", origin: "user" }];
    const { container } = await open({ [`GET ${SCOPE_PATH}`]: () => json(withTopics(topics)) });

    expect(row(container, "u1").textContent).toContain("นอกเอกสาร");
    expect(row(container, "t1").textContent).not.toContain("นอกเอกสาร");
  });

  // AC-6
  it("SM03 the page shows the API's stars even when the reason disagrees", async () => {
    const topics = [{ ...scopeFixture.topics[1], stars: 1, reason: "ออกทุกชุด" }];
    const { container } = await open({ [`GET ${SCOPE_PATH}`]: () => json(withTopics(topics)) });

    expect(filledStars(row(container, "t2"))).toBe(1);
  });
});

describe("ScopeReview topic detail (S38)", () => {
  // AC-7
  it("SM04 opening a topic loads its sheet text and past exam questions once", async () => {
    const { container, api } = await open({ [`GET ${sourcesPath("t3")}`]: () => json(sourcesFixture) });
    const r = row(container, "t3");
    expect(r.getAttribute("aria-expanded")).toBe("false");

    await act(async () => void fireEvent.click(r));
    const detail = await waitFor(() => {
      const el = container.querySelector<HTMLElement>('[data-topic-detail="t3"]');
      expect(el?.textContent).toContain("จากชีท · ch3-factorization.pdf หน้า 5");
      return el!;
    });

    expect(r.getAttribute("aria-expanded")).toBe("true");
    expect(api.count(`GET ${sourcesPath("t3")}`)).toBe(1);
    expect(detail.textContent).toContain("ใช้เมื่อพจน์ทั้งสองเป็นกำลังสองสมบูรณ์");
    expect(detail.textContent).toContain("ข้อสอบเก่าในหัวข้อนี้ · 3 ข้อ");
    for (const label of ["midterm-2566 ข้อ 3", "midterm-2566 ข้อ 7", "midterm-2567 ข้อ 5"]) {
      expect(detail.textContent).toContain(label);
    }
  });

  // AC-8
  it("SM04 a question with map_note shows an AI line and one without does not", async () => {
    const { container } = await open({ [`GET ${sourcesPath("t3")}`]: () => json(sourcesFixture) });

    await act(async () => void fireEvent.click(row(container, "t3")));
    const detail = await waitFor(() => container.querySelector<HTMLElement>('[data-topic-detail="t3"] [data-question-id]')!);
    const q = (id: string) => container.querySelector<HTMLElement>(`[data-topic-detail="t3"] [data-question-id="${id}"]`)!;

    expect(detail).toBeTruthy();
    expect(q("q7").textContent).toContain("AI: ใช้ผลต่างกำลังสองสองรอบ");
    expect(q("q3").textContent).not.toContain("AI:");
  });

  // AC-9
  it("SM04 sheet text is shown as text, never as HTML", async () => {
    const sources = { ...sourcesFixture, excerpts: [{ material_name: "x.pdf", page: 1, text: "<b>ตัวหนา</b><script>alert(1)</script>" }] };
    const { container } = await open({ [`GET ${sourcesPath("t3")}`]: () => json(sources) });

    await act(async () => void fireEvent.click(row(container, "t3")));
    const detail = await waitFor(() => {
      const el = container.querySelector<HTMLElement>('[data-topic-detail="t3"]');
      expect(el?.textContent).toContain("<b>ตัวหนา</b>");
      return el!;
    });

    expect(detail.querySelector("b, script")).toBeNull();
  });

  // AC-10
  it("SM04 clicking again folds the topic and reopening does not fetch again", async () => {
    const { container, api } = await open({ [`GET ${sourcesPath("t3")}`]: () => json(sourcesFixture) });
    const r = row(container, "t3");

    await act(async () => void fireEvent.click(r));
    await waitFor(() => expect(container.querySelector('[data-topic-detail="t3"]')?.textContent).toContain("หน้า 5"));
    await act(async () => void fireEvent.click(r));
    expect(r.getAttribute("aria-expanded")).toBe("false");
    expect(container.querySelector('[data-topic-detail="t3"]')).toBeNull();

    await act(async () => void fireEvent.click(r));
    expect(container.querySelector('[data-topic-detail="t3"]')?.textContent).toContain("หน้า 5");
    expect(api.count(`GET ${sourcesPath("t3")}`)).toBe(1);
  });

  // Decided OQ 2
  it("SM04 several topics can be open at the same time", async () => {
    const { container } = await open({
      [`GET ${sourcesPath("t3")}`]: () => json(sourcesFixture),
      [`GET ${sourcesPath("t2")}`]: () => json({ excerpts: [], questions: [] }),
    });

    await act(async () => void fireEvent.click(row(container, "t3")));
    await act(async () => void fireEvent.click(row(container, "t2")));

    expect(row(container, "t3").getAttribute("aria-expanded")).toBe("true");
    expect(row(container, "t2").getAttribute("aria-expanded")).toBe("true");
  });

  // AC-11
  it("SM04 a topic with no past exam questions says so", async () => {
    const { container } = await open({ [`GET ${sourcesPath("t9")}`]: () => json({ ...sourcesFixture, questions: [] }) });

    await act(async () => void fireEvent.click(row(container, "t9")));

    await waitFor(() =>
      expect(container.querySelector('[data-topic-detail="t9"]')?.textContent).toContain("ยังไม่เคยออกในข้อสอบเก่า"),
    );
  });

  // AC-12
  it("SM04 a failed sources request shows an error with retry that fetches again", async () => {
    const { container, api } = await open({
      [`GET ${sourcesPath("t3")}`]: [() => json({ error: { code: "x", message: "boom" } }, 500), () => json(sourcesFixture)],
    });

    await act(async () => void fireEvent.click(row(container, "t3")));
    const detail = await waitFor(() => {
      const el = container.querySelector<HTMLElement>('[data-topic-detail="t3"]');
      expect(el?.textContent).toContain("โหลดที่มาไม่สำเร็จ");
      return el!;
    });

    await act(async () => void fireEvent.click(within(detail).getByRole("button", { name: "ลองใหม่" })));
    await waitFor(() => expect(container.querySelector('[data-topic-detail="t3"]')?.textContent).toContain("หน้า 5"));
    expect(api.count(`GET ${sourcesPath("t3")}`)).toBe(2);
  });

  // AC-13
  it("TM08 a past exam question renders its math with KaTeX", async () => {
    const { container } = await open({ [`GET ${sourcesPath("t3")}`]: () => json(sourcesFixture) });

    await act(async () => void fireEvent.click(row(container, "t3")));
    await waitFor(() => expect(container.querySelector('[data-question-id="q3"] .tex')).toBeTruthy());

    expect(texSources(container.querySelector<HTMLElement>('[data-question-id="q3"]')!)).toEqual(["x^2 - 49"]);
  });
});

describe("ScopeReview unmapped questions", () => {
  // AC-14
  it("SM04 questions that fit no topic get their own box with the AI's note", async () => {
    const { getByRole } = await open();

    const box = getByRole("region", { name: "ข้อสอบที่ไม่เข้าหัวข้อไหน · 1 ข้อ" });
    expect(box.textContent).toContain("midterm-2567 ข้อ 11");
    expect(box.textContent).toContain("AI: เป็นเรื่องสมการกำลังสอง ไม่มีในชีทที่ใส่มา");
    expect(texSources(box)).toEqual(["x^2 - 5x + 6 = 0"]);
  });

  it("SM04 no unmapped questions means no box", async () => {
    const { queryByRole } = await open({ [`GET ${SCOPE_PATH}`]: () => json(scope({ unmapped_questions: [] })) });

    expect(queryByRole("region", { name: /ข้อสอบที่ไม่เข้าหัวข้อไหน/ })).toBeNull();
  });
});

describe("ScopeReview buttons and states", () => {
  // AC-15
  it("SM09 confirming posts once, disables the button while waiting, then goes to the room", async () => {
    const confirm = pending();
    const { getByRole, api, navigate } = await open({ [`POST ${CONFIRM_PATH}`]: confirm.handler });
    const button = getByRole("button", { name: "ยืนยันขอบเขตนี้" }) as HTMLButtonElement;

    await act(async () => void fireEvent.click(button));
    expect(button.disabled).toBe(true);
    await act(async () => void fireEvent.click(button));
    expect(api.count(`POST ${CONFIRM_PATH}`)).toBe(1);

    await confirm.release(json({}));
    await waitFor(() => expect(navigate).toHaveBeenCalledWith(`/preps/${PREP}/room`));
  });

  // AC-16
  it("SM09 a failed confirm says so, stays on the page and can be pressed again", async () => {
    const { getByRole, getByText, navigate } = await open({
      [`POST ${CONFIRM_PATH}`]: () => json({ error: { code: "x", message: "boom" } }, 500),
    });
    const button = getByRole("button", { name: "ยืนยันขอบเขตนี้" }) as HTMLButtonElement;

    await act(async () => void fireEvent.click(button));

    await waitFor(() => expect(getByText("ยืนยันไม่สำเร็จ ลองอีกครั้งนะ")).toBeTruthy());
    expect(navigate).not.toHaveBeenCalled();
    expect(button.disabled).toBe(false);
  });

  // AC-17
  it("SM04 shows loading, then an error with retry when the scope does not load", async () => {
    const first = pending();
    mockApi({ [`GET ${SCOPE_PATH}`]: [first.handler, () => json(scopeFixture)] });
    const { getByText, getByRole, container } = render(<ScopeReview prepId={PREP} navigate={vi.fn()} />);

    expect(getByText("กำลังโหลดขอบเขต…")).toBeTruthy();
    await first.release(json({ error: { code: "x", message: "boom" } }, 500));
    await waitFor(() => expect(getByText("โหลดขอบเขตไม่สำเร็จ")).toBeTruthy());

    await act(async () => void fireEvent.click(getByRole("button", { name: "ลองใหม่" })));
    await waitFor(() => expect(rows(container)).toHaveLength(6));
  });

  it("SM04 a 404 says the prep was not found with a link home", async () => {
    mockApi({ [`GET ${SCOPE_PATH}`]: () => json({ error: { code: "exam_prep_not_found", message: "x" } }, 404) });
    const { findByText, getByRole } = render(<ScopeReview prepId={PREP} navigate={vi.fn()} />);

    expect(await findByText("ไม่พบการเตรียมสอบนี้")).toBeTruthy();
    expect(getByRole("link", { name: "กลับหน้าหลัก" }).getAttribute("href")).toBe("/");
  });

  // AC-18
  it("SM09 no topics says so and confirm is disabled", async () => {
    const { getByText, getByRole } = await open({ [`GET ${SCOPE_PATH}`]: () => json(withTopics([])) });

    expect(getByText("ยังไม่มีหัวข้อ")).toBeTruthy();
    expect((getByRole("button", { name: "ยืนยันขอบเขตนี้" }) as HTMLButtonElement).disabled).toBe(true);
  });

  // AC-19 (decided OQ 1)
  it("SM06 ขอแก้ก่อน is shown but disabled until the chat edit exists", async () => {
    const { getByRole, getByText } = await open();

    expect((getByRole("button", { name: "ขอแก้ก่อน" }) as HTMLButtonElement).disabled).toBe(true);
    expect(getByText("แก้ผ่านแชทได้เร็วๆ นี้")).toBeTruthy();
  });

  // AC-19b (decided OQ 4)
  it("SM09 a confirmed scope is read-only with a link to the room and topics still open", async () => {
    const { queryByRole, getByRole, getByText, container } = await open({
      [`GET ${SCOPE_PATH}`]: () => json(scope({ status: "confirmed" })),
      [`GET ${sourcesPath("t3")}`]: () => json(sourcesFixture),
    });

    expect(queryByRole("button", { name: "ขอแก้ก่อน" })).toBeNull();
    expect(queryByRole("button", { name: "ยืนยันขอบเขตนี้" })).toBeNull();
    expect(getByText("ยืนยันขอบเขตแล้ว")).toBeTruthy();
    expect(getByRole("link", { name: "ไปห้องติว" }).getAttribute("href")).toBe(`/preps/${PREP}/room`);

    await act(async () => void fireEvent.click(row(container, "t3")));
    expect(row(container, "t3").getAttribute("aria-expanded")).toBe("true");
  });

  // AC-20
  it("SM04 topic rows are buttons reachable by keyboard with aria-expanded", async () => {
    const { container } = await open();

    for (const r of rows(container)) {
      expect(r.tagName).toBe("BUTTON");
      expect(r.getAttribute("aria-expanded")).toBe("false");
    }
  });
});
