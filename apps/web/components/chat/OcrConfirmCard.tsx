"use client";

import { useState } from "react";
import { Tex } from "@/components/math/Tex";
import { roomStrings as t } from "./strings";

// Spec: specs/features/check/ocr-confirm-card.md · payload: api.md "SSE events" ocr_preview.

/**
 * Hand-written until the API schema has `OcrPreviewEvent` (spec OQ 5); then use
 * `components["schemas"]["OcrPreviewEvent"]` like ProblemCard. `latex` is plain LaTeX without $ (OQ 6).
 */
export type OcrPreviewData = { lines: { latex: string; confidence: number }[] };

/** pending: waits for the user · sending: the confirm reply streams · confirmed / retaken: locked. */
export type OcrStatus = "pending" | "sending" | "confirmed" | "retaken";

type Props = {
  preview: OcrPreviewData;
  status: OcrStatus;
  onConfirm: (lines: string[]) => void;
  onRetake: () => void;
};

const BUTTON = "rounded-lg border border-zinc-300 px-3 py-1 text-xs disabled:opacity-40";

/**
 * "อ่านได้แบบนี้ ถูกไหม" card (wireframe S21). Shown for every photo answer; confidence is
 * never read (AM-02 · P1). Lines can be edited one at a time, not added or removed (OQ 2, 3).
 */
export function OcrConfirmCard({ preview, status, onConfirm, onRetake }: Props) {
  const [lines, setLines] = useState(() => preview.lines.map((l) => l.latex));
  const [edited, setEdited] = useState<boolean[]>(() => preview.lines.map(() => false));
  const [editing, setEditing] = useState<{ index: number; draft: string } | null>(null);

  if (lines.length === 0) return null;

  const locked = status === "confirmed" || status === "retaken";
  const sending = status === "sending";

  function save() {
    if (!editing || editing.draft.trim() === "") return;
    const { index, draft } = editing;
    setLines((prev) => prev.map((l, i) => (i === index ? draft : l)));
    setEdited((prev) => prev.map((e, i) => (i === index ? e || draft !== lines[index] : e)));
    setEditing(null);
  }

  function edit(index: number) {
    // One line at a time: the open line is saved first, or dropped when blank (OQ 2).
    if (editing && editing.draft.trim() !== "") save();
    setEditing({ index, draft: lines[index] });
  }

  return (
    <div role="region" aria-label={t.ocrCard} className="mt-4 rounded-xl border border-zinc-200 bg-white px-4 py-3 text-sm">
      <p className="mb-2">{t.ocrIntro}</p>
      <ol>
        {lines.map((latex, i) => {
          const n = i + 1;
          const open = !locked && editing?.index === i;
          return (
            <li key={i} data-ocr-line={n} className="flex items-center gap-3 py-1">
              <span className="w-4 shrink-0 font-mono text-xs text-zinc-400">{n}</span>
              {open ? (
                <div className="flex-1">
                  <input
                    type="text"
                    aria-label={t.ocrLine(n)}
                    value={editing.draft}
                    autoFocus
                    onChange={(e) => setEditing({ index: i, draft: e.target.value })}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && !e.nativeEvent.isComposing) {
                        e.preventDefault();
                        save();
                      } else if (e.key === "Escape") {
                        setEditing(null);
                      }
                    }}
                    className="w-full rounded-lg border border-zinc-300 px-2 py-1 font-mono text-xs"
                  />
                  <Tex math={editing.draft} />
                  <div className="mt-1 flex gap-2">
                    <button type="button" onClick={save} disabled={editing.draft.trim() === ""} className={BUTTON}>
                      {t.ocrSave}
                    </button>
                    <button type="button" onClick={() => setEditing(null)} className={BUTTON}>
                      {t.ocrCancel}
                    </button>
                  </div>
                </div>
              ) : (
                <>
                  <span className="flex-1">
                    <Tex math={latex} />
                    {edited[i] && (
                      <span className="ml-2 rounded bg-zinc-100 px-1.5 py-0.5 font-mono text-[10px] text-zinc-500">
                        {t.ocrEdited}
                      </span>
                    )}
                  </span>
                  {!locked && (
                    <button
                      type="button"
                      aria-label={t.ocrEditLine(n)}
                      disabled={sending}
                      onClick={() => edit(i)}
                      className="text-xs text-zinc-400 hover:text-zinc-700 disabled:opacity-40"
                    >
                      {t.ocrEdit}
                    </button>
                  )}
                </>
              )}
            </li>
          );
        })}
      </ol>
      {locked ? (
        <p className="mt-2 text-xs text-zinc-400">{status === "confirmed" ? t.ocrConfirmed : t.ocrRetaken}</p>
      ) : (
        <div className="mt-3 flex gap-2">
          <button
            type="button"
            disabled={sending || editing !== null}
            onClick={() => onConfirm(lines)}
            className={`${BUTTON} border-zinc-900 bg-zinc-900 text-white`}
          >
            {t.ocrConfirm}
          </button>
          <button type="button" disabled={sending} onClick={onRetake} className={BUTTON}>
            {t.ocrRetake}
          </button>
        </div>
      )}
    </div>
  );
}
