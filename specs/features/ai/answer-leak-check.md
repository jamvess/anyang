# Feature: answer-leak check (ข้อความ tutor ต้องไม่มีเฉลยของโจทย์ที่ยังรอคำตอบ)

| | |
|---|---|
| Area | platform |
| Requirements | AM-13 (tutor reply ต้องไม่มีเฉลยของโจทย์ที่ยังรอคำตอบ · answer-leak check แบบ deterministic) |
| Owner | Jam |
| Reviewer | Jam · Junior ดูย้อนหลัง (gateway ใช้ตอนต่อ) |
| Status | approved 2026-11-22 (Jam · §10 ข้อ 1–4 ตามข้อเสนอ · ข้อ 5 ตัดสินใน PR ต่อ gateway) |
| Related system spec | ai-orchestration.md §2.9 "Answer-leak check" (string match + SymPy → generate ใหม่) · `config/ai.yaml` → `guards.answer_leak_check` · demo-room.md §2 C (prompt รับโจทย์ไม่รับเฉลย), §2 K ข้อ 7 (ระหว่างใบ้ส่ง `none` แทนเฉลย) · `app/domain/room.py` (`_plain`: เขียน LaTeX แบบเดียวกัน) · `app/domain/hint_ladder.py` (`_UNEVALUATED`) · `app/math/sympy_service.py` (`_classify`, `_in_factored_form`, `SympyWorkerPool.run`) |

## 1. Context

prompt ของห้องติวไม่ได้รับเฉลยอยู่แล้ว (`tutor_reply/v2` รับแค่ข้อความโจทย์ · hint ladder ส่ง `none`) แต่ LLM แก้โจทย์เองได้แล้วพิมพ์คำตอบออกมา ซึ่งขัด AM-13 · ai-orchestration §2.9 ให้ code ตรวจข้อความของ tutor ด้วย string match และ SymPy แล้ว generate ใหม่ถ้าพบเฉลย · feature นี้ทำ**ตัวตรวจ**อย่างเดียว: บอกได้แบบ deterministic ว่าข้อความหนึ่งมีเฉลยของโจทย์ค้างหรือไม่ · การต่อเข้า gateway และการรับมือกับ stream เป็น PR ถัดไปหลังส่งวิดีโอ 23 พ.ย. (§10 ข้อ 5)

## 2. Behavior

### 2.1 ส่วนของข้อความที่ตรวจ

1. ตรวจเฉพาะ math ใน `$…$` และ `$$…$$` ของข้อความ (prompt ทุกตัวของห้องติวบังคับให้เขียนสูตรแบบนี้ · `tutor_reply/v2` "Inline math between single dollar signs") · `\$` ไม่ใช่ math
2. แต่ละ math block แตกเป็น **ส่วน** ด้วย `,` และ `=` ที่อยู่นอกวงเล็บ (`_split_top_level` แบบเดียวกับ `sympy_service`) · เก็บทั้งส่วนเดี่ยว (`3x^2`) และคู่ซ้าย-ขวาของ `=` (`x=7`) ไว้ใช้กับ `equation`
3. normalize ทุกส่วนและเฉลยด้วยกฎเดียวกับ `room._plain` (ตัดช่องว่างรวม zero-width · `\dfrac`/`\tfrac` → `\frac` · ตัด `\left`/`\right`/`\limits` · `x^{2}` → `x^2`)

### 2.2 ขั้นที่ 1 · string match (pure · `app/domain/answer_leak.py`)

`leaks_by_text(reply, reference_answer, answer_format) -> bool`

- `expression`, `factored`: ส่วนใดส่วนหนึ่ง = เฉลยหลัง normalize → หลุด
- `equation`: เฉลยแตกด้วย `,` เป็นคำตอบย่อย (`x=7`, `x=-7`) · คู่ `ตัวแปร=ค่า` ใน math block ตรงกับคำตอบย่อยข้อใดข้อหนึ่ง → หลุด (คำตอบครึ่งเดียวนับว่าหลุด · §10 ข้อ 2) · กลับข้าง (`7=x`) ไม่นับในขั้นนี้ (SymPy จับในขั้นที่ 2)
- ไม่มี math block → ไม่หลุด

### 2.3 ขั้นที่ 2 · SymPy (`app/math/answer_leak.py` · รันใน `SympyWorkerPool` พร้อม `checker.sympy_timeout_seconds`)

`leaks_by_sympy(answer_format, reference_answer, problem_expression, parts) -> bool` · รันเมื่อขั้นที่ 1 ไม่พบ · ส่วนที่ parse ไม่ได้ข้ามไป

ส่วนที่ "**เขียนในรูปคำตอบสุดท้าย**" และมีค่าเท่าเฉลย → หลุด (§10 ข้อ 1):

| `answer_format` | ค่าเท่ากัน | รูปคำตอบสุดท้าย (กันไม่ให้นับตัวโจทย์) |
|---|---|---|
| `factored` | SymPy เท่ากับเฉลย | อยู่ในรูปแยกตัวประกอบแล้ว (`_in_factored_form`) · `x^2-49` เท่ากับ `(x-7)(x+7)` แต่ไม่ใช่รูปแยกตัวประกอบ จึงไม่นับ |
| `expression` | SymPy เท่ากับเฉลย | ไม่มี operator ที่ยังไม่คำนวณ (`hint_ladder._UNEVALUATED`: `\frac{d}{dx}`, `\lim`, `\int`, `\sum`, `d/dx`) และไม่ใช่ตัวโจทย์ (`problem_expression` หลัง normalize ไม่ตรงกัน · SymPy ไม่ถือว่าเท่ากันแบบ "เขียนเหมือนกัน") |
| `equation` | คู่ `ตัวแปร=ค่า` หรือ `ค่า=ตัวแปร` ที่ค่าไม่มีตัวแปร และค่านั้นอยู่ในเซตคำตอบของเฉลย | ฝั่งหนึ่งเป็นตัวแปรเดี่ยว อีกฝั่งไม่มีตัวแปร · `x^2=49` ไม่ใช่รูปคำตอบ จึงไม่นับ |

### 2.4 รวมสองขั้น (`app/math/answer_leak.py`)

`async check_leak(reply, problem, *, enabled=None, timeout_s=None, pool=None) -> LeakResult` · `problem: LeakProblem(reference_answer, answer_format, expression)` · ค่า default แบบเดียวกับ `check_lines`: `enabled` → `guards.answer_leak_check` · `timeout_s` → `checker.sympy_timeout_seconds` · `pool` → pool ที่ใช้ร่วม · ส่วนของ math ได้จาก `math_parts(reply)` (§2.1 · `app/domain/answer_leak.py`)

1. `guards.answer_leak_check = false` → ไม่หลุด (`checked = false`)
2. ขั้นที่ 1 พบ → หลุด (`method = "text"`)
3. ขั้นที่ 2 พบ → หลุด (`method = "sympy"`)
4. SymPy timeout หรือ worker ล้ม → **ไม่หลุด** (`method = "sympy_timeout"` · ให้ผู้เรียก log) · §10 ข้อ 4

`LeakResult(leaked: bool, method: "text" | "sympy" | "sympy_timeout" | None, part: str | None)` · `part` = ส่วนที่ทำให้หลุด (สำหรับ log · ไม่ส่งให้ผู้ใช้)

### 2.5 ใครต้องเรียก (ใช้ตอนต่อ · §10 ข้อ 3)

ข้อความของ tutor ขณะที่**มีโจทย์รอคำตอบ**: `tutor_reply`, `open_session` (โจทย์ข้อแรก) และ `explain_check` เมื่อ directive คือ `continue`, `hint_1`, `hint_2`, `ask_working` (โจทย์ยังค้าง) · ไม่ตรวจ `explain_check` ที่ `reveal` และ `praise_and_show` เพราะตั้งใจแสดงวิธีทำเต็ม · ไม่มีโจทย์ค้าง → ไม่ตรวจ

## 3. Inputs and outputs

| | Type / schema | ตัวอย่าง |
|---|---|---|
| Input | `reply: str` · `problem` (`reference_answer`, `answer_format`, `expression`) | `"ลองแยกตัวประกอบ $x^2-49$ ดูนะ คำตอบคือ $(x+7)(x-7)$"` · เฉลย `(x-7)(x+7)` · `factored` · โจทย์ `x^2-49` |
| Output | `LeakResult(leaked, method, part)` | `(True, "sympy", "(x+7)(x-7)")` (ลำดับต่างจากเฉลย ขั้นที่ 1 ไม่พบ ขั้นที่ 2 พบ) |

## 4. Acceptance criteria

ทุกข้อเป็น unit test · ไม่เรียก AI · SymPy ผ่าน pool ของ test (แบบเดียวกับ `test_sympy_service.py`) · ตัวอย่างจากโจทย์ของเดโม่

**ขั้นที่ 1 · string (AM-13)**

- **AC-1 (AM13)** `factored`: ข้อความมี `$(x-7)(x+7)$` (เขียนต่างแค่ช่องว่าง, `\left(`, `x^{2}`) → หลุด `method = "text"`
- **AC-2 (AM13)** `expression`: `$\frac{d}{dx}x^3 = 3x^2$` เฉลย `3x^2` → หลุด (ส่วนขวาของ `=`) · `$\dfrac{1}{2}$` กับเฉลย `\frac{1}{2}` → หลุด
- **AC-3 (AM13)** `equation` เฉลย `x=7, x=-7`: มี `$x = 7$` อย่างเดียว → หลุด (ครึ่งเดียว) · มี `$x=-7, x=7$` → หลุด
- **AC-4 (AM13)** ไม่หลุด: ไม่มี math block · มีแค่ตัวโจทย์ `$x^2-49$` · สูตรทั่วไป `$$a^2-b^2=(a-b)(a+b)$$` · `\$7` (ไม่ใช่ math) · เลขที่มีเฉลยอยู่ข้างใน (`$17$` เมื่อเฉลย `7`)

**ขั้นที่ 2 · SymPy (AM-13)**

- **AC-5 (AM13)** `factored`: `$(x+7)(x-7)$` (สลับลำดับ) → หลุด `method = "sympy"` · `$x^2-49$` → ไม่หลุด (ไม่ใช่รูปแยกตัวประกอบ)
- **AC-6 (AM13)** `expression`: `$6x \cdot \frac{x}{2}$` เมื่อเฉลย `3x^2` → หลุด · `$\frac{d}{dx}x^3$` → ไม่หลุด (operator ยังไม่คำนวณ) · ตัวโจทย์ที่เขียนเหมือน `expression` → ไม่หลุด
- **AC-7 (AM13)** `equation`: `$7 = x$` → หลุด · `$x^2 = 49$` → ไม่หลุด · `$x = 5$` → ไม่หลุด (ไม่อยู่ในเซตคำตอบ)
- **AC-8 (AM13)** ส่วนที่ parse ไม่ได้ (`$\text{ลองดู}$`) ข้ามไป ไม่ทำให้ล้ม

**รวม (AM-13)**

- **AC-9 (AM13)** `guards.answer_leak_check = false` → `leaked = false`, ไม่เรียก SymPy
- **AC-10 (AM13)** SymPy timeout (pool ที่ timeout เสมอ) → `leaked = false`, `method = "sympy_timeout"`
- **AC-11 (AM13)** ขั้นที่ 1 พบแล้วไม่เรียก SymPy (pool ที่นับจำนวนครั้ง = 0)

**AC-boundary:** ไม่มี threshold ใหม่ (timeout ใช้ `checker.sympy_timeout_seconds` ที่ test อยู่แล้วใน `test_sympy_service_timeout.py`) · **AC-tenant:** ไม่อ่านหรือเขียนข้อมูล

## 5. Data changes

ไม่มี

## 6. API / SSE changes

ไม่มี

## 7. AI calls

ไม่มี (code ล้วน)

## 8. Test plan

| Test | ระดับ | ครอบคลุม AC |
|---|---|---|
| `tests/unit/test_answer_leak_text.py` (table-driven) | unit | AC-1 ถึง AC-4 |
| `tests/unit/test_answer_leak_sympy.py` (เรียก `leaks_by_sympy` ตรงๆ เหมือน `evaluate_lines` + `check_leak` กับ pool ปลอม) | unit | AC-5 ถึง AC-11 |

## 9. Out of scope

- ต่อเข้า gateway / ห้องติว: เรียก `check_leak` ใน purpose ตาม §2.5, generate ใหม่, ข้อความสำรองเมื่อยังหลุด, log ลง `ai_calls` (PR ถัดไปหลัง 23 พ.ย. · §10 ข้อ 5)
- buddy (S6) · ข้อความที่ไม่ใช่ math (เช่น "ตอบเจ็ด") · `numeric` (Should · ยังไม่มีใน `AnswerFormat`)

## 10. Open questions

ตัดสินแล้ว (Jam 2026-11-22): ข้อ 1–4 ตามข้อเสนอ · ข้อ 5 เป็นข้อเสนอสำหรับ PR ต่อ gateway

1. **อะไรนับว่าหลุดในขั้น SymPy:** ข้อเสนอ: ตามตาราง §2.3 (ค่าเท่าเฉลย **และ** เขียนในรูปคำตอบสุดท้าย) · เหตุผล: ถ้านับแค่ค่าเท่ากัน ตัวโจทย์เองจะหลุดทุกครั้ง (`x^2-49` = `(x-7)(x+7)` · `\frac{d}{dx}x^3` = `3x^2`) · ผลข้างเคียงที่ต้องรู้: `expression` ที่เป็นขั้นกลางแต่ค่าเท่าเฉลยแล้ว (`3x^{3-1}` ของ hint_2 "ทำให้ดู 1 ขั้น") นับว่าหลุด เพราะเหลือแค่คิดเลข · ทางอื่น: (ข) string อย่างเดียว ไม่มี SymPy (พลาดการสลับลำดับ `(x+7)(x-7)`)
2. **คำตอบครึ่งเดียว (`equation` ที่มีหลายราก):** ข้อเสนอ: นับว่าหลุด เพราะบอกรากไป 1 ตัวแล้ว
3. **ใครต้องเรียก:** ข้อเสนอ: ตาม §2.5 (`tutor_reply`, `open_session`, `explain_check` ตอนโจทย์ยังค้าง · ไม่ตรวจ `reveal`, `praise_and_show`)
4. **SymPy timeout:** ข้อเสนอ: ถือว่าไม่หลุด (fail open) + log · เหตุผล: ขั้นที่ 1 ตรวจไปแล้ว และ generate ใหม่ทุกครั้งที่ timeout ทำให้ช้ากว่า 2 เท่า · ทางอื่น: ถือว่าหลุด (ปลอดภัยกว่า แต่ช้า)
5. **stream (สำหรับ PR ต่อ ไม่ตัดสินใน PR นี้):** `tutor_reply`, `open_session`, `explain_check` เป็น stream ส่ง token ทันที จึง "generate ใหม่" หลังผู้ใช้เห็นแล้วไม่ได้ · ข้อเสนอที่จะเขียนใน spec ของ PR ต่อ: gateway ส่ง text ออกได้จนถึง `$` ที่เปิดอยู่ แล้วกักไว้จนกว่า math block จะปิดและตรวจผ่าน · เจอหลุด → หยุด stream, ตัด block นั้น แล้ว generate ต่อ 1 ครั้ง (ค่าใน `guards`) · ยังหลุด → ข้อความสำรองจาก code

## 11. Spec changes needed

- ไม่แตะไฟล์กลางใน PR นี้ (`guards.answer_leak_check` มีแล้ว)
- PR ต่อ gateway: §10 ข้อ 5 · ค่าใหม่ใน `config/ai.yaml` `guards` (จำนวนครั้งที่ generate ใหม่) · แก้ ai-orchestration §2.9 ให้บอกวิธีกับ stream
