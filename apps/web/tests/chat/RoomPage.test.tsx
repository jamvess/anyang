import { cleanup, fireEvent, render, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import RoomPage from "@/app/preps/[id]/room/page";
import { ChatRoom } from "@/components/chat/ChatRoom";
import type { RoomData } from "@/components/chat/types";
import fixture from "../fixtures/room/session-s15.json";

const room = fixture as RoomData;

afterEach(cleanup);

describe("ChatRoom (S2, fixture data)", () => {
  it("TM20 top bar shows the prep name, days left from the data and a link out of the room", () => {
    const { getByText, getByRole } = render(<ChatRoom room={room} />);

    expect(getByText(room.prep_name)).toBeTruthy();
    expect(getByText(`สอบใน ${room.days_left} วัน`)).toBeTruthy();
    const exit = getByRole("link", { name: "ออกจากห้องติว" });
    expect(exit.getAttribute("href")).toBe("/");
  });

  it("TM06 the whole room has no answer choice buttons", () => {
    const { getAllByRole } = render(<ChatRoom room={room} />);

    const names = getAllByRole("button").map((b) => b.getAttribute("aria-label") ?? b.textContent);
    expect(names.sort()).toEqual(["ส่ง", "แนบรูป"].sort());
  });

  it("TM20 a sent message appears at the end as a user bubble", () => {
    const { container, getByLabelText, getByRole } = render(<ChatRoom room={room} />);

    fireEvent.change(getByLabelText("พิมพ์ตอบ"), { target: { value: "ใช่ๆ" } });
    fireEvent.click(getByRole("button", { name: "ส่ง" }));

    const bubbles = container.querySelectorAll("[data-role]");
    const last = bubbles[bubbles.length - 1];
    expect(last.getAttribute("data-role")).toBe("user");
    expect(last.textContent).toContain("ใช่ๆ");
  });
});

describe("Room page (S3, fake transport)", () => {
  // chat-streaming.md AC-21
  it("TM20 a sent message gets the streamed reply from tutor_reply.txt", async () => {
    const { container, getByLabelText, getByRole } = render(<RoomPage />);
    const before = container.querySelectorAll("[data-role]").length;

    fireEvent.change(getByLabelText("พิมพ์ตอบ"), { target: { value: "ใช่ๆ" } });
    fireEvent.click(getByRole("button", { name: "ส่ง" }));

    await waitFor(
      () => {
        const added = [...container.querySelectorAll("[data-role]")].slice(before);
        expect(added.map((b) => b.getAttribute("data-role"))).toEqual(["user", "tutor", "buddy", "tutor"]);
        expect(added[0].textContent).toContain("ใช่ๆ");
        expect(added[1].textContent).toContain("ถูกแล้ว");
        expect(added[3].querySelectorAll("div.tex > .katex-display")).toHaveLength(1);
      },
      { timeout: 5000 },
    );
  }, 10_000);
});
