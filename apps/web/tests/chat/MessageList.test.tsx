import { cleanup, render, within } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { MessageList, avatarInitial } from "@/components/chat/MessageList";
import { MESSAGE_GROUP_GAP_MIN } from "@/components/chat/MessageList";
import type { ChatMessage } from "@/components/chat/types";
import room from "../fixtures/room/session-s15.json";

const messages = room.messages as ChatMessage[];

function msg(partial: Partial<ChatMessage> & Pick<ChatMessage, "id" | "role">): ChatMessage {
  return {
    content: null,
    input_mode: null,
    attachment_path: null,
    created_at: "2026-08-28T13:30:00Z",
    ...partial,
  };
}

afterEach(cleanup);

describe("MessageList", () => {
  it("TM20 shows tutor, buddy and user bubbles in created_at order", () => {
    const shuffled = [...messages].reverse();
    const { container } = render(
      <MessageList messages={shuffled} tutorName={room.tutor_name} buddyName={room.buddy_name} />,
    );

    const roles = [...container.querySelectorAll("[data-role]")].map((el) =>
      el.getAttribute("data-role"),
    );
    const expected = messages
      .filter((m) => m.role === "tutor" || m.role === "buddy" || m.role === "user")
      .map((m) => m.role);
    expect(roles).toEqual(expected);
  });

  it("TM20 buddy bubble shows the buddy name and an avatar different from the tutor", () => {
    const { container } = render(
      <MessageList
        messages={[
          msg({ id: "t", role: "tutor", content: "ลองข้อนี้" }),
          msg({ id: "b", role: "buddy", content: "เดี๋ยวดิ", created_at: "2026-08-28T13:31:00Z" }),
        ]}
        tutorName="พี่ตาล"
        buddyName="มีน"
      />,
    );

    const buddy = container.querySelector('[data-role="buddy"]') as HTMLElement;
    const tutor = container.querySelector('[data-role="tutor"]') as HTMLElement;
    expect(within(buddy).getByText("มีน")).toBeTruthy();

    const buddyAvatar = buddy.querySelector("[data-avatar]");
    const tutorAvatar = tutor.querySelector("[data-avatar]");
    expect(buddyAvatar?.textContent).toBe("ม");
    expect(tutorAvatar?.textContent).toBe("ต");
    expect(buddyAvatar?.getAttribute("data-avatar")).not.toBe(
      tutorAvatar?.getAttribute("data-avatar"),
    );
  });

  it.each([
    ["พี่ตาล", "ต"],
    ["พี่โจ๊ก", "จ"],
    ["มีน", "ม"],
    ["ครู แอน", "อ"],
    ["Tar", "T"],
  ])("TM20 avatar initial of %s is %s", (name, initial) => {
    expect(avatarInitial(name)).toBe(initial);
  });

  it("TM20 shows the speaker name once for consecutive messages from the same speaker", () => {
    const { getAllByText, container } = render(
      <MessageList
        messages={[
          msg({ id: "a", role: "tutor", content: "ถูก" }),
          msg({ id: "b", role: "tutor", content: "ข้ามไปเลย", created_at: "2026-08-28T13:30:10Z" }),
        ]}
        tutorName="พี่ตาล"
        buddyName={null}
      />,
    );

    expect(container.querySelectorAll('[data-role="tutor"]')).toHaveLength(2);
    expect(getAllByText("พี่ตาล")).toHaveLength(1);
  });

  it.each(["card", "system"] as const)("TM20 does not render a bubble for role %s", (role) => {
    const { container } = render(
      <MessageList
        messages={[msg({ id: "x", role, content: "ไม่ควรเห็น" })]}
        tutorName="พี่ตาล"
        buddyName="มีน"
      />,
    );

    expect(container.querySelectorAll("[data-role]")).toHaveLength(0);
    expect(container.textContent).not.toContain("ไม่ควรเห็น");
  });

  it("TM06 shows a photo message as a box with the file name from attachment_path", () => {
    const { container } = render(
      <MessageList
        messages={[
          msg({
            id: "p",
            role: "user",
            input_mode: "image",
            attachment_path: "sessions/s1/วิธีทำ.jpg",
          }),
        ]}
        tutorName="พี่ตาล"
        buddyName="มีน"
      />,
    );

    const user = container.querySelector('[data-role="user"]') as HTMLElement;
    expect(within(user).getByText(/วิธีทำ\.jpg/)).toBeTruthy();
    expect(user.textContent).not.toContain("sessions/s1/");
  });

  // chat-room-ui.md AC-6b (api.md v1.3)
  it("TM06 the photo box shows attachment_name, not the uuid file name in attachment_path", () => {
    const { container } = render(
      <MessageList
        messages={[
          msg({
            id: "p",
            role: "user",
            input_mode: "image",
            attachment_name: "วิธีทำ.jpg",
            attachment_path: "sessions/s1/3f2a9c1e-7b4d-4e8a-9c2f-1d5e6a7b8c90.jpg",
          }),
        ]}
        tutorName="พี่ตาล"
        buddyName="มีน"
      />,
    );

    const user = container.querySelector('[data-role="user"]') as HTMLElement;
    expect(within(user).getByText(/วิธีทำ\.jpg/)).toBeTruthy();
    expect(user.textContent).not.toContain("3f2a9c1e");
  });

  // chat-room-ui.md AC-6c
  it("TM06 a local photo message with attachment_name and no attachment_path still shows its box", () => {
    const { container } = render(
      <MessageList
        messages={[msg({ id: "p", role: "user", input_mode: "image", attachment_name: "วิธีทำ.jpg" })]}
        tutorName="พี่ตาล"
        buddyName="มีน"
      />,
    );

    const user = container.querySelector('[data-role="user"]') as HTMLElement;
    expect(within(user).getByText(/วิธีทำ\.jpg/)).toBeTruthy();
  });
});

// Spec: chat-room-ui.md AC-3b, AC-3b-boundary (repeat the header after a long gap)
describe("MessageList · time gap between the same speaker", () => {
  const at = (iso: string, plusSeconds = 0) => new Date(Date.parse(iso) + plusSeconds * 1000).toISOString();
  const T0 = "2026-10-20T13:00:00Z";
  const gap = MESSAGE_GROUP_GAP_MIN * 60;

  function tutorPair(secondsApart: number) {
    return render(
      <MessageList
        messages={[
          msg({ id: "a", role: "tutor", content: "ข้อแรก", created_at: at(T0) }),
          msg({ id: "b", role: "tutor", content: "ข้อสอง", created_at: at(T0, secondsApart) }),
        ]}
        tutorName="พี่ตาล"
        buddyName="มีน"
      />,
    );
  }

  it("TM20 a user message the next day after an old one shows the name again with its own time", () => {
    const { getAllByText, container } = render(
      <MessageList
        messages={[
          msg({ id: "old", role: "user", content: "ใช่ๆ", created_at: "2026-10-20T13:47:00Z" }),
          msg({ id: "new", role: "user", content: "(x-7)(x+7)", created_at: "2026-10-21T04:42:00Z" }),
        ]}
        tutorName="พี่ตาล"
        buddyName="มีน"
        userName="ปาล"
      />,
    );

    expect(getAllByText("ปาล")).toHaveLength(2);
    const times = [...container.querySelectorAll("time")].map((t) => t.textContent);
    expect(times).toEqual(["20:47", "11:42"]);
  });

  it.each([
    [gap - 1, 1],
    [gap, 2],
    [gap + 1, 2],
  ])("TM20 two tutor messages %i seconds apart show the name %i time(s)", (seconds, headers) => {
    const { getAllByText } = tutorPair(seconds);

    expect(getAllByText("พี่ตาล")).toHaveLength(headers);
  });
});
