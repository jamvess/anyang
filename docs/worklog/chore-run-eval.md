# Script `evals/run_eval.py` สำหรับ checker (P2)

| | |
|---|---|
| Owner | Jam |
| Branch | `chore/run-eval` |
| Checklist item | Script `evals/run_eval.py` ออกคะแนน verdict, error type, บรรทัดผิด |
| Status | in progress · 2026-10-21 |

## Plan

- [x] 1. 🙋 Jam ตัดสินนิยาม metric 3 ตัว (ตัวหาร, การนับ `null`) และรูปแบบไฟล์ prediction · Claude เขียนลง `evals/README.md` ให้
- [ ] 2. 🤖 เขียน test `evals/test_run_eval.py` จากนิยามในข้อ 1 (red) · fixture labels/predictions เล็กๆ ไม่ใช้ AI จริง
- [ ] 3. 🙋 Jam review test
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

## Next step

ข้อ 2: เขียน `evals/test_run_eval.py` จากตาราง "การให้คะแนน" ใน `evals/README.md` (red)

## Waiting on

ไม่มี

## Notes for next time

- `evals/answers/labels.jsonl` ยังไม่มี (label 50 ข้อเป็นงาน S3) · test ใช้ fixture
