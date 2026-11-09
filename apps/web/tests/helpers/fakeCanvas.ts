import { fireEvent } from "@testing-library/react";
import { vi } from "vitest";

// jsdom cannot draw on a canvas and has no PointerEvent: these stand in for both
// (specs/features/tutor/answer-canvas.md §2 item 15 · no new dependency).

class FakePointerEvent extends MouseEvent {
  pointerType: string;
  isPrimary: boolean;
  pressure: number;
  pointerId: number;
  constructor(type: string, init: PointerEventInit = {}) {
    super(type, init);
    this.pointerType = init.pointerType ?? "mouse";
    this.isPrimary = init.isPrimary ?? true;
    this.pressure = init.pressure ?? 0.5;
    this.pointerId = init.pointerId ?? 1;
  }
}

/** Installs the stand-ins; `exported.size` is the size of the PNG that toBlob hands back. */
export function installFakeCanvas() {
  const exported = { size: 1000 };
  vi.stubGlobal("PointerEvent", FakePointerEvent);
  const ctx = new Proxy(
    {},
    {
      get: (_obj, key) => (key === "canvas" ? document.createElement("canvas") : () => {}),
      set: () => true,
    },
  );
  vi.spyOn(HTMLCanvasElement.prototype, "getContext").mockImplementation(
    () => ctx as unknown as CanvasRenderingContext2D,
  );
  vi.spyOn(HTMLCanvasElement.prototype, "toBlob").mockImplementation(function (cb: BlobCallback) {
    const blob = new Blob(["png"], { type: "image/png" });
    Object.defineProperty(blob, "size", { value: exported.size });
    cb(blob);
  });
  vi.spyOn(HTMLCanvasElement.prototype, "getBoundingClientRect").mockReturnValue({
    left: 0,
    top: 0,
    width: 600,
    height: 320,
    right: 600,
    bottom: 320,
    x: 0,
    y: 0,
    toJSON: () => ({}),
  } as DOMRect);
  return exported;
}

/** One stroke across the canvas with the given pointer type. */
export function draw(canvas: Element, pointerType = "mouse") {
  const at = (clientX: number, clientY: number) => ({ pointerType, isPrimary: true, pressure: 0.5, clientX, clientY });
  fireEvent.pointerDown(canvas, at(10, 10));
  fireEvent.pointerMove(canvas, at(40, 30));
  fireEvent.pointerUp(canvas, at(40, 30));
}
