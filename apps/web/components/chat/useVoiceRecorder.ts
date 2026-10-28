"use client";

import { useEffect, useRef, useState } from "react";
import type { Transcribe } from "./types";

// Hold-to-talk recording (spec: specs/features/tutor/voice-input.md §2).
// Limits come from the API with the room, never hard-coded (TM-21).

export type VoiceState = "idle" | "starting" | "recording" | "transcribing";

export type VoiceProblem = "noMic" | "transcribeFailed" | "notHeard" | null;

type Options = {
  transcribe: Transcribe | undefined;
  maxSeconds: number;
  minSeconds: number;
  /** Called with the transcript; the caller puts it in the input box, never sends it. */
  onText: (text: string) => void;
};

export function useVoiceRecorder({ transcribe, maxSeconds, minSeconds, onText }: Options) {
  const [state, setState] = useState<VoiceState>("idle");
  const [elapsed, setElapsed] = useState(0);
  const [problem, setProblem] = useState<VoiceProblem>(null);

  const held = useRef(false);
  const recorder = useRef<MediaRecorder | null>(null);
  const stream = useRef<MediaStream | null>(null);
  const chunks = useRef<Blob[]>([]);
  const startedAt = useRef(0);
  const timers = useRef<ReturnType<typeof setTimeout>[]>([]);
  const abort = useRef<AbortController | null>(null);

  function clearTimers() {
    timers.current.forEach((id) => clearTimeout(id));
    timers.current = [];
  }

  function releaseMic() {
    stream.current?.getTracks().forEach((track) => track.stop());
    stream.current = null;
  }

  // Leaving the room: stop without transcribing, free the mic, cancel the request (AC-14).
  useEffect(
    () => () => {
      held.current = false;
      clearTimers();
      if (recorder.current) {
        recorder.current.onstop = null;
        if (recorder.current.state === "recording") recorder.current.stop();
      }
      releaseMic();
      abort.current?.abort();
    },
    [],
  );

  async function finish(type: string) {
    clearTimers();
    releaseMic();
    recorder.current = null;
    // A press shorter than the minimum is a slip: nothing is sent, nothing is said (AC-8).
    if (Date.now() - startedAt.current < minSeconds * 1000 || !transcribe) {
      setState("idle");
      return;
    }
    setState("transcribing");
    const controller = new AbortController();
    abort.current = controller;
    try {
      const { text } = await transcribe(new Blob(chunks.current, { type }), controller.signal);
      if (controller.signal.aborted) return;
      if (text.trim() === "") setProblem("notHeard");
      else onText(text.trim());
    } catch {
      if (!controller.signal.aborted) setProblem("transcribeFailed");
    }
    if (!controller.signal.aborted) setState("idle");
  }

  async function press() {
    if (state !== "idle") return;
    setProblem(null);
    if (typeof MediaRecorder === "undefined" || !navigator.mediaDevices?.getUserMedia) {
      setProblem("noMic");
      return;
    }
    held.current = true;
    setState("starting");
    let media: MediaStream;
    try {
      media = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch {
      held.current = false;
      setProblem("noMic");
      setState("idle");
      return;
    }
    stream.current = media;
    if (!held.current) {
      // Let go before the browser gave the mic.
      releaseMic();
      setState("idle");
      return;
    }
    const rec = new MediaRecorder(media);
    chunks.current = [];
    rec.ondataavailable = (e) => chunks.current.push(e.data);
    rec.onstop = () => void finish(rec.mimeType);
    recorder.current = rec;
    rec.start();
    startedAt.current = Date.now();
    setElapsed(0);
    setState("recording");
    for (let s = 1; s < maxSeconds; s++) timers.current.push(setTimeout(() => setElapsed(s), s * 1000));
    // Stops by itself at the limit, like letting go (AC-6).
    timers.current.push(setTimeout(stop, maxSeconds * 1000));
  }

  function stop() {
    if (recorder.current?.state === "recording") recorder.current.stop();
  }

  function release() {
    held.current = false;
    stop();
  }

  return { state, elapsed, problem, press, release, clearProblem: () => setProblem(null) };
}
