import { act, cleanup, fireEvent, render } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { Composer } from "@/components/chat/Composer";
import type { InputLimits } from "@/components/chat/types";
import { installMic } from "../helpers/fakeMic";
import room from "../fixtures/room/session-s15.json";

// Spec: specs/features/tutor/voice-input.md
// Audio limits are not in the API yet (OQ 5): the fixture's limits plus the proposed values.
const LIMITS = { ...room.limits, max_audio_seconds: 60, min_audio_seconds: 1 } as InputLimits;
const MAX = LIMITS.max_audio_seconds!;
const MIN = LIMITS.min_audio_seconds!;
const MIC = "กดค้างเพื่อพูด";
const VOICE_NOTE = "ข้อความจากเสียง · แก้ได้ก่อนกดส่ง ระบบไม่ส่งเอง";
const NO_MIC = "ใช้ไมค์ไม่ได้ พิมพ์คำตอบมาแทนนะ";

beforeEach(() => {
  vi.useFakeTimers();
});

afterEach(() => {
  cleanup();
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

/** Lets pending promises (getUserMedia, transcribe) settle inside act. */
const settle = () => act(async () => void (await vi.advanceTimersByTimeAsync(0)));
const wait = (seconds: number) => act(async () => void (await vi.advanceTimersByTimeAsync(seconds * 1000)));

function setup({
  limits = LIMITS,
  voiceEnabled = true,
  text = "สองเอ็กซ์ลบห้า",
  transcribe = vi.fn(async (_audio: Blob, _signal: AbortSignal) => ({ text })),
}: {
  limits?: InputLimits;
  voiceEnabled?: boolean;
  text?: string;
  transcribe?: (audio: Blob, signal: AbortSignal) => Promise<{ text: string }>;
} = {}) {
  const onSend = vi.fn();
  const utils = render(
    <Composer limits={limits} onSend={onSend} voiceEnabled={voiceEnabled} transcribe={transcribe} />,
  );
  const input = utils.getByLabelText("พิมพ์ตอบ") as HTMLTextAreaElement;
  const mic = () => utils.getByRole("button", { name: MIC }) as HTMLButtonElement;
  const press = async () => {
    fireEvent.pointerDown(mic());
    await settle();
  };
  const release = async () => {
    fireEvent.pointerUp(mic());
    await settle();
  };
  /** Holds the button for `seconds`, then lets go. */
  const talk = async (seconds = 3) => {
    await press();
    await wait(seconds);
    await release();
  };
  return { ...utils, onSend, input, mic, press, release, talk, transcribe };
}

describe("Composer voice button", () => {
  // AC-1
  it("TM07 holding the mic asks for the microphone once and starts recording with a timer", async () => {
    const m = installMic();
    const { mic, press, getByText } = setup();

    await press();

    expect(m.getUserMedia).toHaveBeenCalledTimes(1);
    expect(m.getUserMedia).toHaveBeenCalledWith({ audio: true });
    expect(m.recorder()?.start).toHaveBeenCalled();
    expect(mic().getAttribute("aria-pressed")).toBe("true");
    expect(getByText(/0:00 \/ 1:00/)).toBeTruthy();
  });

  // AC-2
  it("TM07 letting go sends the audio to transcribe and puts the text in the box without sending", async () => {
    installMic();
    let resolve!: (r: { text: string }) => void;
    const transcribe = vi.fn((_a: Blob, _s: AbortSignal) => new Promise<{ text: string }>((r) => (resolve = r)));
    const { mic, press, release, input, onSend, getByText, queryByText } = setup({ transcribe });

    await press();
    await wait(3);
    await release();

    expect(transcribe).toHaveBeenCalledTimes(1);
    expect(transcribe.mock.calls[0][0]).toBeInstanceOf(Blob);
    expect(getByText("กำลังแปลงเสียง…")).toBeTruthy();
    expect(mic().disabled).toBe(true);

    await act(async () => resolve({ text: "สองเอ็กซ์ลบห้า" }));

    expect(input.value).toBe("สองเอ็กซ์ลบห้า");
    expect(getByText(new RegExp(VOICE_NOTE))).toBeTruthy();
    expect(queryByText("กำลังแปลงเสียง…")).toBeNull();
    expect(mic().disabled).toBe(false);
    expect(onSend).not.toHaveBeenCalled();
  });

  // AC-3
  it("TM07 spoken text is added after what is already typed", async () => {
    installMic();
    const { input, talk } = setup({ text: "เอ็กซ์เท่ากับสาม" });

    fireEvent.change(input, { target: { value: "ข้อ 2" } });
    await talk();

    expect(input.value).toBe("ข้อ 2 เอ็กซ์เท่ากับสาม");
  });

  // AC-4 (Composer part)
  it("TM07 sending spoken text, even after editing, marks it as voice", async () => {
    installMic();
    const { input, talk, onSend, getByRole } = setup({ text: "สองเอ็กซ์ลบห้า" });

    await talk();
    fireEvent.change(input, { target: { value: "(2x-5)(2x+5)" } });
    fireEvent.click(getByRole("button", { name: "ส่ง" }));

    expect(onSend).toHaveBeenCalledWith({ text: "(2x-5)(2x+5)", image: null, voice: true });
  });

  // AC-5
  it("TM07 clearing the spoken text removes the voice note and the next typed message is not voice", async () => {
    installMic();
    const { input, talk, onSend, getByRole, queryByText } = setup();

    await talk();
    fireEvent.change(input, { target: { value: "" } });
    expect(queryByText(new RegExp(VOICE_NOTE))).toBeNull();

    fireEvent.change(input, { target: { value: "พิมพ์เอง" } });
    fireEvent.click(getByRole("button", { name: "ส่ง" }));
    // Typed messages keep the old payload `{text, image}` (reviewed tests compare it exactly).
    expect(onSend).toHaveBeenCalledWith({ text: "พิมพ์เอง", image: null });
    expect(onSend.mock.calls[0][0].voice).toBeUndefined();
  });

  // AC-6 (boundary: MAX − 1, MAX, never past MAX)
  it("TM21 recording stops by itself at max_audio_seconds from the API, not before", async () => {
    const m = installMic();
    const { press, transcribe } = setup();

    await press();
    await wait(MAX - 1);
    expect(m.recorder()?.state).toBe("recording");
    expect(transcribe).not.toHaveBeenCalled();

    await wait(1);
    expect(m.recorder()?.state).toBe("inactive");
    expect(transcribe).toHaveBeenCalledTimes(1);

    await wait(1);
    expect(transcribe).toHaveBeenCalledTimes(1);
  });

  // AC-7
  it("TM21 a room with max_audio_seconds = 5 stops at 5 seconds and shows / 0:05", async () => {
    const m = installMic();
    const { press, getByText, transcribe } = setup({ limits: { ...LIMITS, max_audio_seconds: 5 } as InputLimits });

    await press();
    expect(getByText(/\/ 0:05/)).toBeTruthy();
    await wait(5);

    expect(m.recorder()?.state).toBe("inactive");
    expect(transcribe).toHaveBeenCalledTimes(1);
  });

  // AC-8 (boundary: MIN − ε, MIN)
  it("TM07 a press shorter than min_audio_seconds is not sent and shows no alert", async () => {
    installMic();
    const { press, release, transcribe, queryByRole } = setup();

    await press();
    await act(async () => void (await vi.advanceTimersByTimeAsync(MIN * 1000 - 100)));
    await release();

    expect(transcribe).not.toHaveBeenCalled();
    expect(queryByRole("alert")).toBeNull();
  });

  it("TM07 a press of exactly min_audio_seconds is sent", async () => {
    installMic();
    const { talk, transcribe } = setup();

    await talk(MIN);

    expect(transcribe).toHaveBeenCalledTimes(1);
  });

  // AC-9
  it("TM07 a denied microphone shows an alert, does not record, and the button can be tried again", async () => {
    const m = installMic({ deny: true });
    const { press, release, mic, getByRole } = setup();

    await press();
    await release();

    expect(getByRole("alert").textContent).toBe(NO_MIC);
    expect(m.recorder()).toBeUndefined();
    expect(mic().disabled).toBe(false);
  });

  // AC-10
  it("TM07 a browser without MediaRecorder shows the same alert", async () => {
    installMic({ recorder: false });
    const { press, getByRole } = setup();

    await press();

    expect(getByRole("alert").textContent).toBe(NO_MIC);
  });

  // AC-11
  it("TM07 a failed transcription shows an alert and leaves the box unchanged", async () => {
    installMic();
    const transcribe = vi.fn(async () => {
      throw new Error("stt down");
    });
    const { input, talk, mic, getByRole } = setup({ transcribe });

    fireEvent.change(input, { target: { value: "ร่าง" } });
    await talk();

    expect(getByRole("alert").textContent).toBe("แปลงเสียงไม่สำเร็จ ลองพูดใหม่หรือพิมพ์แทนนะ");
    expect(input.value).toBe("ร่าง");
    expect(mic().disabled).toBe(false);
  });

  // AC-12
  it.each(["", "   "])("TM07 an empty transcript %j leaves the box unchanged and says nothing was heard", async (text) => {
    installMic();
    const { input, talk, getByText, queryByText } = setup({ text });

    await talk();

    expect(input.value).toBe("");
    expect(getByText("ไม่ได้ยินเสียง ลองพูดใหม่อีกทีนะ")).toBeTruthy();
    expect(queryByText(new RegExp(VOICE_NOTE))).toBeNull();
  });

  // AC-13
  it.each([
    ["voiceEnabled = false", { voiceEnabled: false }],
    ["limits without audio values", { limits: room.limits as InputLimits }],
  ])("TM07 %s: the mic does not record and says voice is not available yet", async (_name, opts) => {
    const m = installMic();
    const { press, getByText } = setup(opts);

    await press();

    expect(m.getUserMedia).not.toHaveBeenCalled();
    expect(getByText("ตอนนี้ยังพูดตอบไม่ได้ พิมพ์คำตอบมาก่อนนะ")).toBeTruthy();
  });

  // AC-16
  it("TM07 holding Space on the mic records and letting go stops, like the mouse", async () => {
    const m = installMic();
    const { mic, transcribe } = setup();

    fireEvent.keyDown(mic(), { key: " " });
    await settle();
    expect(m.recorder()?.state).toBe("recording");
    await wait(2);
    fireEvent.keyUp(mic(), { key: " " });
    await settle();

    expect(m.recorder()?.state).toBe("inactive");
    expect(transcribe).toHaveBeenCalledTimes(1);
  });

  it("TM07 the microphone is released after each recording", async () => {
    const m = installMic();
    const { talk } = setup();

    await talk();

    expect(m.track.stop).toHaveBeenCalled();
  });

  // AC-17
  it("TM06 with a voice transport the composer buttons are mic, attach and send only", () => {
    installMic();
    const { getAllByRole } = setup();

    const names = getAllByRole("button").map((b) => b.getAttribute("aria-label") ?? b.textContent);
    expect(names.sort()).toEqual([MIC, "ส่ง", "แนบรูป"].sort());
  });
});
