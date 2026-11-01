import { vi } from "vitest";

// jsdom has no microphone: stand-ins for getUserMedia and MediaRecorder
// (spec: specs/features/tutor/voice-input.md §4).

export class FakeMediaRecorder {
  static instances: FakeMediaRecorder[] = [];
  state: "inactive" | "recording" = "inactive";
  mimeType = "audio/webm";
  ondataavailable: ((e: { data: Blob }) => void) | null = null;
  onstop: (() => void) | null = null;
  start = vi.fn(() => {
    this.state = "recording";
  });
  stop = vi.fn(() => {
    if (this.state === "inactive") return;
    this.state = "inactive";
    this.ondataavailable?.({ data: new Blob(["voice"], { type: this.mimeType }) });
    this.onstop?.();
  });
  constructor(readonly stream: unknown) {
    FakeMediaRecorder.instances.push(this);
  }
}

/** Installs a microphone that grants (or denies) access. Returns the track to check it was stopped. */
export function installMic({ deny = false, recorder = true } = {}) {
  FakeMediaRecorder.instances = [];
  const track = { stop: vi.fn() };
  const stream = { getTracks: () => [track] };
  const getUserMedia = vi.fn(async () => {
    if (deny) throw Object.assign(new Error("denied"), { name: "NotAllowedError" });
    return stream;
  });
  Object.defineProperty(navigator, "mediaDevices", { configurable: true, value: { getUserMedia } });
  if (recorder) vi.stubGlobal("MediaRecorder", FakeMediaRecorder);
  else vi.stubGlobal("MediaRecorder", undefined);
  return { getUserMedia, track, recorder: () => FakeMediaRecorder.instances.at(-1) };
}
