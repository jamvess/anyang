# P2 · merge rules ของ checker (ai-orchestration §2.4.5)

| | |
|---|---|
| Owner | Jam |
| Branch | `feat/check-answer-merge-rules` |
| Checklist item | P2: merge rules + LLM classifier (`prompts/check_answer/v1`) ใช้ SymPy service ของ Junior |
| Status | in progress · 2026-10-21 |

## Plan

- [x] 1. 🤖 `/spec-feature check/merge-rules AM-04 AM-05 AM-06` → `specs/features/check/merge-rules.md` · input = ผลของ SymPy (ตาม answer_format) + ผลของ LLM classifier · output = verdict ตาม §2.4.5 · ตัวตัดสินอยู่ใน `apps/api/app/domain/` (code ล้วน ไม่เรียก AI)
- [ ] 2. 🙋 Jam review spec + ตอบ open questions · 🙋 ขอ Junior ตกลงรูปแบบผลของ SymPy service (`app/math/`) ที่ merge rules จะรับ
- [ ] 3. 🤖 `/spec-to-tests` → test ใน `apps/api/tests/unit/` (red) · ใช้ผลของ SymPy ปลอม
- [ ] 4. 🙋 Jam review test (+ Junior เพราะอยู่ใน `apps/api/`)
- [ ] 5. 🤖 `/implement-feature` จนเขียว

## Definition of done

- feature spec ผ่าน review · ทุก AC มี test ที่ชื่อขึ้นต้นด้วย requirement ID (test strategy §5)
- merge rules เป็น code ล้วนใน `app/domain/` ไม่มี AI call · test ผ่าน · ruff ผ่าน
- ข้อ checklist นี้เสร็จแค่ครึ่ง (merge rules) · LLM classifier `check_answer/v1` แยกเป็นงานต่อไป → ไม่ติ๊ก เพิ่ม sub-bullet

## Decisions

- 2026-10-21 · ทำล่วงหน้าของ S3 · เริ่มได้โดยไม่ต้องรอ SymPy service เพราะ test ใส่ผลของ SymPy ปลอม แต่ต้องตกลงรูปแบบผลกับ Junior ก่อนเขียน test

- 2026-10-21 · (Jam ok ตามคำแนะนำ) open questions 2–7 ของ spec: ไม่จับคำพูด "ไม่รู้" · no answer `decided_by=sympy` · confidence = 1.0 เมื่อ SymPy/code ตัดสิน · ผิดแต่ทุกบรรทัดถูก → first_wrong_line ของ LLM ไม่งั้นบรรทัดสุดท้าย · error_type ของ LLM บังคับด้วย schema + AI-05 · incomplete คงไว้ · เพิ่ม AC-6b, AC-7b, AC-15

## Next step

รอ Junior ตอบ open question 1 ของ spec (รูปแบบผลของ SymPy service) · ถ้า Junior ตกลงรูปแบบที่เสนอ: ปิดข้อ 1 ใน §10 แล้วไปข้อ 3 `/spec-to-tests specs/features/check/merge-rules.md` · ถ้าเปลี่ยน: แก้ §3 + AC ที่ใช้ `line_ok` ก่อน

## Waiting on

Junior: รูปแบบผลของ SymPy service + column `first_wrong_line`, `method` ใน `attempts`

## Notes for next time

- golden set พร้อมแล้ว: `evals/answers/labels.jsonl` 50 ข้อ (AI ร่าง ต้องตรวจซ้ำ 28 ข้อก่อน report P2 · `evals/README.md` "กฎ")
- `evals/run_eval.py --purpose check_answer` ให้คะแนนจากไฟล์ prediction ได้แล้ว
