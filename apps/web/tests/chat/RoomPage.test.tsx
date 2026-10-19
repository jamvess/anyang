import { cleanup, fireEvent, render } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { ChatRoom } from "@/components/chat/ChatRoom";
import type { RoomData } from "@/components/chat/types";
import fixture from "../fixtures/room/session-s15.json";

const room = fixture as RoomData;

afterEach(cleanup);

describe("ChatRoom (S2, fixture data)", () => {
  it("TM04 top bar shows the prep name, days left from the data and a link out of the room", () => {
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

  it("TM06 a sent message appears at the end as a user bubble", () => {
    const { container, getByLabelText, getByRole } = render(<ChatRoom room={room} />);

    fireEvent.change(getByLabelText("พิมพ์ตอบ"), { target: { value: "ใช่ๆ" } });
    fireEvent.click(getByRole("button", { name: "ส่ง" }));

    const bubbles = container.querySelectorAll("[data-role]");
    const last = bubbles[bubbles.length - 1];
    expect(last.getAttribute("data-role")).toBe("user");
    expect(last.textContent).toContain("ใช่ๆ");
  });
});
