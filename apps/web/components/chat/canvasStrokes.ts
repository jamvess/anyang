// The drawing on the answer canvas as plain data, and how it is painted
// (specs/features/tutor/answer-canvas.md §2 items 5-8, 14). Pure: no DOM, so it is testable.

/** UI values of the canvas (not learning-model numbers). */
export const CANVAS_HEIGHT_PX = 320;
export const PEN_WIDTH_PX = 2.5;
export const ERASER_WIDTH_PX = 18;
// Pen pressure 0.5 draws PEN_WIDTH_PX; lighter or heavier scales it within these bounds.
const PRESSURE_SCALE = 2;
const MIN_PRESSURE_FACTOR = 0.5;
const MAX_PRESSURE_FACTOR = 2;
const INK = "#18181b";
const PAPER = "#ffffff";

export type Tool = "pen" | "eraser";
export type PointerInfo = { pointerType: string; isPrimary: boolean; pressure: number; x: number; y: number };
export type Point = { x: number; y: number };
export type Stroke = { tool: Tool; width: number; points: Point[] };
/** An image under the strokes, with its natural size. */
export type Background = { image: CanvasImageSource; width: number; height: number };

type Snapshot = { strokes: Stroke[]; background: Background | null };

export type Scene = {
  strokes: Stroke[];
  background: Background | null;
  /** The stroke being drawn now, not yet in `strokes`. */
  current: Stroke | null;
  /** A pen has drawn here: from now on touch is a palm resting on the screen (§2 item 6). */
  penSeen: boolean;
  /** States before each finished action, for undo. */
  history: Snapshot[];
};

export function emptyScene(): Scene {
  return { strokes: [], background: null, current: null, penSeen: false, history: [] };
}

/** Whether this pointer may draw: the primary one only, and no touch once a pen has drawn. */
export function accepts(scene: Scene, p: PointerInfo): boolean {
  if (!p.isPrimary) return false;
  return !(p.pointerType === "touch" && scene.penSeen);
}

export function strokeWidth(tool: Tool, p: PointerInfo): number {
  if (tool === "eraser") return ERASER_WIDTH_PX;
  if (p.pointerType !== "pen") return PEN_WIDTH_PX;
  const factor = Math.min(MAX_PRESSURE_FACTOR, Math.max(MIN_PRESSURE_FACTOR, p.pressure * PRESSURE_SCALE));
  return PEN_WIDTH_PX * factor;
}

export function startStroke(scene: Scene, tool: Tool, p: PointerInfo): Scene {
  if (!accepts(scene, p)) return scene;
  return {
    ...scene,
    current: { tool, width: strokeWidth(tool, p), points: [{ x: p.x, y: p.y }] },
    penSeen: scene.penSeen || p.pointerType === "pen",
  };
}

export function extendStroke(scene: Scene, p: PointerInfo): Scene {
  if (!scene.current || !accepts(scene, p)) return scene;
  return { ...scene, current: { ...scene.current, points: [...scene.current.points, { x: p.x, y: p.y }] } };
}

export function endStroke(scene: Scene): Scene {
  if (!scene.current) return scene;
  return {
    ...scene,
    history: [...scene.history, snapshot(scene)],
    strokes: [...scene.strokes, scene.current],
    current: null,
  };
}

export function undo(scene: Scene): Scene {
  const previous = scene.history[scene.history.length - 1];
  if (!previous) return scene;
  return { ...scene, ...previous, current: null, history: scene.history.slice(0, -1) };
}

/** Everything goes, history too: undo after clear brings nothing back (AC-4). */
export function clear(scene: Scene): Scene {
  return { ...emptyScene(), penSeen: scene.penSeen };
}

export function setBackground(scene: Scene, background: Background): Scene {
  return { ...scene, history: [...scene.history, snapshot(scene)], background };
}

export function isEmpty(scene: Scene): boolean {
  return scene.strokes.length === 0 && scene.background === null && scene.current === null;
}

export function canUndo(scene: Scene): boolean {
  return scene.history.length > 0;
}

/** Where an image of w×h goes in a box of boxW×boxH: as large as fits, not stretched, centred. */
export function containRect(w: number, h: number, boxW: number, boxH: number) {
  const scale = Math.min(boxW / w, boxH / h);
  const width = w * scale;
  const height = h * scale;
  return { x: (boxW - width) / 2, y: (boxH - height) / 2, width, height };
}

/**
 * Paints the scene: the strokes go on `layer` (so the eraser cuts strokes only), then `base`
 * gets white paper, the background image and the layer on top.
 */
export function drawScene(
  base: CanvasRenderingContext2D,
  layer: CanvasRenderingContext2D,
  scene: Scene,
  size: { width: number; height: number },
): void {
  layer.clearRect(0, 0, size.width, size.height);
  for (const stroke of scene.current ? [...scene.strokes, scene.current] : scene.strokes) {
    layer.globalCompositeOperation = stroke.tool === "eraser" ? "destination-out" : "source-over";
    layer.lineWidth = stroke.width;
    layer.lineCap = "round";
    layer.lineJoin = "round";
    layer.strokeStyle = INK;
    layer.beginPath();
    const [first, ...rest] = stroke.points;
    layer.moveTo(first.x, first.y);
    // A single tap still leaves a dot.
    for (const point of rest.length > 0 ? rest : [first]) layer.lineTo(point.x, point.y);
    layer.stroke();
  }

  base.fillStyle = PAPER;
  base.fillRect(0, 0, size.width, size.height);
  if (scene.background) {
    const { image, width, height } = scene.background;
    const r = containRect(width, height, size.width, size.height);
    base.drawImage(image, r.x, r.y, r.width, r.height);
  }
  base.drawImage(layer.canvas, 0, 0, size.width, size.height);
}

function snapshot(scene: Scene): Snapshot {
  return { strokes: scene.strokes, background: scene.background };
}
