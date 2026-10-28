# SymPy service `app/math/` (P2)

| | |
|---|---|
| Owner | Jam |
| Branch | `feat/sympy-service` |
| Checklist item | SymPy service `app/math/`: parse LaTeX, เทียบทีละบรรทัด, expression / factored / equation, subprocess + timeout จาก config · ย้ายให้ Jam 21 ต.ค. (ทีมตกลง · ใกล้กับ P2) · รูปแบบผลตกลงไว้ใน `specs/features/check/merge-rules.md` §3 · Junior review เพราะอยู่ใน `apps/api/` |
| Status | in progress · 2026-10-28 |

## Plan

- [x] 1. 🤖 `/spec-feature AM-04 AM-05` → `specs/features/check/sympy-service.md` · input (โจทย์, เฉลย, `answer_format`, `lines`) → `SympyResult` ตาม merge-rules §3 · AC จากโจทย์ P01–P17 และ golden set `evals/answers/` · เขียนคำถามที่ต้องตัดสินไว้ใน §10
- [x] 2. 🙋 Jam review spec และตอบคำถามใน §10 (เปิดไฟล์ spec อ่าน §2, §4, §10 แล้วตอบในแชทนี้เป็นข้อ)
- [x] 3. 🙋 ขอ Junior ในแชทกลุ่ม 3 เรื่องตาม spec §11: (1) เพิ่ม `antlr4-python3-runtime==4.11` ใน `apps/api/pyproject.toml` (2) เพิ่ม `checker.sympy_workers` ใน `learning.yaml` + field ใน `CheckerConfig` ของ `settings.py` (3) ประโยคเรื่อง `line_ok = []` ใน merge-rules §3 · ตอบ OK แล้วบอกในแชทนี้
- [x] 4. 🤖 `/spec-to-tests` → `apps/api/tests/unit/test_sympy_service.py` แบบ table-driven (ต้องแดงก่อน implement)
- [x] 5. 🙋 Jam review test: ชื่อ test ขึ้นต้นด้วย requirement ID และครบทุก AC ใน spec §4
- [x] 6. 🤖 `/implement-feature` → `apps/api/app/math/sympy_service.py` (parse, เทียบรายบรรทัด, `factor_list`, `solveset`, subprocess + timeout จาก `checker.sympy_timeout_seconds`) จน test เขียว + ruff ผ่าน
- [x] 7. 🤖 รัน service กับคำตอบ 50 ข้อใน `evals/answers/labels.jsonl` นับว่า parse ได้กี่ข้อ, timeout กี่ข้อ และ `final_equal` ตรงกับ verdict ของ label กี่ข้อ · จดตัวเลขไว้ใน worklog ให้ P2 (ยังไม่ต่อ prompt `check_answer`)

## Definition of done

- `app/math/` คืน `SympyResult` (`parsed`, `timed_out`, `final_equal`, `final_in_form`, `line_ok`) ตรงกับ `merge-rules.md` §3 และส่งเข้า `merge_check` ได้เลย
- รองรับ `expression`, `factored` (เทียบ `factor_list`), `equation` (เทียบ solution set) · `line_ok` เทียบบรรทัด i กับ i − 1
- SymPy รันใน subprocess พร้อม timeout จาก `config/learning.yaml` `checker.sympy_timeout_seconds` (ไม่ hard-code) · ค้างแล้วไม่ทำให้ request ค้าง
- test ใน `tests/unit/` ขึ้นต้นด้วย requirement ID ผ่าน · `uv run ruff check .` และ `uv run pytest` ผ่าน
- มีตัวเลข parse/timeout จาก golden set 50 ข้อใน PR
- PR review โดย Junior (CODEOWNERS ของ `apps/api/`)

## Decisions

- 2026-10-28 · ใช้ parser แบบ `antlr` ไม่ใช่ `lark` · ผลจาก P1 (`poc/P1/lines.py`): `lark` อ่านบางบรรทัดผิดโดยไม่แจ้ง
- 2026-10-28 · Jam ตัดสิน §10 ของ spec ตามที่เสนอทั้ง 5 ข้อ: f(x) บรรทัดแรกถูกเสมอ · implicit dy/dx ให้ LLM · `a=b=c` แยกขั้นย่อย · `checker.sympy_workers: 1 [C]` · `line_ok = []` ตอนตัดสินไม่ได้ · spec approved · ai-orchestration v1.3 §2.4.3
- 2026-10-28 · Junior OK 3 เรื่องใน spec §11 · เพิ่ม `antlr4-python3-runtime==4.11`, `checker.sympy_workers` (`learning.yaml` 1.3 + `CheckerConfig`), merge-rules §3 `line_ok = []`
- 2026-10-28 · test กำหนดชื่อภายในเพิ่มจาก spec §3: `evaluate_lines(answer_format, reference, lines)` (ฟังก์ชันที่ worker รัน · test กฎเทียบได้โดยไม่เปิด process), `SympyWorkerPool(workers=n)` + `await pool.run(fn, *args, timeout_s=)` + `close()`, `SympyTimeoutError`, `default_pool()` (ใช้ร่วมกัน), `check_lines(..., pool=None)` · ใน repo ยังไม่มี fixture `LearningConfig` จึงอ่านค่าจาก `get_settings().learning.checker`
- 2026-10-28 · implement: red → green 2 รอบ (1: ยังไม่มีโมดูล → 34/36 · 2: antlr อ่าน `x(x^{2}-1)` เป็นฟังก์ชัน → ใส่ `\cdot` ระหว่างตัวอักษรเดียวกับ `(` → ผ่านหมด) · เพิ่มเป็น spec §2.1 ข้อ 5 · `factored` "อยู่ในรูป" = ทุกตัวประกอบที่มีตัวแปรมี `factor_list` = (±1, [ตัวเดียว ยกกำลัง 1]) ทำให้ `3x+6` ไม่อยู่ในรูปตาม AC-12 · ตัวแปร = free symbol เดียวของเฉลยและทุกบรรทัดรวมกัน (spec §2.2 ตามตัวอักษรจะทำให้ AC-27 ที่ไม่มี symbol เลย parse ไม่ได้ จึงต้องใช้ตัวแปรเฉพาะตอนจำเป็น: อนุพันธ์และ solveset)
- 2026-10-28 · บรรทัด 1 เทียบกับเฉลยแทนตัวโจทย์ เพราะ `problems.text` เป็นภาษาไทยปน parse ไม่ได้ และ AM-11 รับประกันว่าค่าโจทย์ = เฉลย
- 2026-10-28 · ใช้ worker ที่เปิดค้างไว้ ไม่เปิด process ใหม่ทุกครั้ง · วัดแล้วเปิด Python + import SymPy ใช้ 1.9 วินาที (budget 2 วินาที)
- 2026-10-28 · แทน symbol `e` ด้วย `E` · ทดลองแล้ว parser อ่าน `e^{x}` เป็นตัวแปร ทำให้ P16 แก้ไม่ได้

## Next step

ครบทุกขั้น · รอ Jam ตัดสินว่าจะเพิ่ม "ตัวอย่างค้านเชิงตัวเลข" ใน `_equal` ไหม (ดูหัวข้อผลกับ golden set) · ถ้าไม่เพิ่ม → `/work-done`

## ผลกับ golden set 50 ข้อ (28 ต.ค. · `check_lines` จริงผ่าน `default_pool()` timeout 2 วินาที)

| | ผล |
|---|---|
| SymPy ตัดสินได้ | 44/50 · parse ไม่ได้ 4 (ans_004, 041, 046 implicit dy/dx · ans_047 จบที่บรรทัด `f'(x)`) · ตัดสินไม่ได้ 2 (ans_034 `solveset` คืน ConditionSet · ans_042 `equals` ตอบ None) · timeout 0 |
| `final_equal` ตรงกับ label | 44/44 |
| verdict หลัง merge (ให้ LLM ปลอมใช้ error_type ของ label) | 44/44 |
| first_wrong_line | 19/21 · พลาด ans_037, ans_038 (wrong_method: ตั้ง f′ หรือ f″ = 0 ผิดตัว ทุกบรรทัดเท่ากันทางคณิต) → merge rules ใช้บรรทัดที่ LLM ชี้ (ตอนวัดให้ LLM ไม่ชี้ จึงได้บรรทัดสุดท้าย) |
| เวลาต่อข้อ | median 0.14 วินาที · max 0.47 วินาที |

อีก 6 ข้อที่ SymPy ไม่ตัดสินไปที่ LLM (merge-rules ข้อ 2) · ถ้า LLM ถูกทั้ง 6 ข้อ verdict ได้ 50/50 แต่ถ้าผิดเกิน 3 ข้อจะต่ำกว่าเป้า P2 ที่ 47/50

## Waiting on

ไม่มี

## Notes for next time

- `poc/P1/lines.py` มีโค้ดที่ใช้ซ้ำได้ (normalize, split comma ระดับบนสุด, เทียบ Eq) แต่ P1 **ไม่คำนวณ** derivative/limit (เทียบตามที่เขียน) · P2 ต้องคำนวณ เพราะบรรทัด 1 มักเป็นโจทย์ และบรรทัดถัดไปเป็นผลที่คำนวณแล้ว
- golden set 50 ข้อ: factored 9 · expression 30 (limit, derivative, implicit dy/dx, f″) · equation 11 (P15 จุดวิกฤต, P16, P17) · โจทย์มี `\text{…}` ภาษาไทยปน
