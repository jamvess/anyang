# ใบงาน golden set คำตอบ · P2

คู่มือ: `evals/README.md` หัวข้อ "คู่มือ label golden set คำตอบ · P2"
· คน label ต้องไม่ใช่ Jam (คนทำ P2)

- กรอกเฉพาะช่องหลัง `lines:` (verdict, error_type, first_wrong_line, method, labeled_by)
  · ช่องที่ว่างไว้ = ยังไม่ label
- ข้อที่มาจากรูป: ห้ามแก้ image, writer, problem_id, lines
  · problem, answer_format, reference แสดงไว้ให้ดูเท่านั้น
- ข้อพิมพ์ (`image: none`): ใส่ `problem_id` (P01-P17 ใน `evals/handwriting/problems.md`),
  `writer` (w01, w02, ...) และบรรทัดคำตอบทีละบรรทัด เช่น 1. `x(x^{2}-1)`
- method ว่าง = `doc` · กรอกเสร็จแล้วรัน `--build` เพื่อตรวจกติกาและสร้าง `labels.jsonl`

## ans_001

- image: ../handwriting/raw/hw_001.jpg
- writer: w01
- problem_id: P01
- answer_format: factored
- problem: `\text{แยกตัวประกอบ } x^{3}-x`
- reference: `x(x-1)(x+1)`

lines:

1. `x^{3}-x`
2. `=x(x^{2}-1)`

- verdict:
- error_type:
- first_wrong_line:
- method:
- labeled_by:

## ans_002

- image: ../handwriting/raw/hw_002.jpg
- writer: w01
- problem_id: P05
- answer_format: expression
- problem: `\lim_{x \to 2} \frac{x^{2}-4}{x^{2}-3x+2}`
- reference: `4`

lines:

1. `\lim_{x \to 2} \frac{x^{2}-4}{x^{2}-3x+2}`
2. `=\lim_{x \to 2} \frac{-4}{-3x+2}`
3. `=\frac{-4}{-6+2}`
4. `=1`

- verdict:
- error_type:
- first_wrong_line:
- method:
- labeled_by:

## ans_003

- image: ../handwriting/raw/hw_003.jpg
- writer: w01
- problem_id: P07
- answer_format: expression
- problem: `\lim_{x \to \infty} \frac{3x^{2}-x}{2x^{2}+5}`
- reference: `\frac{3}{2}`

lines:

1. `\lim_{x \to \infty} \frac{3x^{2}-x}{2x^{2}+5}`
2. `=\lim_{x \to \infty} \frac{3-\frac{1}{x}}{2+\frac{5}{x^{2}}}`
3. `=\frac{3-0}{2+0}`
4. `=\frac{3}{2}`

- verdict:
- error_type:
- first_wrong_line:
- method:
- labeled_by:

## ans_004

- image: ../handwriting/raw/hw_004.jpg
- writer: w01
- problem_id: P12
- answer_format: expression
- problem: `\text{หา } \frac{dy}{dx} \text{ จาก } x^{2}+y^{2}=4xy`
- reference: `\frac{2y-x}{y-2x}`

lines:

1. `x^{2}+y^{2}=4xy`
2. `2x+2y\frac{dy}{dx}=4y+4x\frac{dy}{dx}`
3. `2y\frac{dy}{dx}-4x\frac{dy}{dx}=4y-2x`
4. `\frac{dy}{dx}(2y-4x)=4y-2x`
5. `\frac{dy}{dx}=\frac{4y-2x}{2y-4x}`
6. `\frac{dy}{dx}=\frac{2y-x}{y-2x}`

- verdict:
- error_type:
- first_wrong_line:
- method:
- labeled_by:

## ans_005

- image: ../handwriting/raw/hw_005.jpg
- writer: w01
- problem_id: P16
- answer_format: equation
- problem: `\text{แก้สมการ } e^{2x}-3e^{x}+2=0`
- reference: `x=0, x=\ln(2)`

lines:

1. `e^{2x}-3e^{x}+2=0`
2. `(e^{x})^{2}-3e^{x}+2=0`
3. `(e^{x}-1)(e^{x}-2)=0`
4. `e^{x}=1, e^{x}=2`
5. `x=0, x=\ln(2)`

- verdict:
- error_type:
- first_wrong_line:
- method:
- labeled_by:

## ans_006

- image: ../handwriting/raw/hw_006.jpg
- writer: w01
- problem_id: P03
- answer_format: factored
- problem: `\text{แยกตัวประกอบ } x^{4}-16`
- reference: `(x-2)(x+2)(x^{2}+4)`

lines:

1. `x^{4}-16`
2. `=(x^{2}-4)(x^{2}+4)`
3. `=(x-2)(x+2)(x^{2}+4)`

- verdict:
- error_type:
- first_wrong_line:
- method:
- labeled_by:

## ans_007

- image: ../handwriting/raw/hw_007.jpg
- writer: w02
- problem_id: P08
- answer_format: expression
- problem: `\frac{d}{dx}\left(x^{2}\sin(x)\right)`
- reference: `2x\sin(x)+x^{2}\cos(x)`

lines:

1. `\frac{d}{dx}\left(x^{2}\sin(x)\right)`
2. `=\sin(x)\frac{d}{dx}\left(x^{2}\right)+x^{2}\frac{d}{dx}\left(\sin(x)\right)`
3. `=2x\sin(x)-x^{2}\cos(x)`

- verdict:
- error_type:
- first_wrong_line:
- method:
- labeled_by:

## ans_008

- image: ../handwriting/raw/hw_008.jpg
- writer: w02
- problem_id: P15
- answer_format: equation
- problem: `\text{หาจุดวิกฤตของ } f(x)=x^{3}-3x^{2}-9x+1`
- reference: `x=-1, x=3`

lines:

1. `f(x)=x^{3}-3x^{2}-9x+1`
2. `f'(x)=3x^{2}-6x-9`
3. `3x^{2}-6x-9=0`
4. `x^{2}-2x-3=0`
5. `(x+3)(x-1)=0`
6. `x=-3, x=1`

- verdict:
- error_type:
- first_wrong_line:
- method:
- labeled_by:

## ans_009

- image: ../handwriting/raw/hw_009.jpg
- writer: w02
- problem_id: P02
- answer_format: factored
- problem: `\text{แยกตัวประกอบ } 2x^{2}+x-6`
- reference: `(2x-3)(x+2)`

lines:

1. `2x^{2}+x-6`
2. `=2x^{2}+4x-3x-6`
3. `=2x(x+2)-3(x+2)`
4. `=(2x-3)(x+2)`

- verdict:
- error_type:
- first_wrong_line:
- method:
- labeled_by:

## ans_010

- image: ../handwriting/raw/hw_010.jpg
- writer: w02
- problem_id: P11
- answer_format: expression
- problem: `\frac{d}{dx}\left(e^{x^{2}}\ln(x)\right)`
- reference: `2xe^{x^{2}}\ln(x)+\frac{e^{x^{2}}}{x}`

lines:

1. `\frac{d}{dx}\left(e^{x^{2}}\ln(x)\right)`
2. `=e^{x^{2}}\cdot 2x\cdot\ln(x)+e^{x^{2}}\cdot\frac{1}{x}`
3. `=2xe^{x^{2}}\ln(x)+\frac{e^{x^{2}}}{x}`

- verdict:
- error_type:
- first_wrong_line:
- method:
- labeled_by:

## ans_011

- image: ../handwriting/raw/hw_011.jpg
- writer: w02
- problem_id: P14
- answer_format: expression
- problem: `\lim_{x \to 1} \frac{x^{2}+1}{x+1}`
- reference: `1`

lines:

1. `\lim_{x \to 1} \frac{x^{2}+1}{x+1}`
2. `=\frac{1^{2}+1}{1+1}`
3. `=\frac{2}{2}`
4. `=1`

- verdict:
- error_type:
- first_wrong_line:
- method:
- labeled_by:

## ans_012

- image: ../handwriting/raw/hw_012.jpg
- writer: w02
- problem_id: P17
- answer_format: equation
- problem: `\text{หาค่า } x \text{ ที่ } f(x)=x^{4}-6x^{2} \text{ อาจมีจุดเปลี่ยนเว้า}`
- reference: `x=-1, x=1`

lines:

1. `f(x)=x^{4}-6x^{2}`
2. `f'(x)=4x^{3}-12x`
3. `f''(x)=12x^{2}-12`
4. `12x^{2}-12=0`
5. `x^{2}=1`
6. `x=1, x=-1`

- verdict:
- error_type:
- first_wrong_line:
- method:
- labeled_by:

## ans_013

- image: ../handwriting/raw/hw_013.png
- writer: w03
- problem_id: P09
- answer_format: expression
- problem: `\frac{d}{dx}\left(\frac{x^{2}+1}{x-1}\right)`
- reference: `\frac{x^{2}-2x-1}{(x-1)^{2}}`

lines:

1. `\frac{d}{dx}\left(\frac{x^{2}+1}{x-1}\right)`
2. `=\frac{(x^{2}+1)(1)-(x-1)(2x)}{(x-1)^{2}}`
3. `=\frac{x^{2}+1-2x^{2}+2x}{(x-1)^{2}}`
4. `=\frac{-x^{2}+2x+1}{(x-1)^{2}}`

- verdict:
- error_type:
- first_wrong_line:
- method:
- labeled_by:

## ans_014

- image: ../handwriting/raw/hw_014.png
- writer: w03
- problem_id: P10
- answer_format: expression
- problem: `\frac{d}{dx}\left(\sin^{3}(2x)\right)`
- reference: `6\sin^{2}(2x)\cos(2x)`

lines:

1. `\frac{d}{dx}\left(\sin^{3}(2x)\right)`
2. `=3\sin^{2}(2x)\cdot\frac{d}{dx}\left(\sin(2x)\right)`
3. `=3\sin^{2}(2x)\cos(2x)`

- verdict:
- error_type:
- first_wrong_line:
- method:
- labeled_by:

## ans_015

- image: ../handwriting/raw/hw_015.png
- writer: w03
- problem_id: P04
- answer_format: factored
- problem: `\text{แยกตัวประกอบ } x^{3}-2x^{2}-4x+8`
- reference: `(x-2)^{2}(x+2)`

lines:

1. `x^{3}-2x^{2}-4x+8`
2. `=x^{2}(x-2)-4(x-2)`
3. `=(x^{2}-4)(x-2)`
4. `=(x-2)(x+2)(x-2)`
5. `=(x-2)^{2}(x+2)`

- verdict:
- error_type:
- first_wrong_line:
- method:
- labeled_by:

## ans_016

- image: ../handwriting/raw/hw_016.png
- writer: w03
- problem_id: P06
- answer_format: expression
- problem: `\lim_{x \to 0} \frac{\sin(3x)}{x}`
- reference: `3`

lines:

1. `\lim_{x \to 0} \frac{\sin(3x)}{x}`
2. `=\lim_{x \to 0} 3\cdot\frac{\sin(3x)}{3x}`
3. `=3\cdot 1`
4. `=3`

- verdict:
- error_type:
- first_wrong_line:
- method:
- labeled_by:

## ans_017

- image: ../handwriting/raw/hw_017.png
- writer: w03
- problem_id: P13
- answer_format: expression
- problem: `f(x)=x^{4}-3x^{2}+2x \text{ หา } f''(x)`
- reference: `12x^{2}-6`

lines:

1. `f(x)=x^{4}-3x^{2}+2x`
2. `f'(x)=4x^{3}-6x+2`
3. `f''(x)=12x^{2}-6`

- verdict:
- error_type:
- first_wrong_line:
- method:
- labeled_by:

## ans_018

- image: ../handwriting/raw/hw_018.png
- writer: w03
- problem_id: P15
- answer_format: equation
- problem: `\text{หาจุดวิกฤตของ } f(x)=x^{3}-3x^{2}-9x+1`
- reference: `x=-1, x=3`

lines:

1. `f(x)=x^{3}-3x^{2}-9x+1`
2. `f'(x)=3x^{2}-6x-9`
3. `3x^{2}-6x-9=0`
4. `x^{2}-2x-3=0`
5. `(x-3)(x+1)=0`
6. `x=3, x=-1`

- verdict:
- error_type:
- first_wrong_line:
- method:
- labeled_by:

## ans_019

- image: ../handwriting/raw/hw_019.png
- writer: w04
- problem_id: P13
- answer_format: expression
- problem: `f(x)=x^{4}-3x^{2}+2x \text{ หา } f''(x)`
- reference: `12x^{2}-6`

lines:

1. `f(x)=x^{4}-3x^{2}+2x`
2. `f'(x)=4x^{3}-6x+2`
3. `f''(x)=16x^{2}-6`

- verdict:
- error_type:
- first_wrong_line:
- method:
- labeled_by:

## ans_020

- image: ../handwriting/raw/hw_020.png
- writer: w04
- problem_id: P14
- answer_format: expression
- problem: `\lim_{x \to 1} \frac{x^{2}+1}{x+1}`
- reference: `1`

lines:

1. `\lim_{x \to 1} \frac{x^{2}+1}{x+1}`
2. `=\lim_{x \to 1} \frac{2x}{1}`
3. `=2(1)`
4. `=2`

- verdict:
- error_type:
- first_wrong_line:
- method:
- labeled_by:

## ans_021

- image: ../handwriting/raw/hw_021.png
- writer: w04
- problem_id: P01
- answer_format: factored
- problem: `\text{แยกตัวประกอบ } x^{3}-x`
- reference: `x(x-1)(x+1)`

lines:

1. `x^{3}-x`
2. `=x(x^{2}-1)`
3. `=x(x-1)(x+1)`

- verdict:
- error_type:
- first_wrong_line:
- method:
- labeled_by:

## ans_022

- image: ../handwriting/raw/hw_022.png
- writer: w04
- problem_id: P08
- answer_format: expression
- problem: `\frac{d}{dx}\left(x^{2}\sin(x)\right)`
- reference: `2x\sin(x)+x^{2}\cos(x)`

lines:

1. `\frac{d}{dx}\left(x^{2}\sin(x)\right)`
2. `=\sin(x)\frac{d}{dx}\left(x^{2}\right)+x^{2}\frac{d}{dx}\left(\sin(x)\right)`
3. `=2x\sin(x)+x^{2}\cos(x)`

- verdict:
- error_type:
- first_wrong_line:
- method:
- labeled_by:

## ans_023

- image: ../handwriting/raw/hw_023.png
- writer: w04
- problem_id: P16
- answer_format: equation
- problem: `\text{แก้สมการ } e^{2x}-3e^{x}+2=0`
- reference: `x=0, x=\ln(2)`

lines:

1. `e^{2x}-3e^{x}+2=0`
2. `(e^{x})^{2}-3e^{x}+2=0`
3. `(e^{x}-1)(e^{x}-2)=0`
4. `e^{x}=1, e^{x}=2`
5. `x=0, x=\ln(2)`

- verdict:
- error_type:
- first_wrong_line:
- method:
- labeled_by:

## ans_024

- image: ../handwriting/raw/hw_024.png
- writer: w04
- problem_id: P05
- answer_format: expression
- problem: `\lim_{x \to 2} \frac{x^{2}-4}{x^{2}-3x+2}`
- reference: `4`

lines:

1. `\lim_{x \to 2} \frac{x^{2}-4}{x^{2}-3x+2}`
2. `=\lim_{x \to 2} \frac{(x-2)(x+2)}{(x-2)(x-1)}`
3. `=\lim_{x \to 2} \frac{x+2}{x-1}`
4. `=\frac{4}{1}`
5. `=4`

- verdict:
- error_type:
- first_wrong_line:
- method:
- labeled_by:

## ans_025

- image: ../handwriting/raw/hw_025.png
- writer: w05
- problem_id: P04
- answer_format: factored
- problem: `\text{แยกตัวประกอบ } x^{3}-2x^{2}-4x+8`
- reference: `(x-2)^{2}(x+2)`

lines:

1. `x^{3}-2x^{2}-4x+8`
2. `=x^{2}(x-2)-4(x-2)`
3. `=(x^{2}-4)(x-2)`
4. `=(x-2)(x+2)(x-2)`
5. `=(x-2)^{2}(x+2)`

- verdict:
- error_type:
- first_wrong_line:
- method:
- labeled_by:

## ans_026

- image: ../handwriting/raw/hw_026.png
- writer: w05
- problem_id: P06
- answer_format: expression
- problem: `\lim_{x \to 0} \frac{\sin(3x)}{x}`
- reference: `3`

lines:

1. `\lim_{x \to 0} \frac{\sin(3x)}{x}`
2. `=\lim_{x \to 0} 3\cdot\frac{\sin(3x)}{3x}`
3. `=3\cdot 1`
4. `=3`

- verdict:
- error_type:
- first_wrong_line:
- method:
- labeled_by:

## ans_027

- image: ../handwriting/raw/hw_027.png
- writer: w05
- problem_id: P02
- answer_format: factored
- problem: `\text{แยกตัวประกอบ } 2x^{2}+x-6`
- reference: `(2x-3)(x+2)`

lines:

1. `2x^{2}+x-6`
2. `=2x^{2}+4x-3x-6`
3. `=2x(x+2)-3(x+2)`
4. `=(2x-3)(x+2)`

- verdict:
- error_type:
- first_wrong_line:
- method:
- labeled_by:

## ans_028

- image: ../handwriting/raw/hw_028.png
- writer: w05
- problem_id: P09
- answer_format: expression
- problem: `\frac{d}{dx}\left(\frac{x^{2}+1}{x-1}\right)`
- reference: `\frac{x^{2}-2x-1}{(x-1)^{2}}`

lines:

1. `\frac{d}{dx}\left(\frac{x^{2}+1}{x-1}\right)`
2. `=\frac{(x-1)(2x)-(x^{2}+1)(1)}{(x-1)^{2}}`
3. `=\frac{2x^{2}-2x-x^{2}-1}{(x-1)^{2}}`
4. `=\frac{x^{2}-2x-1}{(x-1)^{2}}`

- verdict:
- error_type:
- first_wrong_line:
- method:
- labeled_by:

## ans_029

- image: ../handwriting/raw/hw_029.png
- writer: w05
- problem_id: P10
- answer_format: expression
- problem: `\frac{d}{dx}\left(\sin^{3}(2x)\right)`
- reference: `6\sin^{2}(2x)\cos(2x)`

lines:

1. `\frac{d}{dx}\left(\sin^{3}(2x)\right)`
2. `=3\sin^{2}(2x)\cdot\frac{d}{dx}\left(\sin(2x)\right)`
3. `=3\sin^{2}(2x)\cdot\cos(2x)\cdot 2`
4. `=6\sin^{2}(2x)\cos(2x)`

- verdict:
- error_type:
- first_wrong_line:
- method:
- labeled_by:

## ans_030

- image: ../handwriting/raw/hw_030.png
- writer: w05
- problem_id: P17
- answer_format: equation
- problem: `\text{หาค่า } x \text{ ที่ } f(x)=x^{4}-6x^{2} \text{ อาจมีจุดเปลี่ยนเว้า}`
- reference: `x=-1, x=1`

lines:

1. `f(x)=x^{4}-6x^{2}`
2. `f'(x)=4x^{3}-12x`
3. `f''(x)=12x^{2}-12`
4. `12x^{2}-12=0`
5. `x^{2}=1`
6. `x=1, x=-1`

- verdict:
- error_type:
- first_wrong_line:
- method:
- labeled_by:

## ans_031

- image: none
- writer:
- problem_id:

lines:

1. ``

- verdict:
- error_type:
- first_wrong_line:
- method:
- labeled_by:

## ans_032

- image: none
- writer:
- problem_id:

lines:

1. ``

- verdict:
- error_type:
- first_wrong_line:
- method:
- labeled_by:

## ans_033

- image: none
- writer:
- problem_id:

lines:

1. ``

- verdict:
- error_type:
- first_wrong_line:
- method:
- labeled_by:

## ans_034

- image: none
- writer:
- problem_id:

lines:

1. ``

- verdict:
- error_type:
- first_wrong_line:
- method:
- labeled_by:

## ans_035

- image: none
- writer:
- problem_id:

lines:

1. ``

- verdict:
- error_type:
- first_wrong_line:
- method:
- labeled_by:

## ans_036

- image: none
- writer:
- problem_id:

lines:

1. ``

- verdict:
- error_type:
- first_wrong_line:
- method:
- labeled_by:

## ans_037

- image: none
- writer:
- problem_id:

lines:

1. ``

- verdict:
- error_type:
- first_wrong_line:
- method:
- labeled_by:

## ans_038

- image: none
- writer:
- problem_id:

lines:

1. ``

- verdict:
- error_type:
- first_wrong_line:
- method:
- labeled_by:

## ans_039

- image: none
- writer:
- problem_id:

lines:

1. ``

- verdict:
- error_type:
- first_wrong_line:
- method:
- labeled_by:

## ans_040

- image: none
- writer:
- problem_id:

lines:

1. ``

- verdict:
- error_type:
- first_wrong_line:
- method:
- labeled_by:

## ans_041

- image: none
- writer:
- problem_id:

lines:

1. ``

- verdict:
- error_type:
- first_wrong_line:
- method:
- labeled_by:

## ans_042

- image: none
- writer:
- problem_id:

lines:

1. ``

- verdict:
- error_type:
- first_wrong_line:
- method:
- labeled_by:

## ans_043

- image: none
- writer:
- problem_id:

lines:

1. ``

- verdict:
- error_type:
- first_wrong_line:
- method:
- labeled_by:

## ans_044

- image: none
- writer:
- problem_id:

lines:

1. ``

- verdict:
- error_type:
- first_wrong_line:
- method:
- labeled_by:

## ans_045

- image: none
- writer:
- problem_id:

lines:

1. ``

- verdict:
- error_type:
- first_wrong_line:
- method:
- labeled_by:

## ans_046

- image: none
- writer:
- problem_id:

lines:

1. ``

- verdict:
- error_type:
- first_wrong_line:
- method:
- labeled_by:

## ans_047

- image: none
- writer:
- problem_id:

lines:

1. ``

- verdict:
- error_type:
- first_wrong_line:
- method:
- labeled_by:

## ans_048

- image: none
- writer:
- problem_id:

lines:

1. ``

- verdict:
- error_type:
- first_wrong_line:
- method:
- labeled_by:

## ans_049

- image: none
- writer:
- problem_id:

lines:

1. ``

- verdict:
- error_type:
- first_wrong_line:
- method:
- labeled_by:

## ans_050

- image: none
- writer:
- problem_id:

lines:

1. ``

- verdict:
- error_type:
- first_wrong_line:
- method:
- labeled_by:
