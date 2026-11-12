"use client";

import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { roomStrings as t } from "./strings";

/** Longer side of a sent photo's thumbnail. A UI value, not a learning-model one (answer-canvas.md §2 D). */
export const THUMBNAIL_MAX_PX = 160;

/**
 * A photo sent in this session, shown small in the user's bubble; pressing it opens the
 * full image over the page (answer-canvas.md §2 D items 21–25 · May 12 Nov).
 */
export function Thumbnail({ src, name }: { src: string; name: string }) {
  const [open, setOpen] = useState(false);
  const opener = useRef<HTMLAnchorElement>(null);
  const closer = useRef<HTMLButtonElement>(null);

  function close() {
    setOpen(false);
    opener.current?.focus();
  }

  useEffect(() => {
    if (!open) return;
    closer.current?.focus();
    // Esc closes wherever focus is (a click on the image or backdrop moves it to body · self-review PR #124).
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") close();
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [open]);

  return (
    <>
      {/* A link, not a button: the room keeps no buttons besides its inputs (TM-06 · RoomPagePhoto AC-19 · May 12 Nov). */}
      <a
        ref={opener}
        href={src}
        aria-label={t.thumbnailOpen(name)}
        onClick={(e) => {
          e.preventDefault();
          setOpen(true);
        }}
        className="my-1 inline-block rounded-lg border border-zinc-200 bg-zinc-50 p-1"
      >
        {/* eslint-disable-next-line @next/next/no-img-element -- a local object URL, next/image cannot optimise it */}
        <img src={src} alt={t.thumbnailAlt(name)} style={{ maxWidth: `${THUMBNAIL_MAX_PX}px`, maxHeight: `${THUMBNAIL_MAX_PX}px`, objectFit: "contain" }} />
      </a>
      {/* The name stays readable under the picture (chat-room-ui.md AC-6 · without the 📷 box, §2 D item 21). */}
      <p className="text-xs text-zinc-500">{name}</p>
      {open &&
        // On body, not inside the chat log: the log is a live region and would announce it as a message.
        createPortal(
          <div
            role="dialog"
            aria-modal="true"
            aria-label={t.thumbnailAlt(name)}
            tabIndex={-1}
            onKeyDown={(e) => {
              // The close button is the only control: Tab stays on it, so focus never reaches the page behind.
              if (e.key === "Tab") {
                e.preventDefault();
                closer.current?.focus();
              }
            }}
            className="fixed inset-0 z-50 flex flex-col items-center justify-center gap-3 bg-black/70 p-6"
          >
            {/* eslint-disable-next-line @next/next/no-img-element -- same object URL as the thumbnail */}
            <img src={src} alt={t.thumbnailAlt(name)} className="max-h-[85vh] max-w-full rounded-lg bg-white object-contain" />
            <button ref={closer} type="button" onClick={close} className="rounded-lg bg-white px-4 py-1.5 text-sm text-zinc-800">
              {t.thumbnailClose}
            </button>
          </div>,
          document.body,
        )}
    </>
  );
}
