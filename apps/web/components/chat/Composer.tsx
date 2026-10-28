"use client";

import { useImperativeHandle, useRef, useState, type Ref } from "react";
import { roomStrings as t } from "./strings";
import type { InputLimits, SendPayload, Transcribe } from "./types";
import { useVoiceRecorder } from "./useVoiceRecorder";

// Spec §2: 1 MB = 1,048,576 bytes, must match the backend check.
const BYTES_PER_MB = 1024 * 1024;

type Props = {
  limits: InputLimits;
  onSend: (payload: SendPayload) => void;
  /** While the reply streams the draft stays editable but cannot be sent. */
  disabled?: boolean;
  /** False until the API takes photos (no /uploads yet · room-http.md §2): picking one only explains why. */
  imagesEnabled?: boolean;
  /** Speech → text. The mic button shows only when given (voice-input.md §2). */
  transcribe?: Transcribe;
  /** False until the API has /transcribe: pressing the mic only explains why (like `imagesEnabled`). */
  voiceEnabled?: boolean;
  /** Lets the room open the photo picker, e.g. for "ถ่ายใหม่" (ocr-confirm-card.md OQ 4). */
  handle?: Ref<ComposerHandle>;
};

export type ComposerHandle = { pickPhoto: () => void };

/**
 * Text + photo input of the tutor room. No answer choice buttons (TM-06).
 * Limits come from the API with the room data, never hard-coded.
 */
const clock = (seconds: number) => `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, "0")}`;

export function Composer({
  limits,
  onSend,
  disabled = false,
  imagesEnabled = true,
  handle,
  transcribe,
  voiceEnabled = true,
}: Props) {
  const [text, setText] = useState("");
  const [image, setImage] = useState<File | null>(null);
  const [imageError, setImageError] = useState<string | null>(null);
  const fileInput = useRef<HTMLInputElement>(null);
  const textArea = useRef<HTMLTextAreaElement>(null);
  // True while the text in the box came from speech, even after edits (voice-input.md AC-4, AC-5).
  const [fromVoice, setFromVoice] = useState(false);
  const [voiceNotYet, setVoiceNotYet] = useState(false);
  const { max_audio_seconds: maxAudio, min_audio_seconds: minAudio } = limits;
  // No audio limits from the API means no voice yet: nothing is hard-coded (OQ 3, 5).
  const canSpeak = voiceEnabled && maxAudio !== undefined && minAudio !== undefined;
  const voice = useVoiceRecorder({
    transcribe,
    maxSeconds: maxAudio ?? 0,
    minSeconds: minAudio ?? 0,
    onText: (spoken) => {
      setText((prev) => (prev.trim() === "" ? spoken : `${prev} ${spoken}`));
      setFromVoice(true);
      textArea.current?.focus();
    },
  });
  useImperativeHandle(handle, () => ({ pickPhoto: () => fileInput.current?.click() }), []);

  // Count characters, not UTF-16 units, like the backend.
  const tooLong = Array.from(text).length > limits.max_message_chars;
  const canSend = !disabled && !tooLong && (text.trim() !== "" || image !== null);

  function send() {
    if (!canSend) return;
    onSend({ text: text.trim() || null, image, ...(fromVoice && { voice: true as const }) });
    setText("");
    setFromVoice(false);
    setImage(null);
    setImageError(null);
  }

  function pick(file: File | undefined) {
    if (!file) return;
    if (!imagesEnabled) {
      setImageError(t.imagesNotYet);
    } else if (!file.type.startsWith("image/")) {
      setImageError(t.notImage);
    } else if (file.size > limits.max_image_mb * BYTES_PER_MB) {
      setImageError(t.imageTooBig(limits.max_image_mb));
    } else {
      setImage(file);
      setImageError(null);
    }
  }

  return (
    <div className="mx-auto w-full max-w-2xl">
      {image && (
        <div className="mb-2 flex items-center gap-2 text-xs text-zinc-600">
          <span className="rounded-lg border border-zinc-200 bg-zinc-50 px-3 py-1">📷 <span>{image.name}</span></span>
          <button
            type="button"
            aria-label={t.removePhoto}
            onClick={() => setImage(null)}
            className="rounded-full px-2 py-1 hover:bg-zinc-100"
          >
            ✕
          </button>
        </div>
      )}
      <div className="flex items-end gap-2 rounded-3xl border border-zinc-300 bg-white py-1.5 pl-4 pr-2">
        <textarea
          aria-label={t.inputLabel}
          placeholder={t.inputPlaceholder}
          rows={1}
          value={text}
          ref={textArea}
          onChange={(e) => {
            setText(e.target.value);
            if (e.target.value === "") setFromVoice(false);
          }}
          onKeyDown={(e) => {
            // Enter sends, Shift+Enter adds a line; skip while an IME is composing.
            if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
              e.preventDefault();
              send();
            }
          }}
          className="max-h-40 flex-1 resize-none bg-transparent py-1.5 text-sm outline-none"
        />
        <input
          ref={fileInput}
          type="file"
          accept="image/*"
          hidden
          onChange={(e) => {
            pick(e.target.files?.[0]);
            e.target.value = ""; // allow picking the same file again
          }}
        />
        {transcribe && (
          <button
            type="button"
            aria-label={t.mic}
            aria-pressed={voice.state === "recording"}
            disabled={voice.state === "transcribing"}
            onPointerDown={() => (canSpeak ? void voice.press() : setVoiceNotYet(true))}
            onPointerUp={voice.release}
            onPointerLeave={voice.release}
            onKeyDown={(e) => {
              if ((e.key === " " || e.key === "Enter") && !e.repeat) {
                e.preventDefault();
                if (canSpeak) void voice.press();
                else setVoiceNotYet(true);
              }
            }}
            onKeyUp={(e) => {
              if (e.key === " " || e.key === "Enter") voice.release();
            }}
            className={`flex h-9 w-9 items-center justify-center rounded-full border disabled:opacity-30 ${
              voice.state === "recording" ? "border-red-500 bg-red-50" : "border-zinc-300"
            }`}
          >
            🎤
          </button>
        )}
        <button
          type="button"
          aria-label={t.attach}
          onClick={() => fileInput.current?.click()}
          className="flex h-9 w-9 items-center justify-center rounded-full border border-zinc-300"
        >
          📷
        </button>
        <button
          type="button"
          aria-label={t.send}
          disabled={!canSend}
          onClick={send}
          className="flex h-9 w-9 items-center justify-center rounded-full bg-zinc-900 text-white disabled:opacity-30"
        >
          ↑
        </button>
      </div>
      {tooLong && <p role="alert" className="mt-1 pl-4 text-xs text-red-700">{t.tooLong(limits.max_message_chars)}</p>}
      {imageError && <p role="alert" className="mt-1 pl-4 text-xs text-red-700">{imageError}</p>}
      {voice.state === "recording" && (
        <p role="status" className="mt-1 pl-4 font-mono text-xs text-red-700">
          {t.micTimer(clock(voice.elapsed), clock(maxAudio ?? 0))}
        </p>
      )}
      {voice.state === "transcribing" && <p role="status" className="mt-1 pl-4 text-xs text-zinc-500">{t.transcribing}</p>}
      {fromVoice && text !== "" && <p className="mt-1 pl-4 text-xs text-zinc-400">{t.voiceNote}</p>}
      {voice.problem === "notHeard" && <p role="status" className="mt-1 pl-4 text-xs text-zinc-500">{t.notHeard}</p>}
      {(voice.problem === "noMic" || voice.problem === "transcribeFailed") && (
        <p role="alert" className="mt-1 pl-4 text-xs text-red-700">
          {voice.problem === "noMic" ? t.noMic : t.transcribeFailed}
        </p>
      )}
      {voiceNotYet && <p role="alert" className="mt-1 pl-4 text-xs text-red-700">{t.voiceNotYet}</p>}
    </div>
  );
}
