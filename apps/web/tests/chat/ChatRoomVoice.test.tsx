import { act, cleanup, fireEvent, render } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, type Mock, vi } from "vitest";
import { ChatRoom } from "@/components/chat/ChatRoom";
import type { RoomData, SendPayload } from "@/components/chat/types";
import type { SSEEvent } from "@/lib/sse";
import { installMic } from "../helpers/fakeMic";
import fixture from "../fixtures/room/session-s15.json";

// Spec: specs/features/tutor/voice-input.md
// Audio limits are not in the API yet (OQ 5): the fixture's limits plus the proposed values.
const room = {
  ...fixture,
  limits: { ...fixture.limits, max_audio_seconds: 60, min_audio_seconds: 1 },
} as unknown as RoomData;
const MIC = "กดค้างเพื่อพูด";

beforeEach(() => {
  vi.useFakeTimers();
});

afterEach(() => {
  cleanup();
  vi.useRealTimers();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

const settle = () => act(async () => void (await vi.advanceTimersByTimeAsync(0)));
const wait = (seconds: number) => act(async () => void (await vi.advanceTimersByTimeAsync(seconds * 1000)));

/** A reply stream the test ends by hand. */
function openReply() {
  let finish!: () => void;
  const ended = new Promise<void>((r) => (finish = r));
  const sendMessage = vi.fn((_p: SendPayload, _s: AbortSignal) =>
    (async function* (): AsyncGenerator<SSEEvent> {
      yield { event: "token", data: { speaker: "tutor", text: "รอแป๊บ" } };
      await ended;
      yield { event: "done", data: {} };
    })(),
  );
  return { sendMessage, finish: () => act(async () => finish()) };
}

function setup({
  sendMessage = vi.fn(async function* (): AsyncGenerator<SSEEvent> {
    yield { event: "done", data: {} };
  }),
  transcribe = vi.fn(async (_a: Blob, _s: AbortSignal) => ({ text: "สองเอ็กซ์ลบห้า" })),
}: {
  sendMessage?: Mock<(p: SendPayload, s: AbortSignal) => AsyncIterable<SSEEvent>>;
  transcribe?: (a: Blob, s: AbortSignal) => Promise<{ text: string }>;
} = {}) {
  const utils = render(<ChatRoom room={room} sendMessage={sendMessage} transcribe={transcribe} voiceEnabled />);
  const input = utils.getByLabelText("พิมพ์ตอบ") as HTMLTextAreaElement;
  const mic = () => utils.getByRole("button", { name: MIC });
  const sendButton = () => utils.getByRole("button", { name: "ส่ง" }) as HTMLButtonElement;
  const talk = async (seconds = 2) => {
    fireEvent.pointerDown(mic());
    await settle();
    await wait(seconds);
    fireEvent.pointerUp(mic());
    await settle();
  };
  return { ...utils, input, mic, sendButton, talk, sendMessage, transcribe };
}

describe("ChatRoom voice answer", () => {
  // AC-4
  it("TM07 a spoken answer is sent only when the user presses send, and is marked as voice", async () => {
    installMic();
    const t = setup();

    await t.talk();
    expect(t.sendMessage).not.toHaveBeenCalled();
    expect(t.input.value).toBe("สองเอ็กซ์ลบห้า");

    fireEvent.change(t.input, { target: { value: "(2x-5)(2x+5)" } });
    await act(async () => void fireEvent.click(t.sendButton()));

    expect(t.sendMessage).toHaveBeenCalledTimes(1);
    expect(t.sendMessage.mock.calls[0][0]).toEqual({ text: "(2x-5)(2x+5)", image: null, voice: true });
    const bubbles = t.container.querySelectorAll('[data-role="user"]');
    expect(bubbles[bubbles.length - 1].textContent).toContain("(2x-5)(2x+5)");
  });

  // AC-14
  it.each([
    ["while recording", "recording"],
    ["while transcribing", "transcribing"],
  ])("TM07 leaving the room %s releases the microphone and aborts the request", async (_name, phase) => {
    const m = installMic();
    let signal: AbortSignal | undefined;
    const transcribe = vi.fn((_a: Blob, s: AbortSignal) => {
      signal = s;
      return new Promise<{ text: string }>(() => {});
    });
    const consoleError = vi.spyOn(console, "error");
    const t = setup({ transcribe });

    fireEvent.pointerDown(t.mic());
    await settle();
    await wait(2);
    if (phase === "transcribing") {
      fireEvent.pointerUp(t.mic());
      await settle();
    }
    t.unmount();

    expect(m.track.stop).toHaveBeenCalled();
    if (phase === "transcribing") expect(signal?.aborted).toBe(true);
    else expect(transcribe).not.toHaveBeenCalled();
    expect(consoleError).not.toHaveBeenCalled();
  });

  // AC-15
  it("TM07 the user can speak while the tutor answers, but send waits for the reply to end", async () => {
    installMic();
    const reply = openReply();
    const t = setup({ sendMessage: reply.sendMessage });

    fireEvent.change(t.input, { target: { value: "ตอบ" } });
    await act(async () => void fireEvent.click(t.sendButton()));
    await settle();

    await t.talk();
    expect(t.input.value).toBe("สองเอ็กซ์ลบห้า");
    expect(t.sendButton().disabled).toBe(true);

    await reply.finish();
    await settle();
    expect(t.sendButton().disabled).toBe(false);
  });

  // AC-17
  it("TM06 a room with a voice transport has mic, attach and send as its only buttons", () => {
    installMic();
    const t = setup();

    const names = t.getAllByRole("button").map((b) => b.getAttribute("aria-label") ?? b.textContent);
    expect(names.sort()).toEqual([MIC, "ส่ง", "แนบรูป"].sort());
  });
});
