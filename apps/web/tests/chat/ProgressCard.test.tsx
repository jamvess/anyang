import { cleanup, fireEvent, render, within } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { MessageList } from "@/components/chat/MessageList";
import { PROGRESS_CARD_VISIBLE_TOPICS, ProgressCard } from "@/components/chat/ProgressCard";
import type { ChatMessage } from "@/components/chat/types";

// Spec: specs/features/tutor/progress-card.md · card data from apps/api/app/stubs/room.json (m0)
const STUB_CARD = {
  days_left: 5,
  passed: 1,
  total: 4,
  readiness: 0.25,
  topics: [
    { id: "t1", name: "ตัวประกอบร่วม", stars: 1, level: "passed", review_due: false, origin: "doc" },
    { id: "t2", name: "ผลต่างกำลังสอง", stars: 3, level: "developing", review_due: false, origin: "doc" },
    { id: "t3", name: "กำลังสองสมบูรณ์", stars: 2, level: "not_started", review_due: false, origin: "doc" },
    { id: "t4", name: "แยกตัวประกอบพหุนามดีกรีสอง", stars: 3, level: "weak", review_due: true, origin: "doc" },
  ],
};
const EXPLAIN = "ความพร้อม = สัดส่วนของเนื้อหาข้อสอบที่คาดว่าทำได้ ไม่ใช่คะแนนสอบ";

const topics = (n: number) =>
  Array.from({ length: n }, (_, i) => ({
    id: `t${i + 1}`,
    name: `หัวข้อ ${i + 1}`,
    stars: 2,
    level: "not_started",
    review_due: false,
    origin: "doc",
  }));

const cardMessage = (card: unknown): ChatMessage => ({
  id: "m0",
  role: "card",
  content: null,
  card: card as ChatMessage["card"],
  input_mode: null,
  attachment_path: null,
  created_at: "2026-08-28T13:30:00Z",
});

/** Rows of the topic list: [name, level] in display order. */
const rows = (card: HTMLElement) =>
  [...card.querySelectorAll<HTMLElement>("[data-topic]")].map((r) => ({
    name: r.querySelector("[data-topic-name]")?.textContent,
    level: r.querySelector("[data-topic-level]")?.textContent,
    stars: r.querySelectorAll("[data-star-on]").length,
    text: r.textContent ?? "",
  }));

afterEach(cleanup);

describe("ProgressCard", () => {
  it("TM15 a card message in the history shows as a progress card, not a bubble", () => {
    const { getByRole, container } = render(
      <MessageList messages={[cardMessage(STUB_CARD)]} tutorName="พี่ตาล" buddyName="มีน" />,
    );

    const card = getByRole("group", { name: "ความคืบหน้า" });
    expect(card.textContent).toContain("สอบใน 5 วัน");
    expect(card.textContent).toContain("1 / 4 หัวข้อ");
    expect(card.textContent).toContain("25%");
    expect(card.textContent).toContain(EXPLAIN);
    expect(container.querySelectorAll("[data-role]")).toHaveLength(0);
  });

  it("TM15 topics keep the API order with their level label and filled stars", () => {
    const { getByRole } = render(<ProgressCard card={STUB_CARD} />);

    expect(rows(getByRole("group"))).toEqual([
      expect.objectContaining({ name: "ตัวประกอบร่วม", level: "ผ่าน", stars: 1 }),
      expect.objectContaining({ name: "ผลต่างกำลังสอง", level: "กำลังดี", stars: 3 }),
      expect.objectContaining({ name: "กำลังสองสมบูรณ์", level: "ยังไม่เริ่ม", stars: 2 }),
      expect.objectContaining({ name: "แยกตัวประกอบพหุนามดีกรีสอง", level: "อ่อน", stars: 3 }),
    ]);
  });

  it("TM15 review_due and user-added topics get small tags; others do not", () => {
    const card = {
      ...STUB_CARD,
      topics: [...STUB_CARD.topics, { ...topics(1)[0], id: "u1", name: "สมการกำลังสอง", origin: "user" }],
    };
    const { getByRole } = render(<ProgressCard card={card} />);

    const r = rows(getByRole("group"));
    expect(r[3].text).toContain("ถึงรอบทวน");
    expect(r[0].text).not.toContain("ถึงรอบทวน");
    expect(r[4].text).toContain("นอกเอกสาร");
    expect(r[0].text).not.toContain("นอกเอกสาร");
  });

  it("TM15 an unknown level shows a dash", () => {
    const card = { ...STUB_CARD, topics: [{ ...STUB_CARD.topics[0], level: "mystery" }] };
    const { getByRole } = render(<ProgressCard card={card} />);

    expect(rows(getByRole("group"))[0].level).toBe("—");
  });

  it.each([
    [0.004, "0%"],
    [0.005, "1%"],
    [0.996, "100%"],
  ])("PM03 readiness %f shows as %s", (readiness, shown) => {
    const { getByRole } = render(<ProgressCard card={{ ...STUB_CARD, readiness }} />);

    expect(getByRole("group").textContent).toContain(shown);
  });

  it("TM15 a card message with card = null shows nothing", () => {
    const { container, queryByRole } = render(
      <MessageList messages={[cardMessage(null)]} tutorName="พี่ตาล" buddyName="มีน" />,
    );

    expect(queryByRole("group")).toBeNull();
    expect(container.querySelectorAll("[data-role]")).toHaveLength(0);
  });

  it("TM15 exactly PROGRESS_CARD_VISIBLE_TOPICS topics show all rows and no more button", () => {
    const { getByRole, queryByRole } = render(
      <ProgressCard card={{ ...STUB_CARD, topics: topics(PROGRESS_CARD_VISIBLE_TOPICS) }} />,
    );

    expect(rows(getByRole("group"))).toHaveLength(PROGRESS_CARD_VISIBLE_TOPICS);
    expect(queryByRole("button", { name: /^อีก/ })).toBeNull();
  });

  it("TM15 one topic over the limit shows the limit, a more button, and all rows after a click", () => {
    const n = PROGRESS_CARD_VISIBLE_TOPICS + 1;
    const { getByRole, queryByRole } = render(<ProgressCard card={{ ...STUB_CARD, topics: topics(n) }} />);
    const card = getByRole("group");

    expect(rows(card)).toHaveLength(PROGRESS_CARD_VISIBLE_TOPICS);
    fireEvent.click(within(card).getByRole("button", { name: "อีก 1 หัวข้อ" }));

    expect(rows(card)).toHaveLength(n);
    expect(queryByRole("button", { name: /^อีก/ })).toBeNull();
  });
});
