# Feature: merge rules ของ checker (รวมผล SymPy + LLM เป็น verdict)

| | |
|---|---|
| Area | checker |
| Requirements | AM-04, AM-05, AM-06 (+ PM-01 เฉพาะ field ที่ส่งต่อ) |
| Owner | Jam |
| Reviewer | Junior |
| Status | approved (Jam + Junior · 21 ต.ค.) |
| Related system spec | ai-orchestration.md §2.4.1, §2.4.3, §2.4.4, §2.4.5, §2.4.9 · `evals/README.md` "คู่มือ label golden set คำตอบ · P2" |

## 1. Context

checker มี 3 ส่วน: SymPy ตัดสินถูก/ผิดและบรรทัดที่ผิด · LLM (`check_answer`) จำแนก error_type และชี้หลักฐาน · **code รวมผลตามกฎที่ตายตัว** (§2.4.1) · feature นี้คือส่วนที่ 3 เป็นฟังก์ชันล้วนใน `apps/api/app/domain/` (CLAUDE.md กฎ 1 "Code decides") · รับผลของ 2 ส่วนแรกเข้ามา คืน verdict ที่ทั้ง `attempts` และ SSE `verdict` ใช้ · ไม่เรียก AI ไม่อ่านหรือเขียน DB

## 2. Behavior

ตัดสินตามลำดับนี้ ข้อแรกที่ตรงเงื่อนไขคือผล

1. **ไม่มีคำตอบ** (§2.4.4 "no answer ตัดสินด้วย code"): `lines` ว่าง → `incorrect`, `error_type = no_answer`, `first_wrong_line = null`
2. **SymPy ตัดสินไม่ได้** (parse ไม่ได้ หรือ timeout เกิน `checker.sympy_timeout_seconds` · §2.4.3 Safety) → ใช้ verdict, error_type, first_wrong_line และ `confidence` ของ LLM · `decided_by = llm`
3. **คำตอบสุดท้ายถูก และอยู่ในรูปที่โจทย์สั่ง และทุกบรรทัดถูก** → `correct` · `method` ตาม LLM (`doc` หรือ `other`) · error_type และ first_wrong_line เป็น `null`
4. **คำตอบสุดท้ายถูก และอยู่ในรูปที่โจทย์สั่ง แต่มีบรรทัดผิด** (ผิดสองทีหักล้างกัน) → `correct_with_flaw` · first_wrong_line = บรรทัดแรกที่ SymPy บอกว่าไม่เท่าบรรทัดก่อน · error_type ตาม LLM
5. **ค่าเท่าเฉลยแต่ไม่อยู่ในรูปที่โจทย์สั่ง** (เช่น `factored` ที่ยังแยกไม่หมด) → `incomplete` · **error_type = `concept` เสมอ** (code กำหนด ไม่ใช้ของ LLM · §2.4.5) · first_wrong_line = `null` (ตามคู่มือ label)
6. **คำตอบสุดท้ายผิด** → `incorrect` · first_wrong_line = บรรทัดแรกที่ไม่เท่าบรรทัดก่อน · ถ้าทุกบรรทัดเท่ากันหมด ให้ใช้ `first_wrong_line` ของ LLM และถ้า LLM ไม่ให้มา ให้ใช้บรรทัดสุดท้าย · error_type ตาม LLM

เมื่อข้อ 4 หรือ 6 ต้องใช้ error_type ของ LLM ถือว่า LLM ส่งมาเสมอ: schema ของ `check_answer` บังคับ field นี้ และ gateway retry เมื่อ output ไม่ผ่าน schema (AI-05)

ข้อ 1 และ 3–6 ใช้ `decided_by = sympy` และ `confidence = 1.0` (code และ SymPy ไม่เดา) · **ถ้า LLM ให้ verdict มาด้วยแล้วขัดกับ SymPy เรื่องถูก/ผิด ให้ใช้ผลของ SymPy** และตั้ง `disagreement = true` ให้คนเรียกไปบันทึก `checker_disagreements` (§2.4.5)

**นับ mastery** (`is_correct`): `true` เฉพาะ `correct` (รวม `method: other`) · `correct_with_flaw`, `incomplete`, `incorrect` เป็น `false` (§2.4.9 ข้อ 2)

"อยู่ในรูปที่โจทย์สั่ง" ใช้เฉพาะ `factored` (เทียบ `factor_list` · §2.4.3) · `expression` และ `equation` ถือว่าอยู่ในรูปแล้วเสมอ

ไม่มี threshold ใน `config/learning.yaml` ที่ feature นี้ใช้เอง (`sympy_timeout_seconds` ใช้ใน SymPy service ซึ่งส่งผลมาเป็น `timed_out`)

## 3. Inputs and outputs

| | Type / schema | ตัวอย่าง |
|---|---|---|
| Input `answer_format` | `expression` \| `factored` \| `equation` | `factored` |
| Input `lines` | `list[str]` (LaTeX ที่ user ยืนยันแล้ว) | `["x^{3}-x", "x(x^{2}-1)"]` |
| Input `sympy` (ตกลงกับ Junior 21 ต.ค. · ผลของ SymPy service `app/math/`) | `parsed: bool` · `timed_out: bool` · `final_equal: bool \| None` · `final_in_form: bool \| None` · `line_ok: list[bool]` ยาวเท่า `lines` (บรรทัด i เท่าบรรทัด i − 1 · บรรทัด 1 เทียบกับโจทย์) | `parsed=True, timed_out=False, final_equal=True, final_in_form=False, line_ok=[True, True]` |
| Input `llm` (output ของ `check_answer`) | `error_type: ErrorType \| None` · `evidence: str` · `method: "doc" \| "other"` · `verdict: Verdict \| None` · `first_wrong_line: int \| None` · `confidence: float` | `error_type="sign", evidence="บรรทัด 2: −3 กลายเป็น +3", method="doc", verdict=None, confidence=0.9` |
| Output `CheckResult` | `verdict` · `final_answer_correct: bool` · `first_wrong_line: int \| None` (นับจาก 1) · `error_type` · `evidence` · `method` · `decided_by: "sympy" \| "llm"` · `confidence: float` · `is_correct: bool` · `disagreement: bool` | ตาม §2.4.5 + `is_correct`, `disagreement` |

## 4. Acceptance criteria

ตัวอย่างข้อมูลมาจาก `evals/README.md` (ans_001–003) และโจทย์ P01–P17 · ทุกข้อใช้ผล SymPy และ LLM ปลอม

- **AC-1 (AM-04)** Given `expression`, SymPy `final_equal=True`, `line_ok` จริงทุกบรรทัด, LLM `method="doc"` When รวมผล Then `verdict=correct`, `is_correct=true`, `error_type=null`, `first_wrong_line=null`, `decided_by=sympy`
- **AC-2 (AM-04)** Given เหมือน AC-1 แต่ LLM `method="other"` When รวมผล Then `verdict=correct`, `method=other`, `is_correct=true`
- **AC-3 (AM-05)** Given `final_equal=True`, `line_ok=[True, False, False, True]` (ผิดสองทีหักล้างกัน), LLM `error_type="sign"` When รวมผล Then `verdict=correct_with_flaw`, `first_wrong_line=2`, `error_type=sign`, `is_correct=false`
- **AC-4 (AM-04)** Given `factored`, `final_equal=True`, `final_in_form=False` (ans_002: `x(x^{2}-1)`), LLM `error_type="calculation"` When รวมผล Then `verdict=incomplete`, `error_type=concept` (ไม่ใช่ของ LLM), `first_wrong_line=null`, `is_correct=false`
- **AC-5 (AM-05, AM-06)** Given `expression`, `final_equal=False`, `line_ok=[False]` (ans_001: บวกแทนลบ), LLM `error_type="sign"` When รวมผล Then `verdict=incorrect`, `first_wrong_line=1`, `error_type=sign`, `is_correct=false`
- **AC-6 (AM-05)** Given `final_equal=False`, `line_ok=[True, True, False, False]` When รวมผล Then `first_wrong_line=3` (บรรทัดแรกที่ผิด ไม่ใช่บรรทัดสุดท้าย)
- **AC-7 (AM-06)** Given `lines=[]` (ไม่ว่า SymPy และ LLM จะส่งอะไรมา) When รวมผล Then `verdict=incorrect`, `error_type=no_answer`, `first_wrong_line=null`
- **AC-8 (AM-04)** Given SymPy `parsed=False`, LLM `verdict="incorrect"`, `error_type="concept"`, `first_wrong_line=2`, `confidence=0.6` When รวมผล Then ใช้ค่าของ LLM ทั้งหมด, `decided_by=llm`, `confidence=0.6`
- **AC-9 (AM-04)** Given SymPy `timed_out=True` (parse ได้) When รวมผล Then ทำเหมือน AC-8 (`decided_by=llm`)
- **AC-10 (AM-04)** Given SymPy ตัดสิน `correct` (แบบ AC-1) แต่ LLM `verdict="incorrect"` When รวมผล Then `verdict=correct`, `decided_by=sympy`, `disagreement=true`
- **AC-11 (AM-04)** Given SymPy ตัดสิน `incorrect` แต่ LLM `verdict="correct"` When รวมผล Then `verdict=incorrect`, `disagreement=true`
- **AC-12 (AM-04)** Given LLM `verdict=None` (ปกติเมื่อ SymPy ตัดสินได้) When รวมผล Then `disagreement=false`
- **AC-13 (AM-04)** Given `equation` (P15 `x=-1, x=3`) และ `final_in_form=None` When รวมผล Then ไม่ถือว่าเป็น `incomplete` (รูปใช้เฉพาะ `factored`)
- **AC-6b (AM-05)** Given `final_equal=False`, `line_ok` จริงทุกบรรทัด (3 บรรทัด), LLM `first_wrong_line=2` When รวมผล Then `first_wrong_line=2` · ถ้า LLM `first_wrong_line=None` Then `first_wrong_line=3` (บรรทัดสุดท้าย)
- **AC-7b (AM-06)** Given `lines=[]` When รวมผล Then `decided_by=sympy`, `confidence=1.0`
- **AC-15 (AM-04)** Given SymPy ตัดสินได้ (AC-1, AC-5) และ LLM `confidence=0.6` When รวมผล Then `confidence=1.0`
- **AC-14 (AM-06)** Given ผลใดก็ตามที่ verdict ไม่ใช่ `correct` When รวมผล Then `error_type` เป็นหนึ่งใน 6 ค่าของ AM-06 · Given verdict เป็น `correct` Then `error_type=null`
- **AC-boundary** ไม่มี threshold ใน feature นี้ (ดู §2)
- **AC-tenant (SA-06)** ไม่เกี่ยว: เป็นฟังก์ชันล้วน ไม่อ่านหรือเขียนข้อมูล

## 5. Data changes

ไม่มีใน feature นี้ (คนเรียกเป็นคนเขียน `attempts` และ `checker_disagreements`) · ดู §11 เรื่อง column ที่ `attempts` ยังไม่มี

## 6. API / SSE changes

ไม่มี · output ตรงกับ SSE `verdict` ใน `api.md` (`{verdict, first_wrong_line, error_type}`) อยู่แล้ว

## 7. AI calls

ไม่มี · รับ output ของ `check_answer` (T4) ที่เรียกไปก่อนแล้วเป็น input

## 8. Test plan

| Test | ระดับ | ครอบคลุม AC |
|---|---|---|
| `tests/unit/test_check_merge_rules.py` แบบ table-driven (`parametrize`) | unit | AC-1 ถึง AC-14 |
| `evals/run_eval.py --purpose check_answer` กับ golden set 50 ข้อ (เมื่อมี SymPy service + prompt) | eval | ทั้ง checker (§2.4.8) |

## 9. Out of scope

- SymPy service (`app/math/`) · prompt `check_answer/v1` · hint `sign_flip_detected` (เป็น input ของ LLM)
- เขียน `attempts` / `checker_disagreements` · SSE · dispute (§2.4.7, AM-12)
- `numeric`, `short_text`, `sql` (Should / Could)
- ตรวจว่าเฉลยถูก (§2.4.6)

## 10. Open questions

ไม่มีข้อที่ค้าง

**ตัดสินแล้ว (21 ต.ค.)**

1. (Junior ตกลง) SymPy service คืน `parsed`, `timed_out`, `final_equal`, `final_in_form`, `line_ok` ตาม §3 · merge rules หาบรรทัดแรกที่ผิดเองจาก `line_ok` (SymPy ไม่ต้องคืน `first_wrong_line`)
2. ไม่จับคำพูดอย่าง "ไม่รู้" · `lines` ที่ user ยืนยันมาตัดคำพูดทิ้งแล้วตามกติกาลายมือ เช็คแค่ `lines` ว่าง
3. `decided_by` ของ no answer = `sympy` (code ตัดสิน ไม่ใช่ LLM) · ไม่ต้องแก้ data-model
4. `confidence` เมื่อ SymPy หรือ code ตัดสิน = `1.0` · confidence ของ LLM เป็นของ error_type คนละเรื่อง
5. คำตอบสุดท้ายผิดแต่ทุกบรรทัด `line_ok` จริง → ใช้ `first_wrong_line` ของ LLM ถ้าไม่มี ใช้บรรทัดสุดท้าย (AC-6b)
6. LLM ไม่ให้ error_type → ไม่เกิดใน merge rules เพราะ schema ของ `check_answer` บังคับ และ gateway retry ตาม AI-05
7. `incomplete` ที่มีบรรทัดผิดด้วย → คง `incomplete` และ first_wrong_line = `null` ตามคู่มือ label

## 11. Spec changes needed

- `data-model.md` → `attempts` ยังไม่มี `first_wrong_line` (PM-01 ต้องบันทึก) และ `method` · **Junior ตกลงเพิ่มทั้ง 2 column ใน migration ถัดไป (รวมกับ #67)** · merge rules ไม่ต้องรอ เพราะไม่ได้เขียน DB
- ไม่ต้องแก้ `config/learning.yaml`
