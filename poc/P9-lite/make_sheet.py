"""Build the synthetic Thai course sheet of PoC P9-lite (specs/poc/README.md P9-lite).

Every line below was written for this PoC: no real course material, no student data (AI-07).
Run from apps/api:  uv run python ../../poc/P9-lite/make_sheet.py [--font <Thai .ttf>]
The PDF is gitignored: it embeds the font, and the default (Windows Leelawadee UI) may not be
redistributed. Off Windows, pass an open Thai font such as Sarabun (OFL).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pymupdf

HERE = Path(__file__).resolve().parent
OUT = HERE / "data" / "synthetic-sheet-calculus.pdf"
DEFAULT_FONT = Path("C:/Windows/Fonts/LeelawUI.ttf")  # tahoma.ttf extracts "-" as soft hyphen

PAGES: list[list[str]] = [
    [
        "เอกสารประกอบการเรียน (ชุดสังเคราะห์สำหรับทดสอบระบบ)",
        "วิชาแคลคูลัส 1 · บทที่ 2 ลิมิตและความต่อเนื่อง",
        "",
        "2.1 ลิมิตของฟังก์ชัน",
        "ถ้า f(x) เข้าใกล้ L เมื่อ x เข้าใกล้ a เราเขียนว่า lim_{x->a} f(x) = L",
        "ตัวอย่าง 2.1  lim_{x->2} (x^2 - 4)/(x - 2) = lim_{x->2} (x + 2) = 4",
        "ตัวอย่าง 2.2  lim_{x->0} sin(x)/x = 1",
        "",
        "2.2 ลิมิตทางเดียว",
        "lim_{x->a^-} f(x) และ lim_{x->a^+} f(x) ต้องเท่ากัน ลิมิตจึงมีค่า",
    ],
    [
        "บทที่ 3 อนุพันธ์",
        "",
        "3.1 นิยาม  f'(x) = lim_{h->0} (f(x+h) - f(x))/h",
        "3.2 กฎการหาอนุพันธ์",
        "  (x^n)' = n x^(n-1)      (sin x)' = cos x      (e^x)' = e^x",
        "  กฎผลคูณ (uv)' = u'v + uv'     กฎลูกโซ่ (f(g(x)))' = f'(g(x)) g'(x)",
        "ตัวอย่าง 3.1  d/dx (3x^2 + 5x) = 6x + 5",
        "ตัวอย่าง 3.2  d/dx sin(2x) = 2 cos(2x)",
    ],
    [
        "แบบฝึกหัดท้ายบท",
        "",
        "1. จงหา lim_{x->3} (x^2 - 9)/(x - 3)",
        "2. จงหาอนุพันธ์ของ f(x) = x^3 - 4x + 1",
        "3. จงหาอนุพันธ์ของ g(x) = x e^x",
        "4. จงหาอนุพันธ์ของ h(x) = (2x + 1)^5",
        "5. จงหาค่า x ที่ทำให้ f'(x) = 0 เมื่อ f(x) = x^2 - 6x",
    ],
]


def build(font: Path, out: Path = OUT) -> Path:
    doc = pymupdf.open()
    for lines in PAGES:
        page = doc.new_page()  # A4
        page.insert_font(fontname="th", fontfile=str(font))
        y = 72.0
        for line in lines:
            page.insert_text((60, y), line, fontname="th", fontsize=13)
            y += 22
    doc.subset_fonts()  # embed only the glyphs used, so the file stays small
    out.parent.mkdir(parents=True, exist_ok=True)
    doc.save(out, garbage=4, deflate=True)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--font", type=Path, default=DEFAULT_FONT, help="a TTF with Thai glyphs")
    args = parser.parse_args()
    if not args.font.exists():
        print(f"font not found: {args.font} (pass --font)", file=sys.stderr)
        return 2
    print(build(args.font))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
