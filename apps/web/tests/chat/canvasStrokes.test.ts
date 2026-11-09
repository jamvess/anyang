import { describe, expect, it } from "vitest";
import {
  ERASER_WIDTH_PX,
  PEN_WIDTH_PX,
  accepts,
  canUndo,
  clear,
  containRect,
  drawScene,
  emptyScene,
  endStroke,
  extendStroke,
  isEmpty,
  setBackground,
  startStroke,
  strokeWidth,
  undo,
  type Background,
  type PointerInfo,
  type Scene,
} from "@/components/chat/canvasStrokes";

// Spec: specs/features/tutor/answer-canvas.md §2 items 5-8, 14 · AC-4 to AC-8.

function pointer(pointerType: string, x = 0, y = 0, extra: Partial<PointerInfo> = {}): PointerInfo {
  return { pointerType, isPrimary: true, pressure: 0.5, x, y, ...extra };
}

function stroke(scene: Scene, type = "mouse", tool: "pen" | "eraser" = "pen"): Scene {
  let s = startStroke(scene, tool, pointer(type, 1, 1));
  s = extendStroke(s, pointer(type, 2, 3));
  s = extendStroke(s, pointer(type, 4, 5));
  return endStroke(s);
}

const PHOTO: Background = { image: {} as CanvasImageSource, width: 400, height: 200 };
const OTHER: Background = { image: {} as CanvasImageSource, width: 100, height: 100 };

describe("canvasStrokes", () => {
  it("AC-4 a stroke keeps its points in order; undo removes it; clear empties and drops history", () => {
    const one = stroke(emptyScene());

    expect(one.strokes).toHaveLength(1);
    expect(one.strokes[0].points).toEqual([
      { x: 1, y: 1 },
      { x: 2, y: 3 },
      { x: 4, y: 5 },
    ]);
    expect(isEmpty(one)).toBe(false);
    expect(canUndo(one)).toBe(true);

    const undone = undo(one);
    expect(undone.strokes).toHaveLength(0);
    expect(isEmpty(undone)).toBe(true);

    const cleared = clear(stroke(stroke(emptyScene())));
    expect(isEmpty(cleared)).toBe(true);
    expect(canUndo(cleared)).toBe(false);
    expect(undo(cleared).strokes).toHaveLength(0);
  });

  it("AC-5 palm rejection: touch draws until a pen has drawn; mouse always; never a non-primary pointer", () => {
    const fresh = emptyScene();
    expect(accepts(fresh, pointer("touch"))).toBe(true);
    expect(accepts(fresh, pointer("mouse"))).toBe(true);
    expect(accepts(fresh, pointer("touch", 0, 0, { isPrimary: false }))).toBe(false);

    const afterPen = stroke(fresh, "pen");
    expect(accepts(afterPen, pointer("touch"))).toBe(false);
    expect(accepts(afterPen, pointer("pen"))).toBe(true);
    expect(accepts(afterPen, pointer("mouse"))).toBe(true);
    // Undo does not forget the pen: the palm is still on the screen.
    expect(accepts(undo(afterPen), pointer("touch"))).toBe(false);
  });

  it.each([
    ["pen", 0.5, 1],
    ["pen", 1.0, 2],
    ["pen", 0.1, 0.5],
    ["mouse", 1.0, 1],
    ["mouse", 0, 1],
    ["touch", 0.9, 1],
  ])("AC-6 %s with pressure %s draws %s × PEN_WIDTH_PX", (type, pressure, factor) => {
    expect(strokeWidth("pen", pointer(type, 0, 0, { pressure }))).toBeCloseTo(PEN_WIDTH_PX * factor);
  });

  it("AC-6 the eraser has its own width whatever the pointer", () => {
    expect(strokeWidth("eraser", pointer("pen", 0, 0, { pressure: 1 }))).toBe(ERASER_WIDTH_PX);
    expect(strokeWidth("eraser", pointer("mouse"))).toBe(ERASER_WIDTH_PX);
  });

  it("AC-7 a new background replaces the old one, and undo brings the old one back", () => {
    const first = setBackground(emptyScene(), PHOTO);
    expect(isEmpty(first)).toBe(false);

    const second = setBackground(first, OTHER);
    expect(second.background).toBe(OTHER);
    expect(undo(second).background).toBe(PHOTO);
    expect(undo(undo(second)).background).toBeNull();
  });

  it("AC-8 containRect fits without stretching, centred", () => {
    // 400×200 into 300×300: scale 0.75 → 300×150, centred vertically.
    expect(containRect(400, 200, 300, 300)).toEqual({ x: 0, y: 75, width: 300, height: 150 });
    // 100×400 into 300×200: scale 0.5 → 50×200, centred horizontally.
    expect(containRect(100, 400, 300, 200)).toEqual({ x: 125, y: 0, width: 50, height: 200 });
  });

  it("AC-8 drawScene: white, background (contain), then strokes on their own layer; eraser cuts the layer only", () => {
    const base = recorder();
    const layer = recorder();
    const scene = stroke(stroke(setBackground(emptyScene(), PHOTO)), "mouse", "eraser");

    drawScene(base.ctx, layer.ctx, scene, { width: 300, height: 300 });

    // Base: white first, then the background where containRect puts it, then the layer.
    expect(base.calls[0]).toEqual(["fillStyle", "#ffffff"]);
    expect(base.calls).toContainEqual(["fillRect", 0, 0, 300, 300]);
    expect(base.calls).toContainEqual(["drawImage", PHOTO.image, 0, 75, 300, 150]);
    expect(base.calls[base.calls.length - 1][0]).toBe("drawImage"); // the stroke layer, last
    // Layer: the pen stroke draws normally, the eraser stroke uses destination-out.
    const modes = layer.calls.filter(([name]) => name === "globalCompositeOperation").map(([, v]) => v);
    expect(modes).toEqual(["source-over", "destination-out"]);
    // The base never erases: the background stays under erased strokes.
    expect(base.calls.some(([name, v]) => name === "globalCompositeOperation" && v === "destination-out")).toBe(false);
  });
});

/** A CanvasRenderingContext2D stand-in that records property sets and method calls in order. */
function recorder() {
  const calls: unknown[][] = [];
  const canvas = {} as HTMLCanvasElement;
  const target: Record<string, unknown> = { canvas };
  const ctx = new Proxy(target, {
    get(obj, key: string) {
      if (key in obj) return obj[key];
      return (...args: unknown[]) => {
        calls.push([key, ...args]);
      };
    },
    set(obj, key: string, value) {
      calls.push([key, value]);
      obj[`_${key}`] = value;
      return true;
    },
  }) as unknown as CanvasRenderingContext2D;
  return { ctx, calls };
}

describe("canvasStrokes · added after /code-review (9 Nov)", () => {
  it("TM06 eraser strokes alone leave the canvas empty (nothing to send)", () => {
    const erased = stroke(emptyScene(), "mouse", "eraser");

    expect(isEmpty(erased)).toBe(true);
    expect(isEmpty(stroke(erased))).toBe(false);
  });
});
