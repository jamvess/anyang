"use client";

import { useEffect, useRef, useState, type PointerEvent as ReactPointerEvent } from "react";
import {
  CANVAS_HEIGHT_PX,
  canUndo,
  clear,
  drawScene,
  emptyScene,
  endStroke,
  extendStroke,
  isEmpty,
  setBackground,
  startStroke,
  undo,
  type Background,
  type PointerInfo,
  type Scene,
  type Tool,
} from "./canvasStrokes";
import { Tex } from "@/components/math/Tex";
import { roomStrings as t } from "./strings";
import type { SendPayload } from "./types";

// Spec: specs/features/tutor/answer-canvas.md · provisional design until May decides (§10).

const MB = 1024 * 1024;

/** The browser's own image decoding; tests pass a fake because jsdom cannot decode images. */
async function decodeImage(file: File): Promise<Background> {
  const bitmap = await createImageBitmap(file);
  return { image: bitmap, width: bitmap.width, height: bitmap.height };
}

/** A drawing area under the latest problem card; what is drawn is sent like a photo. */
export function AnswerCanvas({
  onSend,
  disabled,
  maxImageMb,
  loadImage = decodeImage,
  problemLatex,
}: {
  onSend: (payload: SendPayload) => void | Promise<void>;
  /** The room is waiting for a reply: nothing can be sent. */
  disabled: boolean;
  maxImageMb: number;
  loadImage?: (file: File) => Promise<Background>;
  /** The problem this canvas answers, shown small on top (§2 item 17). */
  problemLatex?: string;
}) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const layerRef = useRef<HTMLCanvasElement | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);
  const [initial] = useState(emptyScene);
  const sceneRef = useRef<Scene>(initial);
  const [scene, setScene] = useState<Scene>(initial);
  const [tool, setTool] = useState<Tool>("pen");
  const [sent, setSent] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [width, setWidth] = useState(0);

  /** One place that changes the scene, so pointer handlers read the latest one synchronously. */
  function update(change: (s: Scene) => Scene): Scene {
    const next = change(sceneRef.current);
    if (next !== sceneRef.current) {
      sceneRef.current = next;
      setScene(next);
    }
    return next;
  }

  // Size the drawing surface to the card width, sharp on high-density screens (§2 item 4).
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const measure = () => setWidth(canvas.getBoundingClientRect().width);
    measure();
    if (typeof ResizeObserver === "undefined") return;
    const observer = new ResizeObserver(measure);
    observer.observe(canvas);
    return () => observer.disconnect();
  }, []);

  function paint(current: Scene) {
    const canvas = canvasRef.current;
    if (!canvas || width === 0) return;
    const ratio = window.devicePixelRatio || 1;
    const pixelWidth = Math.round(width * ratio);
    const pixelHeight = Math.round(CANVAS_HEIGHT_PX * ratio);
    if (canvas.width !== pixelWidth) canvas.width = pixelWidth;
    if (canvas.height !== pixelHeight) canvas.height = pixelHeight;
    const layer = (layerRef.current ??= document.createElement("canvas"));
    layer.width = pixelWidth;
    layer.height = pixelHeight;
    const base = canvas.getContext("2d");
    const ink = layer.getContext("2d");
    if (!base || !ink) return;
    base.setTransform(ratio, 0, 0, ratio, 0, 0);
    ink.setTransform(ratio, 0, 0, ratio, 0, 0);
    drawScene(base, ink, current, { width, height: CANVAS_HEIGHT_PX });
  }

  useEffect(() => {
    paint(scene);
    // eslint-disable-next-line react-hooks/exhaustive-deps -- paint reads refs; redraw on scene or size
  }, [scene, width]);

  function info(e: ReactPointerEvent<HTMLCanvasElement>): PointerInfo {
    const rect = e.currentTarget.getBoundingClientRect();
    return {
      pointerType: e.pointerType,
      isPrimary: e.isPrimary,
      pressure: e.pressure,
      x: e.clientX - rect.left,
      y: e.clientY - rect.top,
    };
  }

  function onPointerDown(e: ReactPointerEvent<HTMLCanvasElement>) {
    const before = sceneRef.current;
    const after = update((s) => startStroke(s, tool, info(e)));
    if (after === before) return; // a palm, or not the primary pointer (§2 item 6)
    e.currentTarget.setPointerCapture?.(e.pointerId);
    setSent(false);
    setError(null);
  }

  function onPointerMove(e: ReactPointerEvent<HTMLCanvasElement>) {
    if (sceneRef.current.current) update((s) => extendStroke(s, info(e)));
  }

  function onPointerEnd() {
    update(endStroke);
  }

  async function onPickImage(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file) return;
    if (!file.type.startsWith("image/")) {
      setError(t.canvasNotImage);
      return;
    }
    try {
      const background = await loadImage(file);
      update((s) => setBackground(s, background));
      setSent(false);
      setError(null);
    } catch {
      setError(t.canvasNotImage);
    }
  }

  function exportPng(): Promise<Blob | null> {
    const canvas = canvasRef.current;
    if (!canvas) return Promise.resolve(null);
    paint(sceneRef.current); // what is on screen now
    return new Promise((resolve) => canvas.toBlob(resolve, "image/png"));
  }

  async function onSendClick() {
    const blob = await exportPng();
    if (!blob) return;
    if (blob.size > maxImageMb * MB) {
      setError(t.imageTooBig(maxImageMb));
      return;
    }
    setError(null);
    setSent(true);
    await onSend({ text: null, image: new File([blob], t.canvasFileName, { type: "image/png" }) });
  }

  const empty = isEmpty(scene);
  const button =
    "rounded-lg border border-zinc-200 px-3 py-1.5 text-sm text-zinc-700 hover:bg-zinc-50 disabled:cursor-not-allowed disabled:opacity-40";

  return (
    <section role="form" aria-label={t.canvas} className="mt-4 rounded-xl border border-zinc-200 bg-white p-3">
      {problemLatex && (
        <div className="mb-2 flex items-center gap-2 text-sm text-zinc-700">
          <span className="font-mono text-xs uppercase tracking-wide text-zinc-400">{t.problem}</span>
          <Tex math={problemLatex} />
        </div>
      )}
      <canvas
        ref={canvasRef}
        aria-label={t.canvasLabel}
        className="block w-full cursor-crosshair rounded-lg border border-dashed border-zinc-200"
        style={{ height: CANVAS_HEIGHT_PX, touchAction: "none" }}
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerEnd}
        onPointerCancel={onPointerEnd}
        onPointerLeave={onPointerEnd}
      />
      <div className="mt-2 flex flex-wrap items-center gap-2">
        <button type="button" aria-label={t.canvasPen} aria-pressed={tool === "pen"} className={button} onClick={() => setTool("pen")}>
          ✏️ {t.canvasPen}
        </button>
        <button type="button" aria-label={t.canvasEraser} aria-pressed={tool === "eraser"} className={button} onClick={() => setTool("eraser")}>
          🧽 {t.canvasEraser}
        </button>
        <button type="button" aria-label={t.canvasUndo} className={button} disabled={!canUndo(scene)} onClick={() => update(undo)}>
          ↶ {t.canvasUndo}
        </button>
        <button type="button" aria-label={t.canvasClear} className={button} disabled={empty} onClick={() => update(clear)}>
          {t.canvasClear}
        </button>
        <button type="button" aria-label={t.canvasImage} className={button} onClick={() => fileRef.current?.click()}>
          🖼️ {t.canvasImage}
        </button>
        <input ref={fileRef} type="file" accept="image/*" hidden onChange={onPickImage} />
        <button
          type="button"
          aria-label={t.canvasSend}
          className="ml-auto rounded-lg bg-zinc-900 px-4 py-1.5 text-sm text-white hover:bg-zinc-700 disabled:cursor-not-allowed disabled:opacity-40"
          disabled={empty || disabled}
          onClick={() => void onSendClick()}
        >
          {t.canvasSend}
        </button>
      </div>
      {error && (
        <p role="alert" className="mt-2 text-xs text-red-700">
          {error}
        </p>
      )}
      {sent && !error && <p className="mt-2 text-xs text-zinc-500">{t.canvasSent}</p>}
    </section>
  );
}
