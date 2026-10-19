# ร่างเฉลย LaTeX ลายมือ · May

ไฟล์ชั่วคราว พอกรอกครบ Claude จะแปลงเป็น `labels.jsonl` แล้วลบไฟล์นี้ · คู่มือเต็ม: `evals/README.md` หัวข้อ "คู่มือ label ลายมือ · P1"

**วิธีกรอก**
- พิมพ์ในกล่อง ```` ``` ```` ใต้แต่ละรูป: **1 บรรทัดในรูป = 1 บรรทัดในกล่อง** เรียงบนลงล่าง
- พิมพ์ตามที่เขียน แม้จะผิด · ข้ามบรรทัดที่ขีดฆ่าและบรรทัดที่เป็นคำพูดล้วน · ตัด "ดังนั้น", "∴", `⇒` ต้นบรรทัด
- ไม่ใส่ `$` · พิมพ์ `\` ตัวเดียวได้เลย (ไม่ต้องพิมพ์ซ้อนสองตัวแบบใน JSON)
- อ่านไม่ออกจริงๆ: ใส่ `\?` แทนตัวนั้น แล้วใส่เลขบรรทัดในช่อง `อ่านไม่ออก` เช่น `2, 4` · ถ้าไม่มีใส่ `-`
- ดูหน้าตาที่ render แล้วเทียบกับรูป: บอก Claude ว่า "preview" หรือรันเอง `python evals/handwriting/raw/preview.py` แล้วเปิด `evals/handwriting/raw/preview.html`

**รูปแบบที่ใช้บ่อย:** `\frac{a}{b}` · `x^{2}` · `\sqrt{x}` · `\sin(x)` · `\left|x\right|` · `\lim_{x \to 0}` · `\frac{dy}{dx}` · `f'(x)` · `\infty` · `\cdot`
ight|` · `\lim_{x 	o 0}` · `rac{dy}{dx}` · `f'(x)` · `\infty` · `\cdot`

---

## hw_001 · P01 · w01 · stylus
รูป: `raw/hw_001.jpg` · โจทย์: `\text{แยกตัวประกอบ } x^{3}-x`

```
x^{3}-x
=x(x^{2}-1)
```

อ่านไม่ออก: -

## hw_002 · P05 · w01 · stylus
รูป: `raw/hw_002.jpg` · โจทย์: `\lim_{x \to 2} \frac{x^{2}-4}{x^{2}-3x+2}`

```
\lim_{x \to 2} \frac{x^{2}-4}{x^{2}-3x+2}
=\lim_{x \to 2} \frac{-4}{-3x+2}
=\frac{-4}{-6+2}
=1
```

อ่านไม่ออก: -

## hw_003 · P07 · w01 · stylus
รูป: `raw/hw_003.jpg` · โจทย์: `\lim_{x \to \infty} \frac{3x^{2}-x}{2x^{2}+5}`

```
\lim_{x \to \infty} \frac{3x^{2}-x}{2x^{2}+5}
=\lim_{x \to \infty} \frac{3-\frac{1}{x}}{2+\frac{5}{x^{2}}}
=\frac{3-0}{2+0}
=\frac{3}{2}
```

อ่านไม่ออก: -

## hw_004 · P12 · w01 · stylus
รูป: `raw/hw_004.jpg` · โจทย์: `\text{หา } \frac{dy}{dx} \text{ จาก } x^{2}+y^{2}=4xy`

```
x^{2}+y^{2}=4xy
2x+2y\frac{dy}{dx}=4y+4x\frac{dy}{dx}
2y\frac{dy}{dx}-4x\frac{dy}{dx}=4y-2x
\frac{dy}{dx}(2y-4x)=4y-2x
\frac{dy}{dx}=\frac{4y-2x}{2y-4x}
\frac{dy}{dx}=\frac{2y-x}{y-2x}
```

อ่านไม่ออก: -

## hw_005 · P16 · w01 · stylus
รูป: `raw/hw_005.jpg` · โจทย์: `\text{แก้สมการ } e^{2x}-3e^{x}+2=0`

```
e^{2x}-3e^{x}+2=0
(e^{x})^{2}-3e^{x}+2=0
(e^{x}-1)(e^{x}-2)=0
e^{x}=1, e^{x}=2
x=0, x=\ln(2)
```

อ่านไม่ออก: -

## hw_006 · P03 · w01 · stylus
รูป: `raw/hw_006.jpg` · โจทย์: `\text{แยกตัวประกอบ } x^{4}-16`

```
x^{4}-16
=(x^{2}-4)(x^{2}+4)
=(x-2)(x+2)(x^{2}+4)
```

อ่านไม่ออก: -

## hw_007 · P08 · w02 · stylus
รูป: `raw/hw_007.jpg` · โจทย์: `\frac{d}{dx}\left(x^{2}\sin(x)\right)`

```
\frac{d}{dx}\left(x^{2}\sin(x)\right)
=\sin(x)\frac{d}{dx}\left(x^{2}\right)+x^{2}\frac{d}{dx}\left(\sin(x)\right)
=2x\sin(x)-x^{2}\cos(x)
```

อ่านไม่ออก: -

## hw_008 · P15 · w02 · stylus
รูป: `raw/hw_008.jpg` · โจทย์: `\text{หาจุดวิกฤตของ } f(x)=x^{3}-3x^{2}-9x+1`

```
f(x)=x^{3}-3x^{2}-9x+1
f'(x)=3x^{2}-6x-9
3x^{2}-6x-9=0
x^{2}-2x-3=0
(x+3)(x-1)=0
x=-3, x=1
```

อ่านไม่ออก: -

## hw_009 · P02 · w02 · stylus
รูป: `raw/hw_009.jpg` · โจทย์: `\text{แยกตัวประกอบ } 2x^{2}+x-6`

```
2x^{2}+x-6
=2x^{2}+4x-3x-6
=2x(x+2)-3(x+2)
=(2x-3)(x+2)
```

อ่านไม่ออก: -

## hw_010 · P11 · w02 · stylus
รูป: `raw/hw_010.jpg` · โจทย์: `\frac{d}{dx}\left(e^{x^{2}}\ln(x)\right)`

```
\frac{d}{dx}\left(e^{x^{2}}\ln(x)\right)
=e^{x^{2}}\cdot 2x\cdot\ln(x)+e^{x^{2}}\cdot\frac{1}{x}
=2xe^{x^{2}}\ln(x)+\frac{e^{x^{2}}}{x}
```

อ่านไม่ออก: -

## hw_011 · P14 · w02 · stylus
รูป: `raw/hw_011.jpg` · โจทย์: `\lim_{x \to 1} \frac{x^{2}+1}{x+1}`

```
\lim_{x \to 1} \frac{x^{2}+1}{x+1}
=\frac{1^{2}+1}{1+1}
=\frac{2}{2}
=1
```

อ่านไม่ออก: -

## hw_012 · P17 · w02 · stylus
รูป: `raw/hw_012.jpg` · โจทย์: `\text{หาค่า } x \text{ ที่ } f(x)=x^{4}-6x^{2} \text{ อาจมีจุดเปลี่ยนเว้า}`

```
f(x)=x^{4}-6x^{2}
f'(x)=4x^{3}-12x
f''(x)=12x^{2}-12
12x^{2}-12=0
x^{2}=1
x=1, x=-1
```

อ่านไม่ออก: -

## hw_013 · P09 · w03 · stylus
รูป: `raw/hw_013.png` · โจทย์: `\frac{d}{dx}\left(\frac{x^{2}+1}{x-1}\right)`

```
\frac{d}{dx}\left(\frac{x^{2}+1}{x-1}\right)
=\frac{(x^{2}+1)(1)-(x-1)(2x)}{(x-1)^{2}}
=\frac{x^{2}+1-2x^{2}+2x}{(x-1)^{2}}
=\frac{-x^{2}+2x+1}{(x-1)^{2}}
```

อ่านไม่ออก: -

## hw_014 · P10 · w03 · stylus
รูป: `raw/hw_014.png` · โจทย์: `\frac{d}{dx}\left(\sin^{3}(2x)\right)`

```
\frac{d}{dx}\left(\sin^{3}(2x)\right)
=3\sin^{2}(2x)\cdot\frac{d}{dx}\left(\sin(2x)\right)
=3\sin^{2}(2x)\cos(2x)
```

อ่านไม่ออก: -

## hw_015 · P04 · w03 · stylus
รูป: `raw/hw_015.png` · โจทย์: `\text{แยกตัวประกอบ } x^{3}-2x^{2}-4x+8`

```
x^{3}-2x^{2}-4x+8
=x^{2}(x-2)-4(x-2)
=(x^{2}-4)(x-2)
=(x-2)(x+2)(x-2)
=(x-2)^{2}(x+2)
```

อ่านไม่ออก: -

## hw_016 · P06 · w03 · stylus
รูป: `raw/hw_016.png` · โจทย์: `\lim_{x \to 0} \frac{\sin(3x)}{x}`

```
\lim_{x \to 0} \frac{\sin(3x)}{x}
=\lim_{x \to 0} 3\cdot\frac{\sin(3x)}{3x}
=3\cdot 1
=3
```

อ่านไม่ออก: -

## hw_017 · P13 · w03 · stylus
รูป: `raw/hw_017.png` · โจทย์: `f(x)=x^{4}-3x^{2}+2x \text{ หา } f''(x)`

```
f(x)=x^{4}-3x^{2}+2x
f'(x)=4x^{3}-6x+2
f''(x)=12x^{2}-6
```

อ่านไม่ออก: -

## hw_018 · P15 · w03 · stylus
รูป: `raw/hw_018.png` · โจทย์: `\text{หาจุดวิกฤตของ } f(x)=x^{3}-3x^{2}-9x+1`

```
f(x)=x^{3}-3x^{2}-9x+1
f'(x)=3x^{2}-6x-9
3x^{2}-6x-9=0
x^{2}-2x-3=0
(x-3)(x+1)=0
x=3, x=-1
```

อ่านไม่ออก: -

## hw_019 · P13 · w04 · stylus
รูป: `raw/hw_019.png` · โจทย์: `f(x)=x^{4}-3x^{2}+2x \text{ หา } f''(x)`

```
f(x)=x^{4}-3x^{2}+2x
f'(x)=4x^{3}-6x+2
f''(x)=16x^{2}-6
```

อ่านไม่ออก: -

## hw_020 · P14 · w04 · stylus
รูป: `raw/hw_020.png` · โจทย์: `\lim_{x \to 1} \frac{x^{2}+1}{x+1}`

```
\lim_{x \to 1} \frac{x^{2}+1}{x+1}
=\lim_{x \to 1} \frac{2x}{1}
=2(1)
=2
```

อ่านไม่ออก: -

## hw_021 · P01 · w04 · stylus
รูป: `raw/hw_021.png` · โจทย์: `\text{แยกตัวประกอบ } x^{3}-x`

```
x^{3}-x
=x(x^{2}-1)
=x(x-1)(x+1)
```

อ่านไม่ออก: -

## hw_022 · P08 · w04 · stylus
รูป: `raw/hw_022.png` · โจทย์: `\frac{d}{dx}\left(x^{2}\sin(x)\right)`

```
\frac{d}{dx}\left(x^{2}\sin(x)\right)
=\sin(x)\frac{d}{dx}\left(x^{2}\right)+x^{2}\frac{d}{dx}\left(\sin(x)\right)
=2x\sin(x)+x^{2}\cos(x)
```

อ่านไม่ออก: -

## hw_023 · P16 · w04 · stylus
รูป: `raw/hw_023.png` · โจทย์: `\text{แก้สมการ } e^{2x}-3e^{x}+2=0`

```
e^{2x}-3e^{x}+2=0
(e^{x})^{2}-3e^{x}+2=0
(e^{x}-1)(e^{x}-2)=0
e^{x}=1, e^{x}=2
x=0, x=\ln(2)
```

อ่านไม่ออก: -

## hw_024 · P05 · w04 · stylus
รูป: `raw/hw_024.png` · โจทย์: `\lim_{x \to 2} \frac{x^{2}-4}{x^{2}-3x+2}`

```
\lim_{x \to 2} \frac{x^{2}-4}{x^{2}-3x+2}
=\lim_{x \to 2} \frac{(x-2)(x+2)}{(x-2)(x-1)}
=\lim_{x \to 2} \frac{x+2}{x-1}
=\frac{4}{1}
=4
```

อ่านไม่ออก: -

## hw_025 · P04 · w05 · stylus
รูป: `raw/hw_025.png` · โจทย์: `\text{แยกตัวประกอบ } x^{3}-2x^{2}-4x+8`

```
x^{3}-2x^{2}-4x+8
=x^{2}(x-2)-4(x-2)
=(x^{2}-4)(x-2)
=(x-2)(x+2)(x-2)
=(x-2)^{2}(x+2)
```

อ่านไม่ออก: -

## hw_026 · P06 · w05 · stylus
รูป: `raw/hw_026.png` · โจทย์: `\lim_{x \to 0} \frac{\sin(3x)}{x}`

```
\lim_{x \to 0} \frac{\sin(3x)}{x}
=\lim_{x \to 0} 3\cdot\frac{\sin(3x)}{3x}
=3\cdot 1
=3
```

อ่านไม่ออก: -

## hw_027 · P02 · w05 · stylus
รูป: `raw/hw_027.png` · โจทย์: `\text{แยกตัวประกอบ } 2x^{2}+x-6`

```
2x^{2}+x-6
=2x^{2}+4x-3x-6
=2x(x+2)-3(x+2)
=(2x-3)(x+2)
```

อ่านไม่ออก: -

## hw_028 · P09 · w05 · stylus
รูป: `raw/hw_028.png` · โจทย์: `\frac{d}{dx}\left(\frac{x^{2}+1}{x-1}\right)`

```
\frac{d}{dx}\left(\frac{x^{2}+1}{x-1}\right)
=\frac{(x-1)(2x)-(x^{2}+1)(1)}{(x-1)^{2}}
=\frac{2x^{2}-2x-x^{2}-1}{(x-1)^{2}}
=\frac{x^{2}-2x-1}{(x-1)^{2}}
```

อ่านไม่ออก: -

## hw_029 · P10 · w05 · stylus
รูป: `raw/hw_029.png` · โจทย์: `\frac{d}{dx}\left(\sin^{3}(2x)\right)`

```
\frac{d}{dx}\left(\sin^{3}(2x)\right)
=3\sin^{2}(2x)\cdot\frac{d}{dx}\left(\sin(2x)\right)
=3\sin^{2}(2x)\cdot\cos(2x)\cdot 2
=6\sin^{2}(2x)\cos(2x)
```

อ่านไม่ออก: -

## hw_030 · P17 · w05 · stylus
รูป: `raw/hw_030.png` · โจทย์: `\text{หาค่า } x \text{ ที่ } f(x)=x^{4}-6x^{2} \text{ อาจมีจุดเปลี่ยนเว้า}`

```
f(x)=x^{4}-6x^{2}
f'(x)=4x^{3}-12x
f''(x)=12x^{2}-12
12x^{2}-12=0
x^{2}=1
x=1, x=-1
```

อ่านไม่ออก: -
