"""Crop note-app screenshots (tablet UI around the page) down to the handwriting.

The S2 photos were written on tablets and captured as screenshots with the app's toolbar,
tabs and clock around the page (README "ใครเขียนอะไร"). This keeps only the handwriting
inside the page area of that device, plus a margin, so UI text is not part of the P1 input.

    cd apps/api
    uv run --with pillow --with numpy python ../../evals/handwriting/crop_screenshots.py \
        WRITER SRC DST

Prints the crop box of every file so it can be checked by eye.
"""

import sys
from pathlib import Path

import numpy as np
from PIL import Image

# Page area (x0, y0, x1, y1) per writer's device, measured on the 2026-10-19 screenshots.
# Everything outside it is app UI: toolbar, tabs, the gap to the next page, home indicator.
PAGE_AREA = {
    "friend1": (545, 330, 1615, 1620),  # 2160x1620
    "friend2": (470, 330, 1690, 1620),  # 2160x1620
    "may": (725, 310, 1640, 1240),  # 2360x1640
}
INK = 140  # luminance below this counts as handwriting (the page background is white)
MARGIN = 40


def crop_box(gray: np.ndarray, area: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = area
    ys, xs = np.nonzero(gray[y0:y1, x0:x1] < INK)
    if len(xs) == 0:
        raise ValueError("no handwriting found inside the page area")
    return (
        max(x0, x0 + int(xs.min()) - MARGIN),
        max(y0, y0 + int(ys.min()) - MARGIN),
        min(x1, x0 + int(xs.max()) + MARGIN),
        min(y1, y0 + int(ys.max()) + MARGIN),
    )


def main(writer: str, src: Path, dst: Path) -> None:
    image = Image.open(src).convert("RGB")
    box = crop_box(np.asarray(image.convert("L")), PAGE_AREA[writer])
    dst.parent.mkdir(parents=True, exist_ok=True)
    image.crop(box).save(dst)
    print(f"{src.name} -> {dst.name} box={box} size={box[2] - box[0]}x{box[3] - box[1]}")


if __name__ == "__main__":
    main(sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3]))
