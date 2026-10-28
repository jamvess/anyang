# SymPy service `app/math/` (P2)

| | |
|---|---|
| Owner | Jam |
| Branch | `feat/sympy-service` |
| Checklist item | SymPy service `app/math/`: parse LaTeX, เทียบทีละบรรทัด, expression / factored / equation, subprocess + timeout จาก config · ย้ายให้ Jam 21 ต.ค. (ทีมตกลง · ใกล้กับ P2) · รูปแบบผลตกลงไว้ใน `specs/features/check/merge-rules.md` §3 · Junior review เพราะอยู่ใน `apps/api/` |
| Status | in progress · 2026-10-28 |

## Plan

- [x] 1. 🤖 `/spec-feature AM-04 AM-05` → `specs/features/check/sympy-service.md` · input (โจทย์, เฉลย, `answer_format`, `lines`) → `SympyResult` ตาม merge-rules §3 · AC จากโจทย์ P01–P17 และ golden set `evals/answers/` · เขียนคำถามที่ต้องตัดสินไว้ใน §10
- [ ] 2. 🙋 Jam review spec และตอบคำถามใน §10 (เปิดไฟล์ spec อ่าน §2, §4, §10 แล้วตอบในแชทนี้เป็นข้อ)
- [ ] 3. 🙋 ขอ Junior ในแชทกลุ่ม: เพิ่ม dependency `antlr4-python3-runtime==4.11` ใน `apps/api/pyproject.toml` (ไฟล์ของ Junior) · P1 พบว่า parser แบบ `lark` ของ SymPy อ่าน `2x\sin(x)+x^{2}\cos(x)` ผิดโดยไม่แจ้ง · ตอบ OK แล้วบอกในแชทนี้
- [ ] 4. 🤖 `/spec-to-tests` → `apps/api/tests/unit/test_sympy_service.py` แบบ table-driven (ต้องแดงก่อน implement)
- [ ] 5. 🙋 Jam review test: ชื่อ test ขึ้นต้นด้วย requirement ID และครบทุก AC ใน spec §4
- [ ] 6. 🤖 `/implement-feature` → `apps/api/app/math/sympy_service.py` (parse, เทียบรายบรรทัด, `factor_list`, `solveset`, subprocess + timeout จาก `checker.sympy_timeout_seconds`) จน test เขียว + ruff ผ่าน
- [ ] 7. 🤖 รัน service กับคำตอบ 50 ข้อใน `evals/answers/labels.jsonl` นับว่า parse ได้กี่ข้อ, timeout กี่ข้อ และ `final_equal` ตรงกับ verdict ของ label กี่ข้อ · จดตัวเลขไว้ใน worklog ให้ P2 (ยังไม่ต่อ prompt `check_answer`)

## Definition of done

- `app/math/` คืน `SympyResult` (`parsed`, `timed_out`, `final_equal`, `final_in_form`, `line_ok`) ตรงกับ `merge-rules.md` §3 และส่งเข้า `merge_check` ได้เลย
- รองรับ `expression`, `factored` (เทียบ `factor_list`), `equation` (เทียบ solution set) · `line_ok` เทียบบรรทัด i กับ i − 1
- SymPy รันใน subprocess พร้อม timeout จาก `config/learning.yaml` `checker.sympy_timeout_seconds` (ไม่ hard-code) · ค้างแล้วไม่ทำให้ request ค้าง
- test ใน `tests/unit/` ขึ้นต้นด้วย requirement ID ผ่าน · `uv run ruff check .` และ `uv run pytest` ผ่าน
- มีตัวเลข parse/timeout จาก golden set 50 ข้อใน PR
- PR review โดย Junior (CODEOWNERS ของ `apps/api/`)

## Decisions

- 2026-10-28 · ใช้ parser แบบ `antlr` ไม่ใช่ `lark` · ผลจาก P1 (`poc/P1/lines.py`): `lark` อ่านบางบรรทัดผิดโดยไม่แจ้ง
- 2026-10-28 · (ร่าง spec · รอ Jam) บรรทัด 1 เทียบกับเฉลยแทนตัวโจทย์ เพราะ `problems.text` เป็นภาษาไทยปน parse ไม่ได้ และ AM-11 รับประกันว่าค่าโจทย์ = เฉลย
- 2026-10-28 · ใช้ worker ที่เปิดค้างไว้ ไม่เปิด process ใหม่ทุกครั้ง · วัดแล้วเปิด Python + import SymPy ใช้ 1.9 วินาที (budget 2 วินาที)
- 2026-10-28 · แทน symbol `e` ด้วย `E` · ทดลองแล้ว parser อ่าน `e^{x}` เป็นตัวแปร ทำให้ P16 แก้ไม่ได้

## Next step

ขั้น 2: Jam อ่าน `specs/features/check/sympy-service.md` §2, §4, §10 แล้วตอบ Q1–Q5 · จากนั้นแก้ spec ตามคำตอบ, เปลี่ยน Status เป็น approved และแก้ merge-rules §3 / ai-orchestration §2.4.3 ตาม §11

## Waiting on

ไม่มี

## Notes for next time

- `poc/P1/lines.py` มีโค้ดที่ใช้ซ้ำได้ (normalize, split comma ระดับบนสุด, เทียบ Eq) แต่ P1 **ไม่คำนวณ** derivative/limit (เทียบตามที่เขียน) · P2 ต้องคำนวณ เพราะบรรทัด 1 มักเป็นโจทย์ และบรรทัดถัดไปเป็นผลที่คำนวณแล้ว
- golden set 50 ข้อ: factored 9 · expression 30 (limit, derivative, implicit dy/dx, f″) · equation 11 (P15 จุดวิกฤต, P16, P17) · โจทย์มี `\text{…}` ภาษาไทยปน
