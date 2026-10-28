# Feature: LLM classifier `check_answer` และ pipeline ตรวจคำตอบ 1 ข้อ

| | |
|---|---|
| Area | checker |
| Requirements | AM-06 (error type), AM-05 (first wrong line เมื่อ SymPy ชี้ไม่ได้), AM-04 (SymPy ตัดสินก่อน) · AI-01, AI-05 (ผ่าน gateway + schema) |
| Owner | Jam |
| Reviewer | Junior |
| Status | draft |
| Related system spec | ai-orchestration.md §2.4.1–§2.4.5, §2.4.8 · `specs/features/check/merge-rules.md` · `specs/features/check/sympy-service.md` · `evals/README.md` "คู่มือ label golden set คำตอบ · P2", "การให้คะแนน" · `specs/poc/README.md` P2 |

## 1. Context

checker มี 3 ส่วน (§2.4.1) · SymPy service (PR #75) กับ merge rules (PR #68) เสร็จแล้ว · feature นี้คือส่วนที่เหลือ:

1. **LLM classifier** `check_answer` (§2.4.4): บอกว่าผิดแบบไหน (`error_type`), ชี้หลักฐาน, บอกว่าใช้วิธีตามชีทไหม (`method`) และเมื่อ SymPy ตัดสินไม่ได้ ให้ verdict + บรรทัดที่ผิด + `confidence` แทน
2. **pipeline ตรวจ 1 ข้อ** `check_answer()`: SymPy → LLM → `merge_check` → `CheckResult` · ใช้ทั้งใน checker ของห้องติว (ทำทีหลัง) และใน eval
3. **`evals/run_checker.py`**: รัน pipeline กับ golden set 50 ข้อ แล้วเขียนไฟล์ prediction ให้ `run_eval.py` ออกตัวเลข 3 ตัวของ P2

ไม่อ่านหรือเขียน DB · คนเรียกเป็นคนเขียน `attempts`, `checker_disagreements` และส่ง SSE `verdict`

## 2. Behavior

### 2.1 Pipeline `check_answer(problem, lines)`

1. **ไม่มีคำตอบ** (`lines` ว่าง) → ไม่เรียก SymPy และไม่เรียก LLM · `merge_check` ตัดสิน `incorrect` / `no_answer` เอง (merge-rules ข้อ 1) · ค่า `llm` ที่ส่งเข้า merge เป็นค่าที่ code สร้าง (ดู §10 ข้อ 1)
2. `sympy = await check_lines(answer_format, reference_answer, lines)` (sympy-service.md)
3. `llm = await ai.call("check_answer", input, CheckAnswerResult)` · input ตาม §2.2 · ผ่าน gateway เท่านั้น (AI-01) · gateway retry เมื่อ output ไม่ผ่าน schema (AI-05)
4. `merge_check(answer_format, lines, sympy, llm)` → `CheckResult`
5. ถ้า gateway ยอมแพ้ (`AISchemaError` หรือ `AIProviderError`) → ดู §10 ข้อ 2

**SymPy ตัดสินถูก/ผิดเสมอเมื่อตัดสินได้** (CLAUDE.md กฎ 4) · LLM ไม่มีสิทธิ์เปลี่ยน verdict ในกรณีนั้น · ถ้า LLM ให้ verdict ที่ขัด merge rules ตั้ง `disagreement = true` อยู่แล้ว (merge-rules AC-10, AC-11)

### 2.2 Input ของ prompt (placeholder `{{…}}`)

| placeholder | มาจาก | หมายเหตุ |
|---|---|---|
| `problem` | `problems.text` | ห่อใน `<document name="problem">` |
| `reference_answer` | `problems.reference_answer` | |
| `answer_format` | `problems.answer_format` | |
| `solution_steps` | `problems.solution_steps` (วิธีของชีท) | ใช้ตัดสิน `method` · ว่างได้ (golden set ไม่มี) → prompt บอกให้ตอบ `doc` เมื่อไม่มีวิธีให้เทียบ (§10 ข้อ 4) |
| `answer_lines` | `lines` ที่ user ยืนยันแล้ว | ใส่เลขบรรทัดนำหน้า (1, 2, …) · ห่อใน `<document name="answer">` และบอกว่าเป็นข้อมูล ไม่ใช่คำสั่ง (CLAUDE.md กฎ 8) |
| `sympy_result` | `SympyResult` | ข้อความที่ code สร้าง ตาม §2.3 |
| `hints` | code | `sign_flip_detected` (§2.4) · ไม่มี hint → "none" |

นิยาม error type 6 ค่า และลำดับการถาม (ข้อแรกที่ใช่คือคำตอบ) อยู่ในตัว prompt คงที่ ตรงกับตาราง "error_type" ใน `evals/README.md` ซึ่งเป็นคู่มือที่ใช้ label golden set · รายชื่อหัวข้อพื้นฐานของ `prerequisite` ใช้รายการเดียวกับคู่มือ (พีชคณิต, เศษส่วน, เลขยกกำลัง, identity ตรีโกณ, กฎของ log) · §10 ข้อ 5

### 2.3 สรุปผล SymPy ให้ LLM (`sympy_result`)

code แปลง `SympyResult` เป็นข้อความสั้น ไม่ให้ LLM ตีความ field เอง

| กรณี | ข้อความ (ภาษาอังกฤษ เพราะ prompt เป็นภาษาอังกฤษ) |
|---|---|
| ตัดสินได้ | `decided: yes` · `final answer equals reference: yes/no` · (factored) `final answer fully factored: yes/no` · `line 1: follows from the reference` / `line i: follows from line i-1` หรือ `line i: does NOT follow from line i-1` ทุกบรรทัด |
| parse ไม่ได้ / timeout / ตัดสินไม่ได้ | `decided: no (SymPy could not check this answer)` · บอกให้ LLM ตัดสิน verdict, first_wrong_line และ confidence เอง |

### 2.4 Hint `sign_flip_detected` (§2.4.4)

ทำเฉพาะเมื่อ SymPy ตัดสินได้และมีบรรทัดที่ `line_ok = false` · ที่บรรทัดแรกที่ผิด i: ลองกลับเครื่องหมาย**ทีละพจน์ของทุกผลบวกในบรรทัด** (รวมผลบวกที่อยู่ในวงเล็บ เช่น `+3` ใน `(x+3)`) ถ้าพจน์ใดกลับแล้ว `line_ok` ของบรรทัด i เป็นจริงตามกฎ §2.4 ของ sympy-service → hint `sign_flip_detected: line i` · คำนวณใน worker ของ SymPy service พร้อม timeout เดียวกัน · §10 ข้อ 3

### 2.5 Output ของ LLM `CheckAnswerResult` (Pydantic · `app/models/check.py`)

| field | type | กติกา |
|---|---|---|
| `error_type` | 6 ค่าของ AM-06 หรือ `null` | `null` ได้เฉพาะเมื่อ LLM เห็นว่าคำตอบถูก |
| `evidence` | `str` ภาษาไทย 1 ประโยค | ชี้บรรทัดและสิ่งที่ผิด เช่น "บรรทัด 2: −3 กลายเป็น +3" · ว่างได้เมื่อถูก |
| `method` | `doc` \| `other` | |
| `verdict` | 4 ค่า หรือ `null` | ต้องมีเมื่อ `decided: no` · เมื่อ `decided: yes` ให้ตอบตามที่ LLM เห็นด้วย (ใช้เก็บ disagreement · §10 ข้อ 6) |
| `first_wrong_line` | `int ≥ 1` หรือ `null` | ใช้เมื่อ SymPy ตัดสินไม่ได้ หรือเมื่อทุกบรรทัด follow แต่คำตอบสุดท้ายผิด (merge-rules ข้อ 6 · เช่น ans_037, ans_038 ที่เลือกวิธีผิด) |
| `confidence` | `float` 0–1 | ใช้เมื่อ `decided_by = llm` เท่านั้น |

แปลงเป็น `LlmResult` (`app/domain/checker.py`) ก่อนส่งเข้า merge · `first_wrong_line` ที่มากกว่าจำนวนบรรทัด → `null` (code ตัด ไม่ให้ LLM ชี้บรรทัดที่ไม่มี)

### 2.6 `evals/run_checker.py`

- อ่าน `evals/answers/labels.jsonl` · แต่ละข้อสร้างโจทย์จาก `problem`, `reference`, `answer_format`, `solution_steps = []` แล้วเรียก `check_answer()`
- เขียน `evals/answers/predictions/<prompt>.jsonl` ตามรูปแบบใน `evals/README.md` (`id`, `verdict`, `error_type`, `first_wrong_line` + `evidence`, `method`, `decided_by`, `confidence`, `disagreement`)
- รันทีละข้อตามลำดับ (free tier มีเพดาน request ต่อนาที · gateway retry เองเมื่อโดน rate limit)
- ใช้ provider ตาม `AI_PROVIDER` · fake ใน test · live เมื่อ Jam รันเอง (ขั้น 6 ใน worklog)
- ข้อที่ gateway ยอมแพ้ (§10 ข้อ 2) ไม่เขียน prediction และพิมพ์ id ไว้ · `run_eval.py` นับข้อที่ไม่มี prediction ว่าไม่ตรง
- หลังรัน ให้คนรัน `run_eval.py --purpose check_answer --prompt v1 --predictions …` ต่อ

## 3. Inputs and outputs

| | Type / schema | ตัวอย่าง |
|---|---|---|
| Input `problem` | `CheckProblem`: `text: str` · `reference_answer: str` · `answer_format: AnswerFormat` · `solution_steps: list[str]` | `text="\text{แยกตัวประกอบ } x^{3}-x"`, `reference_answer="x(x-1)(x+1)"`, `answer_format="factored"`, `solution_steps=[]` |
| Input `lines` | `list[str]` LaTeX ที่ user ยืนยันแล้ว | `["x^{3}-x", "=x(x^{2}-1)"]` |
| LLM output | `CheckAnswerResult` (§2.5) | `{"error_type": "concept", "evidence": "บรรทัด 2: x^2−1 ยังแยกต่อได้", "method": "doc", "verdict": "incomplete", "first_wrong_line": null, "confidence": 0.9}` |
| Output | `CheckResult` (`app/domain/checker.py`) | `verdict="incomplete"`, `error_type="concept"`, `decided_by="sympy"` |

ลายเซ็น: `async def check_answer(problem: CheckProblem, lines: list[str]) -> CheckResult`

## 4. Acceptance criteria

ทุกข้อใช้ fake provider (AI-03) · ผล LLM ปลอมเขียนเป็น JSON ใน test · ตัวอย่างจาก golden set

**pipeline**

- **AC-1 (AM-04, AM-06)** Given ans_001 (factored, `x(x^{2}-1)`) และ LLM ปลอมตอบ `error_type="calculation"` When `check_answer` Then `verdict=incomplete`, `error_type=concept`, `decided_by=sympy` (SymPy + merge rules ชนะ LLM)
- **AC-2 (AM-06)** Given ans_007 (sign error บรรทัด 3) และ LLM ปลอมตอบ `error_type="sign"`, `evidence="บรรทัด 3: …"` When `check_answer` Then `verdict=incorrect`, `first_wrong_line=3`, `error_type=sign`, `evidence` ตามที่ LLM ให้
- **AC-3 (AM-05)** Given ans_037 (ทุกบรรทัด follow แต่คำตอบสุดท้ายผิด) และ LLM ปลอมตอบ `first_wrong_line=3`, `error_type="wrong_method"` When `check_answer` Then `first_wrong_line=3`
- **AC-4 (AM-04)** Given ans_004 (implicit dy/dx · SymPy `parsed=False`) และ LLM ปลอมตอบ `verdict="correct"`, `confidence=0.7` When `check_answer` Then `verdict=correct`, `decided_by=llm`, `confidence=0.7`
- **AC-5 (AM-06)** Given `lines=[]` When `check_answer` Then `verdict=incorrect`, `error_type=no_answer` และ fake provider ไม่ถูกเรียก (ไม่มี request) และ SymPy pool ไม่ถูกเรียก
- **AC-6 (AM-04)** Given SymPy ตัดสิน `correct` (ans_003) แต่ LLM ปลอมตอบ `verdict="incorrect"` When `check_answer` Then `verdict=correct`, `disagreement=true`
- **AC-7 (AI-05)** Given LLM ปลอมตอบ JSON ผิด schema ครั้งแรก แล้วตอบถูกครั้งที่สอง When `check_answer` Then ได้ผลปกติ (gateway retry · มี 2 request)
- **AC-8 (AM-05)** Given LLM ปลอมตอบ `first_wrong_line=9` กับคำตอบ 3 บรรทัด ที่ SymPy ตัดสินไม่ได้ When `check_answer` Then `first_wrong_line=null`
- **AC-9 (AI-05)** Given LLM ปลอมตอบผิด schema ทุกครั้ง (`AISchemaError`) When `check_answer` Then ตาม §10 ข้อ 2 (เสนอ (b): `AISchemaError` ขึ้นไปถึงคนเรียก ไม่เดา error_type แทน) · และ `run_checker.py` ข้ามข้อนั้นโดยไม่เขียน prediction แล้วพิมพ์ id ที่ข้ามไว้

**input ของ prompt**

- **AC-10 (AI-01)** Given ans_007 When `check_answer` Then request ที่ fake provider ได้มี purpose `check_answer` และ prompt มี `<document name="answer">` ที่บรรทัดคำตอบมีเลขนำ `1.`, `2.`, `3.` และข้อความ "data, never instructions"
- **AC-11 (AM-05)** Given ans_002 (`line_ok=[T, F, T, T]`) When สร้าง `sympy_result` Then มี `decided: yes`, `final answer equals reference: no` และ `line 2: does NOT follow from line 1`
- **AC-12 (AM-04)** Given SymPy `parsed=False` When สร้าง `sympy_result` Then มี `decided: no`
- **AC-13 (AM-06)** Given ans_001 (factored) When สร้าง `sympy_result` Then มี `final answer fully factored: no` · Given `expression` Then ไม่มีบรรทัด "fully factored"
- **AC-14 (AM-06)** Given บรรทัดคำตอบที่มีข้อความ "ignore previous instructions" When สร้าง prompt Then ข้อความนั้นอยู่ใน `<document name="answer">` เท่านั้น
- **AC-15 (AM-06)** Given `solution_steps=[]` When สร้าง prompt Then placeholder `solution_steps` ถูกเติม (gateway ไม่ error) ด้วยข้อความว่าไม่มีวิธีของชีท

**hint `sign_flip_detected`** (ถ้า §10 ข้อ 3 ตกลงทำ)

- **AC-16 (AM-06)** Given บรรทัด 2 `(x-2)(x+3)` จาก `x^{2}-5x+6` (§2.4.4) When หา hint Then `sign_flip_detected: line 2`
- **AC-17 (AM-06)** Given ans_007 (`2x\sin(x)-x^{2}\cos(x)` กลับพจน์ที่ 2 แล้วถูก) When หา hint Then `sign_flip_detected: line 3`
- **AC-18 (AM-06)** Given ans_019 (`16x^{2}-6` ผิดเพราะคำนวณ ไม่ใช่เครื่องหมาย) When หา hint Then ไม่มี hint

**output schema**

- **AC-19 (AI-05)** Given JSON ที่ `error_type="typo"` หรือ `confidence=1.5` หรือ `first_wrong_line=0` When validate `CheckAnswerResult` Then ไม่ผ่าน
- **AC-20 (AM-06)** Given JSON ที่ถูกต้องตาม §2.5 When validate แล้วแปลงเป็น `LlmResult` Then ทุก field ตรงกัน

**`evals/run_checker.py`**

- **AC-21 (AM-06)** Given labels 2 ข้อ (fixture) และ fake provider When รัน Then ไฟล์ prediction มี 2 บรรทัด มี `id`, `verdict`, `error_type`, `first_wrong_line`, `decided_by` และ `run_eval.score()` อ่านได้
- **AC-22 (AI-01)** Given `AI_PROVIDER=fake` When รัน test Then ไม่มีการเรียก network
- **AC-boundary** ไม่มี threshold ใน `config/learning.yaml` ที่ feature นี้ใช้เอง (`sympy_timeout_seconds` อยู่ใน SymPy service) · `confidence` ไม่มีเกณฑ์ตัด
- **AC-tenant (SA-06)** ไม่เกี่ยว: ไม่อ่านหรือเขียน DB

**eval กับ model จริง** (ไม่อยู่ใน CI · Jam รันเอง)

- **AC-live (AM-06)** Given golden set 50 ข้อ When `run_checker.py` แล้ว `run_eval.py` Then ได้ verdict, error_type, first_wrong_line เทียบเป้า P2 (≥ 95%, ≥ 80%, ≥ 85%) · ผลนี้ใช้ตัดสิน P2 ไม่ใช่ test ที่ต้องเขียว

## 5. Data changes

ไม่มี · `CheckResult` ใช้เขียน `attempts` (มี `decided_by`, `sympy_result`) และ `checker_disagreements` ในภายหลัง · `attempts.first_wrong_line` และ `method` รอ migration ของ Junior (merge-rules §11)

## 6. API / SSE changes

ไม่มี

## 7. AI calls

| Purpose | Tier | Output schema | Prompt file |
|---|---|---|---|
| `check_answer` | `mid` (`config/ai.yaml` · temperature 0, max_tokens 600, timeout 15 s) | `CheckAnswerResult` | `prompts/check_answer/v1.md` |

## 8. Test plan

| Test | ระดับ | ครอบคลุม AC |
|---|---|---|
| `apps/api/tests/unit/test_check_answer_pipeline.py` (fake provider + FakePool ของ SymPy หรือ `evaluate_lines`) | unit | AC-1 ถึง AC-15 |
| `apps/api/tests/unit/test_check_answer_model.py` | unit | AC-19, AC-20 |
| `apps/api/tests/unit/test_sign_flip.py` | unit | AC-16 ถึง AC-18 |
| `evals/test_run_checker.py` | unit | AC-21, AC-22 |
| `run_checker.py` + `run_eval.py` กับ Gemini (Jam รัน) | eval | AC-live |

## 9. Out of scope

- เขียน `attempts`, `checker_disagreements` · SSE `verdict` · dispute (AM-12, `dispute_recheck`)
- `normalize_math` (คำตอบที่พิมพ์ → LaTeX) · `extract_answer` (รูป → LaTeX)
- self-consistency ของโจทย์ที่ `verified = false` (§2.4.6)
- ดึงวิธีของชีทจาก grounding chunk (§2.4.2) · feature นี้รับ `solution_steps` ที่มีอยู่แล้ว
- Report P2 (`/poc-report P2` หลัง merge)

## 10. Open questions

1. **ค่า `llm` เมื่อไม่มีคำตอบ** · merge_check ต้องการ `LlmResult` แต่ไม่เรียก LLM
   - **เสนอ:** code สร้าง `LlmResult(error_type="no_answer", evidence="", method="doc", verdict=None, first_wrong_line=None, confidence=1.0)` · merge rules ข้อ 1 ไม่อ่านค่าเหล่านี้อยู่แล้ว
2. **LLM ล้มเหลวหลัง retry ครบ** (schema หรือ provider)
   - (a) ใช้ผล SymPy + merge ต่อ โดย `error_type` = ค่าที่ code เดาได้ไม่มี → เสนอ `concept`? · เสี่ยงให้ข้อมูลผิดกับ mastery และ tutor
   - (b) ให้ error ขึ้นไปถึงคนเรียก แล้วห้องติวบอก user ว่าตรวจไม่ได้ ลองใหม่
   - **เสนอ (b)** · ไม่เดา error_type แทน LLM · ใน eval นับข้อนั้นเป็นไม่มี prediction (`run_eval.py` นับว่าไม่ตรง)
3. **hint `sign_flip_detected`** ทำใน PR นี้ไหม · golden set มี `sign` 6 ข้อ `calculation` 4 ข้อ
   - **เสนอ:** ทำ (§2.4.4 กำหนดไว้แล้ว · ต้องเพิ่มฟังก์ชันใน `app/math/sympy_service.py` ที่รันใน worker เดิม ไม่เปลี่ยน `SympyResult`)
4. **`method` เมื่อไม่มี `solution_steps`** (golden set ทุกข้อ · label `other` มี 1/50)
   - **เสนอ:** ตอบ `doc` · `method` ไม่อยู่ใน 3 metric ของ P2 · วัดจริงหลังมี grounding chunk
5. **รายชื่อหัวข้อพื้นฐาน** (§2.4.4 "รายชื่อหัวข้อพื้นฐาน") มาจากไหน
   - **เสนอ:** ใช้รายการคงที่ในคู่มือ label (`evals/README.md`) ใส่ในตัว prompt · MVP ไม่ดึงจาก prerequisite ของ scope
6. **ขอ verdict จาก LLM ทุกครั้งไหม** (merge-rules AC-12 บอกว่า "ปกติ" `verdict=None` เมื่อ SymPy ตัดสินได้)
   - (a) ขอทุกครั้ง · ได้ข้อมูล disagreement ไว้ดูว่า LLM กับ SymPy ขัดกันบ่อยแค่ไหน · token เพิ่มเล็กน้อย
   - (b) ขอเฉพาะเมื่อ `decided: no`
   - **เสนอ (a)** · `checker_disagreements` (§2.4.5) มีไว้เพื่อสิ่งนี้
7. **เรียก LLM เมื่อ SymPy ตัดสิน `correct` ทุกบรรทัดไหม** (22/50 ข้อ) · ต้องการแค่ `method`
   - **เสนอ:** เรียก เพื่อได้ `method` และ disagreement · ตัดทีหลังได้ถ้าต้นทุนหรือ latency สูง (วัดตอน P4-lite)
8. **ที่อยู่ของ pipeline** · `apps/api/app/services/checker.py` (โฟลเดอร์ `services/` ของ Junior ตาม `apps/api/CLAUDE.md` "orchestration")
   - **เสนอ:** ที่นี่ · Junior review

## 11. Spec changes needed

- `config/ai.yaml` (ไฟล์ร่วม) · `check_answer` ตั้ง `max_tokens: 600` และไม่ได้ตั้ง `thinking` · ถ้า thinking ของ Gemini 3 กิน token จน JSON ขาด (P3 เคยเจอใน flow 2.3) ต้องเพิ่ม `thinking: low` หรือเพิ่ม `max_tokens` · **ดูจากผลรันจริงขั้น 6 ก่อน แล้วขอทีม**
- `evals/README.md` (Jam) · อัปเดตย่อหน้า "ตอนนี้ `run_eval.py` ให้คะแนนจากไฟล์ prediction ยังไม่ได้เรียก checker เอง" ให้ชี้ไปที่ `run_checker.py`
- `merge-rules.md` · ไม่ต้องแก้ ถ้า §10 ข้อ 6 เลือก (a) เพราะ AC-10/AC-11 รองรับ verdict ของ LLM อยู่แล้ว
