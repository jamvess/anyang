# Feature: SymPy service ของ checker (ตัดสินถูก/ผิดรายบรรทัด)

| | |
|---|---|
| Area | checker |
| Requirements | AM-04, AM-05 |
| Owner | Jam |
| Reviewer | Junior |
| Status | draft |
| Related system spec | ai-orchestration.md §2.4.1, §2.4.2, §2.4.3 · `specs/features/check/merge-rules.md` §3 · architecture.md (Math: subprocess + timeout) · `evals/README.md` "คู่มือ label ลายมือ · P1" |

## 1. Context

checker มี 3 ส่วน (§2.4.1): **SymPy ตัดสินว่าถูกหรือผิด และผิดตั้งแต่บรรทัดไหน** · LLM จำแนก error_type · merge rules (`app/domain/checker.py`) รวมผล

feature นี้คือส่วนแรก อยู่ใน `apps/api/app/math/sympy_service.py` · รับคำตอบรายบรรทัดที่ user ยืนยันแล้ว (LaTeX) กับเฉลยของโจทย์ แล้วคืน `SympyResult` ตามที่ตกลงกับ Junior ใน merge-rules §3 · คนเรียกคือ checker service (ทำทีหลัง) ซึ่งส่งผลต่อให้ `merge_check` และเก็บลง `attempts.sympy_result` · ไม่เรียก AI ไม่อ่านหรือเขียน DB

## 2. Behavior

### 2.1 เตรียมบรรทัด (normalize)

ทำกับทุกบรรทัดและกับเฉลย ก่อน parse

1. ตัด `\left`, `\right`, `\,` `\;` `\:` `\!` `\ ` และ `$` ออก (เหมือน `poc/P1/lines.py`)
2. ตัด `=` ที่ต้นบรรทัด (กติกาลายมือข้อ 5 ให้พิมพ์ `=` ตามที่เขียน)
3. แยกส่วนด้วย `,` ระดับบนสุด (ไม่อยู่ในวงเล็บ) เช่น `x=0, x=\ln(2)` เป็น 2 ส่วน
4. parse ด้วย `sympy.parsing.latex.parse_latex(..., backend="antlr")` · **ไม่ใช้ `lark`** เพราะ P1 พบว่าอ่าน `2x\sin(x)+x^{2}\cos(x)` ผิดโดยไม่แจ้ง
5. แทน symbol `e` ด้วยค่าคงที่ `E` (parser อ่าน `e^{x}` เป็นตัวแปร `e` ทำให้แก้ `e^{x}=1` ไม่ได้ · ทดลองแล้ว 28 ต.ค.)

ถ้าบรรทัดใดหรือเฉลย parse ไม่ได้ (เช่น มี `\text{…}` หรือ `\?`) → ทั้งข้อ `parsed = false`

### 2.2 ชนิดของบรรทัด

| ชนิด | รูป | ค่า (value) ที่ใช้เทียบ |
|---|---|---|
| expression | นิพจน์ไม่มี `=` (หลังตัด `=` ต้นบรรทัด) | นิพจน์หลัง `.doit()` คือ derivative, limit, integral **ถูกคำนวณ** (ต่างจาก P1 ที่เทียบตามที่เขียน) เพราะบรรทัด 1 มักเป็นตัวโจทย์ และบรรทัดถัดไปเป็นผลที่คำนวณแล้ว |
| definition | `f(x)=E`, `f'(x)=E`, `f''(x)=E`, `f'''(x)=E` (ชื่อฟังก์ชันตัวเดียว) · อันดับ k = จำนวน `'` | `E` |
| equation | `A=B` ที่ไม่ใช่ definition หรือหลายส่วนคั่น `,` เช่น `e^{x}=1, e^{x}=2`, `x=0, x=\ln(2)` | solution set บนจำนวนจริง (`solveset(A − B, x, Reals)`) · หลายส่วน = union ของทุกส่วน |

ตัวแปร x คือ free symbol ตัวเดียวของเฉลย (ถ้าเฉลยไม่มี symbol เลยหรือมีหลายตัว → ใช้ free symbol ตัวเดียวของบรรทัด · ถ้ายังหาไม่ได้ตัวเดียว → `parsed = false`)

### 2.3 คำตอบสุดท้าย (`final_equal`, `final_in_form`)

คำตอบสุดท้าย = บรรทัดสุดท้าย

| answer_format | `final_equal` | `final_in_form` |
|---|---|---|
| `expression` | `simplify(value(last) − value(เฉลย)) == 0` (§2.4.3) | `null` |
| `factored` | เหมือน expression | `true` เมื่อทุกตัวประกอบที่ไม่ใช่ค่าคงที่ของบรรทัดสุดท้าย **ตามที่เขียน** ลดรูปต่อไม่ได้บนจำนวนตรรกยะ (เท่ากับจำนวนตัวประกอบใน `factor_list`) · เช่น `x(x^{2}-1)` → `false`, `3(x+2)` → `true` |
| `equation` | solution set ของบรรทัดสุดท้าย = solution set ของเฉลย (ลำดับไม่มีผล) | `null` |

### 2.4 รายบรรทัด (`line_ok`)

`line_ok[i]` = บรรทัด i + 1 ถูกเมื่อเทียบกับบรรทัดก่อนหน้า (ยาวเท่า `lines`) · บรรทัดแรกที่เป็น `false` คือ first wrong line ที่ merge rules หาเอง (merge-rules §10 ข้อ 1)

**บรรทัด 1 เทียบกับเฉลย** แทนการเทียบกับตัวโจทย์ · เหตุผล: `problems.text` เป็นข้อความไทยปนคณิต parse ตรงๆ ไม่ได้ และ AM-11 รับประกันว่าค่าของโจทย์ = เฉลยแล้ว จึงให้ผลเหมือนกัน (เช่น `\lim_{x \to 2} \frac{x^{2}-4}{x^{2}-3x+2}` มีค่า 4 = เฉลย)

กฎการเทียบบรรทัดก่อนหน้า P กับบรรทัดปัจจุบัน C

| P | C | `line_ok` เป็น true เมื่อ |
|---|---|---|
| (บรรทัด 1) เฉลย | expression | value(C) = value(เฉลย) |
| (บรรทัด 1) เฉลย | equation (`equation` format) | solution set(C) = solution set(เฉลย) |
| (บรรทัด 1) — | definition | true เสมอ ถือว่าเขียนโจทย์ซ้ำ (ดู §10 Q1) |
| expression | expression | value(C) = value(P) |
| definition อันดับ j | definition อันดับ k > j | E_C = d^(k−j)/dx^(k−j) E_P |
| definition | expression | value(C) = E_P |
| definition | equation (`equation` format) | solution set(C) = solution set(E_P = 0) · ขั้น "ตั้งอนุพันธ์เท่ากับ 0" เช่น `f'(x)=3x^{2}-6x-9` → `3x^{2}-6x-9=0` |
| equation | equation | solution set(C) = solution set(P) (§2.4.3 "solution set ของแต่ละบรรทัดต้องเท่าเดิม") |
| อื่นๆ | | ไม่รองรับ → ทั้งข้อ `parsed = false` (เช่น equation ใน `expression` format แบบ implicit dy/dx · §10 Q2) |

### 2.5 ตัดสินไม่ได้ และ timeout

- การเทียบใดที่ SymPy ตอบไม่ได้แน่ชัด (เช่น `solveset` คืน `ConditionSet`) → `final_equal = null` และ `line_ok = []` · merge rules ถือว่า SymPy ตัดสินไม่ได้ แล้วใช้ผลของ LLM (merge-rules §2 "final_equal = null")
- งานทั้งข้อ (parse + เทียบทุกบรรทัด) รันใน **worker process แยก** พร้อม timeout `checker.sympy_timeout_seconds` จาก `config/learning.yaml` · timeout คิดต่อ 1 คำตอบ เพราะค่านี้ตั้งเป็น budget ให้ verdict มาทัน TTFT p95 · เกินเวลา → `timed_out = true`, `parsed = true`, `final_equal = null`, `final_in_form = null`, `line_ok = []` แล้วหยุด worker ตัวนั้นและเปิดใหม่
- **ไม่เปิด process ใหม่ทุกครั้ง:** วัดแล้ว (28 ต.ค.) การเปิด Python + import SymPy ใช้ 1.9 วินาที เกือบเท่า budget · จึงใช้ worker ที่เปิดค้างไว้ (pool) · จำนวน worker ดู §10 Q4
- เป็นฟังก์ชัน `async` ไม่บล็อก event loop ของ FastAPI (CLAUDE.md ของ api: "Never call `simplify` in the request thread directly")

### 2.6 ไม่มีคำตอบ

`lines = []` → คืนทันทีโดยไม่เรียก SymPy: `parsed = false`, `timed_out = false`, ค่าอื่น `null`, `line_ok = []` · merge rules จับ no answer จาก `lines` ว่างเองก่อน (merge-rules §2 ข้อ 1)

ไม่มี threshold อื่นนอกจาก `checker.sympy_timeout_seconds`

## 3. Inputs and outputs

| | Type / schema | ตัวอย่าง |
|---|---|---|
| Input `answer_format` | `expression` \| `factored` \| `equation` (`AnswerFormat` ใน `app/domain/checker.py`) | `factored` |
| Input `reference_answer` | `str` LaTeX จาก `problems.reference_answer` | `x(x-1)(x+1)` |
| Input `lines` | `list[str]` LaTeX ที่ user ยืนยันแล้ว | `["x^{3}-x", "=x(x^{2}-1)"]` |
| Input `timeout_s` (optional) | `float` · ไม่ส่ง = อ่านจาก settings | `2` |
| Output `SympyResult` (dataclass เดิมใน `app/domain/checker.py`) | `parsed: bool` · `timed_out: bool` · `final_equal: bool \| None` · `final_in_form: bool \| None` · `line_ok: list[bool]` | `parsed=True, timed_out=False, final_equal=True, final_in_form=False, line_ok=[True, True]` |

ลายเซ็น: `async def check_lines(*, answer_format, reference_answer, lines, timeout_s=None) -> SympyResult`

## 4. Acceptance criteria

ตัวอย่างมาจาก `evals/answers/labels.jsonl` (ans_xxx) · ไม่มี AI · ทุกข้อ (ยกเว้นที่บอกไว้) คาดว่า `parsed=True, timed_out=False`

**expression**

- **AC-1 (AM-04)** Given ans_003 (limit → ∞, เฉลย `\frac{3}{2}`) When ตรวจ Then `final_equal=True`, `line_ok=[True, True, True, True]`, `final_in_form=None`
- **AC-2 (AM-04)** Given บรรทัด 1 เป็นตัวโจทย์ `\frac{d}{dx}\left(x^{2}\sin(x)\right)` และเฉลย `2x\sin(x)+x^{2}\cos(x)` When ตรวจ Then `line_ok[0]=True` (derivative ถูกคำนวณ)
- **AC-3 (AM-05)** Given ans_002 (`\lim_{x \to 2}`, บรรทัด 2 ตัดพจน์ผิด, ตอบ 1, เฉลย 4) When ตรวจ Then `line_ok=[True, False, True, True]`, `final_equal=False`
- **AC-4 (AM-05)** Given ans_007 (บรรทัด 3 `2x\sin(x)-x^{2}\cos(x)`) When ตรวจ Then `line_ok=[True, True, False]`, `final_equal=False`
- **AC-5 (AM-04)** Given ans_010 (`e^{x^{2}}\cdot 2x\cdot\ln(x)+e^{x^{2}}\cdot\frac{1}{x}` เทียบ `2xe^{x^{2}}\ln(x)+\frac{e^{x^{2}}}{x}`) When ตรวจ Then `final_equal=True` (เทียบทางคณิตศาสตร์ ไม่ใช่ string)
- **AC-6 (AM-04)** Given บรรทัดที่มี `\left( \right)`, `\,` และ `=` ต้นบรรทัด When ตรวจ Then ผลเหมือนบรรทัดที่ไม่มีสิ่งเหล่านั้น
- **AC-7 (AM-04)** Given ans_016 (`3\cdot\frac{\sin(3x)}{3x}` ใต้ `\lim_{x \to 0}`) When ตรวจ Then `final_equal=True` และทุก `line_ok` จริง

**definition (f, f′, f″)**

- **AC-8 (AM-04)** Given ans_017 (`f(x)=…`, `f'(x)=4x^{3}-6x+2`, `f''(x)=12x^{2}-6`, `expression`, เฉลย `12x^{2}-6`) When ตรวจ Then `line_ok=[True, True, True]`, `final_equal=True`
- **AC-9 (AM-05)** Given ans_019 (บรรทัด 3 `f''(x)=16x^{2}-6`) When ตรวจ Then `line_ok=[True, True, False]`, `final_equal=False`

**factored**

- **AC-10 (AM-04)** Given ans_001 (`factored`, ตอบ `x(x^{2}-1)`, เฉลย `x(x-1)(x+1)`) When ตรวจ Then `final_equal=True`, `final_in_form=False`, `line_ok=[True, True]`
- **AC-11 (AM-04)** Given ans_006 (`(x-2)(x+2)(x^{2}+4)`) และ ans_015 (`(x-2)^{2}(x+2)`) When ตรวจ Then `final_in_form=True`
- **AC-12 (AM-04)** Given `factored`, เฉลย `3(x+2)`, ตอบ `3(x+2)` When ตรวจ Then `final_in_form=True` (ค่าคงที่ไม่นับเป็นตัวประกอบ และ parser ต้องไม่กระจาย `3(x+2)` เป็น `3x+6`) · Given ตอบ `3x+6` Then `final_equal=True`, `final_in_form=False`
- **AC-13 (AM-04)** Given `expression` หรือ `equation` When ตรวจ Then `final_in_form=None`

**equation**

- **AC-14 (AM-04)** Given ans_005 (`e^{2x}-3e^{x}+2=0` → `e^{x}=1, e^{x}=2` → `x=0, x=\ln(2)`) When ตรวจ Then `line_ok` จริงทุกบรรทัด, `final_equal=True` (`e` คือค่าคงที่ และแก้บนจำนวนจริง ไม่ได้ `2πik`)
- **AC-15 (AM-04)** Given ans_012 (ตอบ `x=1, x=-1`, เฉลย `x=-1, x=1`) When ตรวจ Then `final_equal=True` (ลำดับไม่มีผล)
- **AC-16 (AM-05)** Given ans_018 (จุดวิกฤต: `f(x)=…`, `f'(x)=3x^{2}-6x-9`, `3x^{2}-6x-9=0`, …, `(x-3)(x+1)=0`, `x=3, x=1`) When ตรวจ Then `line_ok=[True, True, True, True, True, False]`, `final_equal=False`
- **AC-17 (AM-05)** Given ans_008 (บรรทัด 5 `(x+3)(x-1)=0`, บรรทัด 6 `x=-3, x=1`) When ตรวจ Then `line_ok=[True, True, True, True, False, True]` (บรรทัด 6 เท่าบรรทัด 5 จึงจริง · merge rules ใช้บรรทัดแรกที่ผิด = 5)

**ตัดสินไม่ได้**

- **AC-18 (AM-04)** Given บรรทัดที่ parse ไม่ได้ (`\text{ดังนั้น } x=1` หรือ `x^{\?}`) When ตรวจ Then `parsed=False`, `final_equal=None`, `final_in_form=None`, `line_ok=[]`
- **AC-19 (AM-04)** Given เฉลย parse ไม่ได้ When ตรวจ Then `parsed=False`
- **AC-20 (AM-04)** Given ans_004 (implicit dy/dx: บรรทัดเป็นสมการของ x, y ใน `expression` format) When ตรวจ Then `parsed=False` (ไม่รองรับ · §10 Q2)
- **AC-21 (AM-04)** Given การเทียบที่ SymPy ตอบไม่ได้แน่ชัด (เช่น solution set เป็น `ConditionSet`) When ตรวจ Then `parsed=True`, `final_equal=None`, `line_ok=[]`
- **AC-22 (AM-06 ส่งต่อ)** Given `lines=[]` When ตรวจ Then `parsed=False`, `line_ok=[]` และไม่เรียก worker

**timeout (`checker.sympy_timeout_seconds`)**

- **AC-23 (AM-04)** Given งานใน worker ใช้เวลาเกิน timeout (test ใส่งานที่ค้าง และ timeout เล็ก) When ตรวจ Then คืนภายในเวลา timeout บวกเวลาหยุด worker · `timed_out=True`, `parsed=True`, `final_equal=None`, `line_ok=[]`
- **AC-24 (AM-04)** Given เพิ่งเกิด timeout ตาม AC-23 When ตรวจคำตอบปกติข้อถัดไป Then ได้ผลถูกต้อง (worker ถูกเปิดใหม่)
- **AC-boundary (AM-04)** งานที่เสร็จก่อน timeout → `timed_out=False` · งานที่เกิน → `timed_out=True` · ไม่ test ที่ "= timeout พอดี" เพราะเวลาจริงไม่แน่นอน
- **AC-25 (AM-04)** Given ไม่ส่ง `timeout_s` When ตรวจ Then ใช้ค่า `checker.sympy_timeout_seconds` จาก settings (ไม่มีตัวเลขใน code)

**ต่อกับ merge rules**

- **AC-26 (AM-04)** Given ผลของ ans_001 จาก service ส่งเข้า `merge_check` (LLM ปลอม) When รวมผล Then `verdict=incomplete` ตรงกับ label
- **AC-tenant (SA-06)** ไม่เกี่ยว: ไม่อ่านหรือเขียนข้อมูล

## 5. Data changes

ไม่มี · `attempts.sympy_result` (jsonb, มีอยู่แล้วใน `data-model.md`) เก็บ `SympyResult` นี้ · คนเรียกเป็นคนเขียน

## 6. API / SSE changes

ไม่มี

## 7. AI calls

ไม่มี

## 8. Test plan

| Test | ระดับ | ครอบคลุม AC |
|---|---|---|
| `tests/unit/test_sympy_service.py` แบบ table-driven (`parametrize`) ใช้ ans_xxx จาก golden set เป็น fixture | unit | AC-1 ถึง AC-22, AC-25, AC-26 |
| `tests/unit/test_sympy_service_timeout.py` งานที่ค้าง + timeout เล็ก | unit | AC-23, AC-24, AC-boundary |
| รัน service กับ 50 ข้อใน `evals/answers/labels.jsonl` นับ parse ได้, timeout, `final_equal` ตรงกับ label (worklog ขั้น 7) | eval | ทั้งหมด (ตัวเลขตั้งต้นให้ P2) |

## 9. Out of scope

- verify เฉลยของโจทย์ที่ AI สร้าง (AM-11, §2.4.6, `checker.max_generate_retries`) · ใช้ worker เดียวกันได้ทีหลัง
- `numeric`, `short_text`, `sql`, `solution_set` (Should / Could)
- implicit differentiation (§10 Q2) · inequality · integral ที่ SymPy คำนวณไม่ได้
- hint `sign_flip_detected` ให้ LLM (§2.4.4) · ทำตอนต่อ prompt `check_answer`
- checker service ที่เรียก service นี้ + LLM + merge แล้วเขียน `attempts`

## 10. Open questions

1. **บรรทัด definition บรรทัดแรก** (`f(x)=…` ที่ user เขียนโจทย์ซ้ำ) ไม่มีอะไรให้เทียบ เพราะ service ไม่ได้รับตัวโจทย์
   - (a) ถือว่าถูกเสมอ · ถ้าลอกโจทย์ผิด คำตอบสุดท้ายจะผิด แล้ว merge rules ใช้ first_wrong_line ของ LLM (merge-rules ข้อ 6) · ไม่ต้องเพิ่ม input
   - (b) เพิ่ม input `problem_text` แล้วดึงคณิตที่อยู่นอก `\text{…}` มาเทียบ · แม่นกว่าแต่เปราะ (ข้อความไทยปน)
   - **เสนอ (a)** · golden set ที่มี definition ทั้ง 11 ข้อเขียน `f(x)=` ซ้ำในบรรทัด 1 ถูกทุกข้อ
2. **implicit dy/dx (P12 · 3 ข้อใน golden set)** บรรทัด 1 → 2 คือการ differentiate ทั้งสองข้าง ไม่ใช่สมการที่เท่ากัน
   - **เสนอ:** ไม่รองรับใน MVP → `parsed=False` → LLM ตัดสินพร้อม confidence (merge-rules ข้อ 2) · กระทบเป้า P2 สูงสุด 3/50 ข้อ ถ้า LLM พลาด
3. **บรรทัดที่มี `=` หลายตัว** เช่น `=\frac{1^{2}+1}{1+1}=\frac{2}{2}=1` (กติกาลายมือข้อ 5 อนุญาต)
   - **เสนอ:** `expression` / `factored` → แยกด้วย `=` ระดับบนสุดแล้วตรวจเป็นหลายขั้นย่อยในบรรทัดเดียว บรรทัดถูกเมื่อทุกขั้นย่อยถูก · `equation` → ถ้าส่วนใดส่วนหนึ่ง (หลังแยก `,`) มี `=` มากกว่า 1 ตัว (เช่น `f'(x)=3x^{2}-6x-9=0`) ไม่รองรับ → `parsed=False`
   - golden set 50 ข้อยังไม่มีบรรทัดแบบนี้ (ที่มี `=` หลายตัวเป็นรายการคั่น `,` อย่าง `x=0, x=\ln(2)` ทั้งหมด) จึงไม่กระทบตัวเลข P2
4. **จำนวน worker** · ค่านี้ไม่ใช่ threshold ของ learning model แต่ CLAUDE.md กฎ 5 ห้ามตัวเลขลอย
   - **เสนอ:** เพิ่ม `checker.sympy_workers: 1  # [C]` ใน `config/learning.yaml` · 1 ตัวต่อ Cloud Run instance พอสำหรับ pilot · วัดใหม่ตอน P4-lite ถ้ามีคิวรอ
5. **`line_ok` ตอนตัดสินไม่ได้** · merge-rules §3 เขียนว่า `line_ok` "ยาวเท่า `lines`" แต่ตอน parse ไม่ได้หรือ timeout ไม่มีค่าที่ถูกต้องให้ใส่
   - **เสนอ:** คืน `[]` (merge rules ไม่อ่าน `line_ok` ในกรณีนี้อยู่แล้ว) และเพิ่มประโยคใน merge-rules §3 ว่า "ยาวเท่า `lines` เมื่อ `parsed` และไม่ `timed_out` และ `final_equal` ไม่เป็น `null`"

## 11. Spec changes needed

- `apps/api/pyproject.toml` (Junior) · เพิ่ม `antlr4-python3-runtime==4.11` (parser ของ `parse_latex` แบบ `antlr` · ต้องเป็น 4.11 ให้ตรงกับ grammar ของ SymPy)
- `specs/features/check/merge-rules.md` §3 · ประโยคเรื่อง `line_ok` ว่าง (Q5) · Junior ตกลงรูปแบบนี้ไว้ จึงต้องให้ Junior OK
- `specs/system/ai-orchestration.md` §2.4.3 (Jam) · เพิ่มว่าบรรทัด 1 เทียบกับเฉลย, กฎของบรรทัด definition (f, f′, f″), `e` คือค่าคงที่, solution set บนจำนวนจริง, worker ที่เปิดค้างไว้
- `config/learning.yaml` (Jam + Junior) · `checker.sympy_workers` ถ้า Q4 ตกลง
