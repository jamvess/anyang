import { Activity } from "react";
import { act, cleanup, fireEvent, render, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ScopeReview } from "@/components/scope/ScopeReview";
import { loginRedirect } from "@/lib/auth";
import scopeFixture from "../fixtures/scope/scope-s12.json";

// Spec: specs/features/scope/scope-review.md §2 "ต่อ API จริง" · AC-21 to AC-24 (the page on the
// API of scope-db.md, PR #137). AC-1 to AC-20 stay in ScopeReview.test.tsx. Every request goes to a
// mocked fetch.

const API = "http://api.test";
const PREP = "11111111-1111-4111-8111-111111111111";
const SCOPE = `GET /exam-preps/${PREP}/scope`;
const CONFIRM = `POST /exam-preps/${PREP}/scope/confirm`;
const SOURCES_T3 = "GET /topics/t3/sources";
const ROOM = `/preps/${PREP}/room`;

const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
const apiError = (status: number, code: string) => () => json({ error: { code, message: "x" } }, status);
const draft = () => json(scopeFixture);
const confirmed = () => json({ ...scopeFixture, status: "confirmed" });

type Handler = () => Response | Promise<Response>;

/** fetch mock routed by "METHOD path"; a list is used one response per call. */
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

function open(routes: Record<string, Handler | Handler[]>) {
  const api = mockApi(routes);
  const navigate = vi.fn();
  const utils = render(<ScopeReview prepId={PREP} navigate={navigate} />);
  return { ...utils, api, navigate };
}

/** Let the promises of a finished request settle (the page sets its state after fetch). */
const settle = () => act(async () => new Promise((r) => setTimeout(r, 0)));

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

describe("ScopeReview on the real API", () => {
  // AC-21
  it("SM09 a scope not ready yet says the files are still being read, with retry and home", async () => {
    const utils = open({ [SCOPE]: [apiError(409, "scope_not_ready"), draft] });

    expect(await utils.findByText("ระบบยังอ่านไฟล์ไม่เสร็จ")).toBeTruthy();
    expect(utils.queryByText("โหลดขอบเขตไม่สำเร็จ")).toBeNull();
    expect(utils.getByRole("link", { name: "กลับหน้าหลัก" }).getAttribute("href")).toBe("/");

    fireEvent.click(utils.getByRole("button", { name: "ลองใหม่" }));

    expect(await utils.findByText("1 · คูณพหุนาม")).toBeTruthy();
    expect(utils.api.count(SCOPE)).toBe(2);
    expect(utils.queryByText("ระบบยังอ่านไฟล์ไม่เสร็จ")).toBeNull();
  });

  // AC-22
  it("SM09 a scope already confirmed elsewhere goes to the room, with no error", async () => {
    const utils = open({ [SCOPE]: draft, [CONFIRM]: apiError(409, "scope_already_confirmed") });
    fireEvent.click(await utils.findByRole("button", { name: "ยืนยันขอบเขตนี้" }));

    await waitFor(() => expect(utils.navigate).toHaveBeenCalledWith(ROOM));
    expect(utils.queryByText("ยืนยันไม่สำเร็จ ลองอีกครั้งนะ")).toBeNull();
  });

  it("SM09 an empty scope says every topic was cut, stays, and the button works again", async () => {
    const utils = open({ [SCOPE]: draft, [CONFIRM]: apiError(409, "scope_empty") });
    fireEvent.click(await utils.findByRole("button", { name: "ยืนยันขอบเขตนี้" }));

    expect(await utils.findByText("ไม่มีหัวข้อให้ติว ทุกหัวข้อถูกตัดออก")).toBeTruthy();
    expect(utils.queryByText("ยืนยันไม่สำเร็จ ลองอีกครั้งนะ")).toBeNull();
    expect(utils.navigate).not.toHaveBeenCalled();
    expect(utils.getByRole("button", { name: "ยืนยันขอบเขตนี้" })).toHaveProperty("disabled", false);
  });

  it("SM09 a scope not ready at confirm is the usual confirm failure (AC-16)", async () => {
    const utils = open({ [SCOPE]: draft, [CONFIRM]: apiError(409, "scope_not_ready") });
    fireEvent.click(await utils.findByRole("button", { name: "ยืนยันขอบเขตนี้" }));

    expect(await utils.findByText("ยืนยันไม่สำเร็จ ลองอีกครั้งนะ")).toBeTruthy();
    expect(utils.navigate).not.toHaveBeenCalled();
  });

  // AC-23
  it("UM01 a 401 on the scope shows no load error: the login page is on its way", async () => {
    const utils = open({ [SCOPE]: apiError(401, "invalid_token") });

    await waitFor(() => expect(toLogin).toHaveBeenCalled());
    await settle();
    expect(utils.queryByText("โหลดขอบเขตไม่สำเร็จ")).toBeNull();
    expect(utils.queryByRole("button", { name: "ลองใหม่" })).toBeNull();
  });

  it("UM01 a 401 on the sources shows no sources error", async () => {
    const utils = open({ [SCOPE]: draft, [SOURCES_T3]: apiError(401, "invalid_token") });
    await utils.findByText("3 · ผลต่างกำลังสอง");

    fireEvent.click(utils.container.querySelector<HTMLElement>('[data-topic-id="t3"]')!);

    await waitFor(() => expect(toLogin).toHaveBeenCalled());
    await settle();
    expect(utils.queryByText("โหลดที่มาไม่สำเร็จ")).toBeNull();
  });

  it("UM01 a 401 on confirm shows no confirm error and does not go to the room", async () => {
    const utils = open({ [SCOPE]: draft, [CONFIRM]: apiError(401, "invalid_token") });
    fireEvent.click(await utils.findByRole("button", { name: "ยืนยันขอบเขตนี้" }));

    await waitFor(() => expect(toLogin).toHaveBeenCalled());
    await settle();
    expect(utils.queryByText("ยืนยันไม่สำเร็จ ลองอีกครั้งนะ")).toBeNull();
    expect(utils.navigate).not.toHaveBeenCalled();
  });
});

describe("ScopeReview under Next's preserved pages", () => {
  // Next 16 with cacheComponents hides the page it leaves (React <Activity>) and keeps its state.
  function openIn(routes: Record<string, Handler | Handler[]>) {
    const api = mockApi(routes);
    const navigate = vi.fn();
    const page = (mode: "visible" | "hidden") => (
      <Activity mode={mode}>
        <ScopeReview prepId={PREP} navigate={navigate} />
      </Activity>
    );
    const utils = render(page("visible"));
    const hideAndShow = () => {
      utils.rerender(page("hidden"));
      utils.rerender(page("visible"));
    };
    return { ...utils, api, navigate, hideAndShow };
  }

  // AC-24
  it("SM09 a page shown again reloads the scope: confirmed meanwhile is read-only", async () => {
    const utils = openIn({ [SCOPE]: [draft, confirmed] });
    await utils.findByRole("button", { name: "ยืนยันขอบเขตนี้" });

    utils.hideAndShow();

    expect(await utils.findByText("ยืนยันขอบเขตแล้ว")).toBeTruthy();
    expect(utils.api.count(SCOPE)).toBe(2);
    expect(utils.queryByRole("button", { name: "ยืนยันขอบเขตนี้" })).toBeNull();
  });

  it("SM09 after a confirm, a page shown again is not stuck on a disabled button", async () => {
    const utils = openIn({ [SCOPE]: [draft, draft], [CONFIRM]: () => json({ version: 1 }) });
    fireEvent.click(await utils.findByRole("button", { name: "ยืนยันขอบเขตนี้" }));
    await waitFor(() => expect(utils.navigate).toHaveBeenCalledWith(ROOM));

    utils.hideAndShow();

    await waitFor(() => expect(utils.api.count(SCOPE)).toBe(2));
    await settle();
    expect(utils.getByRole("button", { name: "ยืนยันขอบเขตนี้" })).toHaveProperty("disabled", false);
  });
});
