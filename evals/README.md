# evals/

Golden sets และ script วัดผล AI ใช้ทั้งใน PoC และใน CI (รันเมื่อ prompt หรือ model เปลี่ยน)

```
evals/
├─ handwriting/        # P1
│  ├─ raw/             # รูปจริง (gitignored ถ้าเป็นลายมือเพื่อน · เก็บใน Drive ทีม)
│  └─ labels.jsonl
├─ answers/            # P2
│  ├─ worksheet.md     # ใบงานที่คน label กรอก · ดู "ใบงาน" ด้านล่าง
│  ├─ make_worksheet.py
│  ├─ labels.jsonl     # สร้างจาก worksheet.md ด้วย make_worksheet.py --build
│  └─ results/         # <prompt>.json ที่ run_eval.py เขียน
├─ topics/             # P3 · ดูเกณฑ์เลือกวิชาและกติกาไฟล์ใน topics/README.md
│  └─ <subject>/       # raw/ (gitignored), sources.md, labels.json
└─ run_eval.py         # ให้คะแนน checker (check_answer) · ดู "การให้คะแนน" ด้านล่าง
```

```bash
uv run --project apps/api python evals/run_eval.py --purpose check_answer --prompt v1 \
    --predictions <checker output>.jsonl
uv run --project apps/api pytest evals/test_run_eval.py
```

`run_eval.py` ให้คะแนนจากไฟล์ prediction · ไฟล์ prediction สร้างด้วย `run_checker.py` ซึ่งเรียก checker จริง (`app/services/checker.py`: SymPy → `check_answer` → merge rules · `specs/features/check/check-answer-classifier.md` §2.6) · ใช้ model จริงเมื่อ `AI_PROVIDER=live` เท่านั้น:

```bash
# Vertex AI (ตั้ง GOOGLE_CLOUD_PROJECT + ADC ตาม docs/team/setup.md A5) · ~5 นาทีสำหรับ 50 ข้อ
AI_PROVIDER=live uv run --project apps/api python evals/run_checker.py --pause 1
uv run --project apps/api pytest evals/test_run_checker.py
```

ผล P2 ล่าสุด (31 ต.ค. · prompt v1 · `vertex:gemini-3.5-flash`) อยู่ที่ `answers/predictions/v1.jsonl` และ `answers/results/v1.json` · ถ้าใช้ API key ของ AI Studio แทน (`AI_MODEL_OVERRIDE=gemini:<model>`) free tier ได้แค่ 20 request/วัน/model รัน 50 ข้อไม่จบในวันเดียว ต้องใช้ `--resume`

การให้คะแนนลายมือ (`extract_answer`) ยังอยู่ที่ `poc/P1/score.py`

## รูปแบบ label

**handwriting/labels.jsonl** · ดู [คู่มือ label ลายมือ](#คู่มือ-label-ลายมือ--p1)

**answers/labels.jsonl**

ดู [คู่มือ label golden set คำตอบ](#คู่มือ-label-golden-set-คำตอบ--p2)

**topics/<subject>/labels.json**

รูปแบบและคู่มือการ label อยู่ใน [`topics/README.md`](topics/README.md#คู่มือ-label--labelsjson)

## คู่มือ label ลายมือ · P1

เป้าหมาย: พิมพ์ **สิ่งที่เขียนอยู่ในรูปจริงๆ** เป็น LaTeX ทีละบรรทัด เพื่อใช้เทียบกับสิ่งที่ AI อ่านได้ (prompt `prompts/extract_answer/v1.md`) · P1 ให้คะแนนแต่ละบรรทัดด้วย SymPy คือบรรทัดที่ AI อ่าน**เท่ากันทางคณิตศาสตร์**กับเฉลยของเรา ถือว่าอ่านถูก ดังนั้นเฉลยต้องถูกต้องตามรูป และ SymPy ต้อง parse ได้

### กติกา 7 ข้อ

1. **พิมพ์ตามที่เขียน รวมถึงที่ผิดด้วย** ห้ามแก้ให้ถูก ถ้าในรูปเขียน `(x-2)(x+3)` ทั้งที่คำตอบที่ถูกคือ `(x-2)(x-3)` ก็พิมพ์ `(x-2)(x+3)`
2. **1 บรรทัดในรูป = 1 รายการใน `lines`** เรียงจากบนลงล่าง ถ้าในรูปเขียน 2 คอลัมน์ ให้อ่านคอลัมน์ซ้ายให้จบก่อน
3. **ข้ามบรรทัดที่ขีดฆ่าทิ้ง** ทั้งบรรทัด ถ้าขีดฆ่าแค่บางส่วน ให้พิมพ์เฉพาะส่วนที่เหลือ
4. **เก็บแค่คณิตศาสตร์** ตัดคำพูดอย่าง "ดังนั้น", "จาก (1)", "∴" และลูกศร `⇒` ที่ต้นบรรทัดออก ถ้าบรรทัดนั้นเป็นคำพูดล้วนๆ ให้ข้ามทั้งบรรทัด
5. **พิมพ์ `=` ตามที่เขียน** ถ้าบรรทัดเดียวมี `a = b = c` ให้พิมพ์ทั้งหมด และถ้าบรรทัดขึ้นต้นด้วย `=` ก็พิมพ์ `=` ไว้ด้วย
6. **ไม่ใส่ `$`** และใช้รูปแบบ LaTeX ตามตารางด้านล่าง
7. **ตัวที่อ่านไม่ออกจริงๆ** ให้ใส่ `\?` แทนตัวนั้น แล้วใส่เลขบรรทัด (เริ่มนับที่ 1) ใน `unclear_lines` · บรรทัดเหล่านี้จะไม่ถูกนำมาให้คะแนน · ถ้าอ่านออกแต่ไม่แน่ใจ ให้เลือกแบบที่น่าจะใช่ที่สุดแล้วไม่ต้องใส่ `unclear_lines`

### รูปแบบ LaTeX

| เรื่อง | พิมพ์แบบนี้ | ไม่ใช่แบบนี้ |
|---|---|---|
| เศษส่วน | `\frac{x+1}{x-2}` | `(x+1)/(x-2)` |
| ยกกำลัง | `x^{2}`, `e^{3x}` (ใส่ `{}` เสมอ) | `e^3x` |
| รากที่สอง / รากที่ n | `\sqrt{x}`, `\sqrt[3]{x}` | `x^{1/2}` (ยกเว้นในรูปเขียนแบบนั้นจริง) |
| ฟังก์ชัน | `\sin(2x)`, `\ln(x)`, `\sec^{-1}(x)`, `\sinh(x)` | `sin2x`, `sin^-1` |
| ยกกำลังของฟังก์ชัน | `\sin^{2}(x)` หรือตามที่เขียน `(\sin x)^{2}` | |
| ค่าสัมบูรณ์ | `\left\|x\right\|` | `\|x\|` |
| ลิมิต | `\lim_{x \to 0^{-}} \frac{2}{x}` | `lim x->0-` |
| อนุพันธ์ | `\frac{dy}{dx}`, `f'(x)`, `f''(1)`, `\frac{d}{dx}\left(x^{2}\right)` | `dy/dx` |
| อนันต์ | `\infty` | `inf` |
| คูณ | เขียนติดกันได้ `2x`, ใช้ `\cdot` เมื่อในรูปมีจุดหรือเครื่องหมายคูณ | `*` |

### รูปแบบไฟล์ · `handwriting/labels.jsonl` (1 บรรทัด = 1 รูป)

```json
{"id": "hw_001", "image": "raw/hw_001.jpg", "writer": "w03", "problem": "\\frac{d}{dx}\\left(x^{2}\\sin(x)\\right)", "lines": ["2x\\sin(x)+x^{2}\\cos(x)"], "unclear_lines": [], "labeled_by": "May"}
```

- `writer` เป็นรหัสคนเขียน (`w01`, `w02`, ...) ห้ามใส่ชื่อจริง ตารางที่จับคู่รหัสกับชื่อและหลักฐานการขอความยินยอมให้เก็บใน Drive ทีม
- `problem` คือโจทย์ที่คนเขียนกำลังทำ ส่งให้ AI เป็น context ด้วย
- ใน JSON ต้องพิมพ์ `\` เป็น `\\` (เช่น `\\frac`) ส่วนตารางด้านบนเขียนแบบ `\` ตัวเดียวให้อ่านง่าย

### ตรวจก่อนส่ง

- เปิดรูปคู่กับ label แล้วนับบรรทัด จำนวนบรรทัดต้องเท่ากัน (ไม่นับบรรทัดที่ขีดฆ่าหรือเป็นคำพูดล้วน)
- วาง LaTeX ของแต่ละบรรทัดลงใน https://www.quicklatex.com หรือ KaTeX แล้วดูว่า render ออกมาหน้าตาเหมือนในรูป

## คู่มือ label golden set คำตอบ · P2

เป้าหมาย: ตัดสินคำตอบ 1 ข้อเหมือนอาจารย์ที่ตรวจละเอียด แล้วบันทึก 3 อย่างคือ **verdict** (ถูกหรือผิดแบบไหน), **error_type** (ผิดเพราะอะไร) และ **first_wrong_line** (เริ่มผิดบรรทัดไหน) เพื่อใช้วัด checker ของ P2 · ค่าทั้งหมดมาจาก `specs/system/ai-orchestration.md` §2.4 ห้ามเพิ่มค่าใหม่เอง

`lines` พิมพ์ตาม[กติกาลายมือ](#คู่มือ-label-ลายมือ--p1) ถ้าคำตอบมาจากรูปที่ label ไว้แล้วใน `handwriting/` ให้ก๊อป `lines` มาใช้ได้เลย

### verdict · ดูที่คำตอบสุดท้ายก่อน แล้วค่อยดูทุกบรรทัด

| verdict | ใช้เมื่อ | นับว่า |
|---|---|---|
| `correct` | คำตอบสุดท้ายถูก และทุกบรรทัดถูก | ถูก |
| `correct_with_flaw` | คำตอบสุดท้ายถูก แต่มีบรรทัดที่ผิด (ผิด 2 ที่แล้วหักล้างกันพอดี) | ผิด |
| `incomplete` | ค่าเท่ากับเฉลย แต่ยังไม่อยู่ในรูปที่โจทย์สั่ง เช่น โจทย์สั่งให้แยกตัวประกอบแต่ยังแยกไม่หมด | ผิด |
| `incorrect` | คำตอบสุดท้ายผิด หรือไม่มีคำตอบ | ผิด |

ถ้าตอบถูกด้วยวิธีที่ต่างจากในชีท ให้ verdict เป็น `correct` แล้วใส่ `"method": "other"` (ค่าปกติคือ `"doc"`)

### error_type · ใส่เฉพาะเมื่อ verdict ไม่ใช่ `correct`

ดูที่**บรรทัดแรกที่ผิด**บรรทัดเดียว แล้วถามตามลำดับนี้ ข้อแรกที่ตอบว่า "ใช่" คือคำตอบ

| ลำดับ | ถาม | error_type | ตัวอย่าง |
|---|---|---|---|
| 1 | ไม่มีคำตอบ หรือเขียนว่า "ไม่รู้", "ทำไม่ได้" ใช่ไหม | `no_answer` | กระดาษเปล่า |
| 2 | ถ้ากลับเครื่องหมายบวกลบของพจน์เดียว บรรทัดนั้นจะถูกใช่ไหม | `sign` | d/dx cos x = sin x |
| 3 | ผิดเพราะความรู้ที่ควรรู้ก่อนเรียนวิชานี้ใช่ไหม (พีชคณิต, เศษส่วน, เลขยกกำลัง, identity ตรีโกณ, กฎของ log) | `prerequisite` | ln(a+b) = ln a + ln b |
| 4 | เลือกวิธีที่ใช้กับโจทย์แบบนี้ไม่ได้ใช่ไหม | `wrong_method` | ใช้ L'Hôpital กับลิมิตที่ไม่ใช่ 0/0 หรือ ∞/∞ |
| 5 | เข้าใจหลักการของหัวข้อนี้ผิด (สูตรผิด, ลืมขั้นตอน, ตอบไม่อยู่ในรูปที่สั่ง) ใช่ไหม | `concept` | d/dx sin(3x) = cos(3x) (ลืม chain rule) · ทุกข้อที่เป็น `incomplete` |
| 6 | ไม่ใช่ข้อไหนเลย วิธีและหลักการถูก แต่คิดเลขพลาด | `calculation` | 3 · 4 = 7 |

ถ้าลังเลระหว่าง `concept` กับ `calculation` ให้ถามว่า "ถ้าให้ทำข้อเดิมอีกรอบ เขาจะผิดแบบเดิมไหม" ถ้าผิดแบบเดิม เป็น `concept` ถ้าน่าจะทำถูก เป็น `calculation`

### first_wrong_line

- คือเลขบรรทัด**แรก**ที่มีความผิด (เริ่มนับที่ 1 ตามลำดับใน `lines`) ถึงแม้บรรทัดหลังจากนั้นจะทำต่อได้ถูกต้องตามบรรทัดที่ผิด ก็ให้ใส่บรรทัดแรก
- เป็น `null` เมื่อ verdict เป็น `correct` หรือ `incomplete` หรือ error_type เป็น `no_answer`
- ถ้า `correct_with_flaw` ให้ใส่บรรทัดแรกที่ผิดใน 2 ที่ที่หักล้างกัน

### answer_format

ใช้บอก checker ว่า "ถูก" แปลว่าอะไร · ข้อมูลของ P2 ใช้แค่ 3 แบบที่เป็น Must

| answer_format | ใช้กับโจทย์ | ตัวอย่าง |
|---|---|---|
| `expression` | หาค่าหรือนิพจน์ (รวมถึงอนุพันธ์และค่าลิมิต) | หา dy/dx, หาค่า lim |
| `factored` | สั่งให้แยกตัวประกอบ | แยกตัวประกอบ x³ − x |
| `equation` | หาคำตอบของสมการ หรือเซตคำตอบ | หาจุดวิกฤต (แก้ f'(x) = 0) |

### รูปแบบไฟล์ · `answers/labels.jsonl` (1 บรรทัด = 1 คำตอบ)

```json
{"id": "ans_001", "image": "../handwriting/raw/hw_014.jpg", "writer": "w03", "problem": "\\frac{d}{dx}\\left(x^{2}\\cos(x)\\right)", "answer_format": "expression", "reference": "2x\\cos(x)-x^{2}\\sin(x)", "lines": ["2x\\cos(x)+x^{2}\\sin(x)"], "verdict": "incorrect", "error_type": "sign", "first_wrong_line": 1, "method": "doc", "labeled_by": "May"}
{"id": "ans_002", "image": null, "writer": "w01", "problem": "\\text{แยกตัวประกอบ } x^{3}-x", "answer_format": "factored", "reference": "x(x-1)(x+1)", "lines": ["x^{3}-x", "x(x^{2}-1)"], "verdict": "incomplete", "error_type": "concept", "first_wrong_line": null, "method": "doc", "labeled_by": "May"}
{"id": "ans_003", "image": null, "writer": "w02", "problem": "\\lim_{x \\to 0} \\frac{x+1}{x+2}", "answer_format": "expression", "reference": "\\frac{1}{2}", "lines": ["\\lim_{x \\to 0} \\frac{1}{1}", "1"], "verdict": "incorrect", "error_type": "wrong_method", "first_wrong_line": 1, "method": "doc", "labeled_by": "May"}
```

- `reference` คือเฉลยที่ถูก ถ้าโจทย์มาจากข้อสอบเก่าที่ไม่มีเฉลย ให้แก้เองแล้วให้อีกคนตรวจ
- `image` ใส่ `null` ได้ถ้าเป็นคำตอบที่พิมพ์
- error_type ใน JSON ใช้ตัวเล็กและ `_` แทนช่องว่าง (`wrong_method`, `no_answer`)

### ใบงาน · `answers/worksheet.md`

ไม่ต้องแก้ `labels.jsonl` เอง ให้กรอกใบงาน แล้วให้ script สร้างไฟล์และตรวจกติกาให้ · แผนเดิมคือให้ May หรือ Junior label เพราะ Jam ทำ P2 (PR #51) · **รอบแรก (21 ต.ค., PR #52) ทีม (May + Jam) ตกลงให้ AI (Claude) ร่าง label ทั้ง 50 ข้อและเขียนคำตอบพิมพ์ ans_031–050 (writer `w06`)** · ดูข้อจำกัดและการตรวจซ้ำใน "กฎ"

1. ใบงานมี 50 หัวข้อ (`ans_001`–`ans_050`) · 30 ข้อแรกมาจากรูปลายมือที่ label `lines` ไว้แล้วใน `handwriting/` · 20 ข้อหลังเป็นคำตอบแบบพิมพ์ (`image: none`)
2. **ข้อพิมพ์:** ใส่ `problem_id` (P01–P17 ในตารางของ `handwriting/problems.md`), `writer` และบรรทัดคำตอบแบบ ``1. `x(x^{2}-1)` `` ทีละบรรทัด · script ดึงโจทย์, เฉลย และ `answer_format` จาก `problem_id` เอง · เขียนคำตอบผิดให้ได้ตามโควตาด้านล่าง
3. **ทุกข้อ:** กรอก `verdict`, `error_type`, `first_wrong_line`, `method` (ว่าง = `doc`) และ `labeled_by` ตามคู่มือข้างบน · ข้อไหนยังไม่กรอก `verdict` ถือว่ายังไม่ label
4. รัน `uv run --project apps/api python evals/answers/make_worksheet.py --build` · ถ้ามีข้อไหนผิดกติกา script บอก id ของข้อนั้นและไม่เขียนไฟล์ · ถ้าผ่าน ได้ `labels.jsonl` เฉพาะข้อที่ label แล้ว จึงทำทีละส่วนได้
5. **ห้ามเปิด** `handwriting/raw/copy-sheets/copy_sheets_key.md` (เฉลยว่ารูปไหนตั้งใจผิด) จนกว่าจะ label ครบ

**โควตาคำตอบพิมพ์ 20 ข้อ** (รูปลายมือมีบรรทัดผิดแค่ ~8 รูป จึงเติมให้ error type ทุกแบบมีข้อมูล)

| แบบ | จำนวน |
|---|---|
| `sign` | 3 |
| `prerequisite` | 3 |
| `wrong_method` | 3 |
| `concept` (เป็น `incomplete` อย่างน้อย 1) | 3 |
| `calculation` | 3 |
| `no_answer` | 2 |
| `correct_with_flaw` | 2 |
| `correct` + `method: other` | 1 |

สร้างใบงานใหม่: `uv run --project apps/api python evals/answers/make_worksheet.py` (ไม่เขียนทับถ้ามีใบงานอยู่แล้ว) · test: `uv run --project apps/api pytest evals/answers`

### การให้คะแนน · `run_eval.py --purpose check_answer`

เป้าหมายของทั้ง 3 ตัวมาจาก P2 ใน `specs/poc/README.md` (และ `ai-orchestration.md` §2.4.8) · ทีมตกลงนิยามเมื่อ 21 ต.ค. (PR #47)

| metric | นับว่าตรงเมื่อ | ตัวหาร | เป้า |
|---|---|---|---|
| verdict accuracy | `verdict` ตรงกับ label ทั้ง 4 ค่า | ทุกข้อใน `labels.jsonl` | ≥ 95% |
| error_type accuracy | `error_type` ตรงกับ label · ถ้า checker ไม่ตอบ (`null`) นับว่าไม่ตรง | ข้อที่ label มี verdict ไม่ใช่ `correct` | ≥ 80% |
| first_wrong_line accuracy | `first_wrong_line` ตรงกับ label | ข้อที่ label มี `first_wrong_line` ไม่ใช่ `null` | ≥ 85% |

- แสดง **verdict แบบ 2 ค่า** ประกอบด้วย คือดูแค่ "นับว่าถูก" (`correct`) หรือ "นับว่าผิด" (อีก 3 ค่า) ตามตาราง verdict ด้านบน · ใช้ดูประกอบ ไม่ใช่เป้า
- ไม่นับข้อที่ label เป็น `null` ใน first_wrong_line เพราะถ้านับ `null` ตรง `null` ว่าถูก คะแนนจะสูงเกินจริง · ข้อที่ label เป็น `null` แต่ checker ชี้บรรทัด จะไปโผล่เป็น verdict ผิดอยู่แล้ว
- ข้อที่มีใน label แต่ไม่มีใน prediction นับว่าไม่ตรงทุก metric ที่ข้อนั้นอยู่ในตัวหาร และแสดงจำนวนไว้ในผล
- ถ้ามี id ใน prediction ที่ไม่มีใน label หรือมี id ซ้ำ script จะหยุดและแจ้ง error
- ถ้าตัวหารของ metric ไหนเป็น 0 (เช่นไม่มีข้อไหนที่ label มีเลขบรรทัด) accuracy เป็น `null` และนับว่าไม่ผ่าน
- ผ่านเมื่อทั้ง 3 ตัวถึงเป้า · ถ้าไม่ผ่าน script จะคืน exit code 1 (ไว้ใช้ใน CI ตาม §2.11)

**ไฟล์ prediction** (JSONL 1 บรรทัด = 1 คำตอบ · field ตาม output ของ §2.4.5)

```json
{"id": "ans_001", "verdict": "incorrect", "error_type": "sign", "first_wrong_line": 1}
```

ใส่ field อื่นของ §2.4.5 มาด้วยได้ (`evidence`, `method`, `decided_by`, `confidence`) · script ไม่ใช้ในการให้คะแนน

## กฎ

- คน label ไม่ใช่คนทำ PoC ตัวนั้น
  - **ข้อยกเว้น: golden set ของ P2 รอบแรก AI ร่าง label** (ทีมตกลง 21 ต.ค., PR #52) · `labeled_by` ในไฟล์เป็น `May` ทุกข้อ แต่หมายถึงคนที่วางไฟล์ ไม่ใช่คนที่ตัดสิน
  - ผลที่ตามมา: label อาจเอนไปทางเดียวกับ checker ที่เป็น LLM ทำให้ verdict และ error_type accuracy **สูงเกินจริง**
  - ก่อนเขียน report P2: คนที่ไม่ใช่ Jam ตรวจซ้ำ**ทุกข้อที่ไม่ใช่ `correct` (28 ข้อ)** เพราะ error_type เป็น metric ที่เสี่ยงที่สุด · ข้อที่ไม่เห็นด้วยให้แก้ใน `worksheet.md` แล้ว `--build` ใหม่ · report P2 รายงานว่าแก้ไปกี่ข้อจาก 28
- ขอความยินยอมก่อนใช้ลายมือของเพื่อน และไม่ commit รูปลง repo สาธารณะ
- เป้าหมายของแต่ละ eval อยู่ใน `specs/poc/README.md`
