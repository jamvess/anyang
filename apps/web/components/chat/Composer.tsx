"use client";

import { useRef, useState } from "react";
import { roomStrings as t } from "./strings";
import type { InputLimits, SendPayload } from "./types";

// Spec §2: 1 MB = 1,048,576 bytes, must match the backend check.
const BYTES_PER_MB = 1024 * 1024;

type Props = {
  limits: InputLimits;
  onSend: (payload: SendPayload) => void;
  /** While the reply streams the draft stays editable but cannot be sent. */
  disabled?: boolean;
  /** False until the API takes photos (no /uploads yet · room-http.md §2): picking one only explains why. */
  imagesEnabled?: boolean;
};

/**
 * Text + photo input of the tutor room. No answer choice buttons (TM-06).
 * Limits come from the API with the room data, never hard-coded.
 */
export function Composer({ limits, onSend, disabled = false, imagesEnabled = true }: Props) {
  const [text, setText] = useState("");
  const [image, setImage] = useState<File | null>(null);
  const [imageError, setImageError] = useState<string | null>(null);
  const fileInput = useRef<HTMLInputElement>(null);

  // Count characters, not UTF-16 units, like the backend.
  const tooLong = Array.from(text).length > limits.max_message_chars;
  const canSend = !disabled && !tooLong && (text.trim() !== "" || image !== null);

  function send() {
    if (!canSend) return;
    onSend({ text: text.trim() || null, image });
    setText("");
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
          onChange={(e) => setText(e.target.value)}
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
    </div>
  );
}
