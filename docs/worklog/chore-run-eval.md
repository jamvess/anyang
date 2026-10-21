# Script `evals/run_eval.py` สำหรับ checker (P2)

| | |
|---|---|
| Owner | Jam |
| Branch | `chore/run-eval` |
| Checklist item | Script `evals/run_eval.py` ออกคะแนน verdict, error type, บรรทัดผิด |
| Status | in progress · 2026-10-21 |

## Plan

- [x] 1. 🙋 Jam ตัดสินนิยาม metric 3 ตัว (ตัวหาร, การนับ `null`) และรูปแบบไฟล์ prediction · Claude เขียนลง `evals/README.md` ให้
- [x] 2. 🤖 เขียน test `evals/test_run_eval.py` จากนิยามในข้อ 1 (red) · fixture labels/predictions เล็กๆ ไม่ใช้ AI จริง
- [x] 3. 🙋 Jam review test
- [ ] 4. 🤖 เขียน `evals/run_eval.py` จน test ผ่าน: อ่าน `answers/labels.jsonl` + predictions → คะแนน 3 ตัวเทียบเป้า → `evals/answers/results/<prompt>.json` · exit code 1 เมื่อไม่ผ่านเป้า (ใช้ใน CI ภายหลัง)
- [ ] 5. 🤖 อัปเดตตัวอย่างคำสั่งใน `evals/README.md` + ruff

## Definition of done

- `uv run --project apps/api python evals/run_eval.py --purpose check_answer --prompt v1 --predictions <file>` ออก verdict accuracy, error_type accuracy, first_wrong_line accuracy เทียบเป้า P2 (≥ 95%, ≥ 80%, ≥ 85% · `specs/poc/README.md`)
- นิยาม metric เขียนไว้ใน `evals/README.md`
- test ผ่าน, ruff ผ่าน

## Decisions

- 2026-10-21 · script ให้คะแนนจากไฟล์ prediction ก่อน · ยังไม่เรียก checker เอง เพราะ SymPy service (`apps/api/app/math/`) ยังไม่มี · ต่อ checker จริงตอนทำ P2
- 2026-10-21 · ไม่แตะ CI (`.github/` เป็นของ Junior) · การรัน eval ใน CI เมื่อ prompt เปลี่ยน (§2.11) แยกไปเป็นงานของ Junior

- 2026-10-21 · นิยาม metric แบบ (a) ทุกข้อ (Jam): verdict ตรง 4 ค่าหารทุกข้อ (+ แสดง 2 ค่าประกอบ) · error_type หารข้อที่ label ไม่ใช่ `correct` · first_wrong_line หารข้อที่ label ไม่ใช่ `null` · prediction เป็น JSONL ตาม §2.4.5 · เขียนไว้ใน `evals/README.md` "การให้คะแนน" · ไม่นับ `null` ตรง `null` เพราะคะแนนจะสูงเกินจริง

- 2026-10-21 · ชื่อ test ใช้ requirement ของสิ่งที่วัด: verdict = AM-04, first_wrong_line = AM-05, error_type = AM-06 · ส่วน command line ใช้ `ai_orchestration_2_11` · API ที่ test กำหนด: `score(labels, predictions) -> dict` และ `main(argv) -> int` (`--purpose --prompt --labels --predictions --out`)

## Next step

ข้อ 3: Jam review `evals/test_run_eval.py` (20 test) · ถ้า ok ไปข้อ 4 เขียน `evals/run_eval.py` จนเขียว

## Waiting on

Jam review test

## Notes for next time

- `evals/answers/labels.jsonl` ยังไม่มี (label 50 ข้อเป็นงาน S3) · test ใช้ fixture
- รัน test: `uv run --project apps/api pytest evals/test_run_eval.py` · ruff ต้องใส่ `--config apps/api/pyproject.toml` (line-length 100) ไม่งั้นใช้ค่า default 88
