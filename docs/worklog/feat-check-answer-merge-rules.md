# P2 · merge rules ของ checker (ai-orchestration §2.4.5)

| | |
|---|---|
| Owner | Jam |
| Branch | `feat/check-answer-merge-rules` |
| Checklist item | P2: merge rules + LLM classifier (`prompts/check_answer/v1`) ใช้ SymPy service ของ Junior |
| Status | in progress · 2026-10-21 |

## Plan

- [x] 1. 🤖 `/spec-feature check/merge-rules AM-04 AM-05 AM-06` → `specs/features/check/merge-rules.md` · input = ผลของ SymPy (ตาม answer_format) + ผลของ LLM classifier · output = verdict ตาม §2.4.5 · ตัวตัดสินอยู่ใน `apps/api/app/domain/` (code ล้วน ไม่เรียก AI)
- [x] 2. 🙋 Jam review spec + ตอบ open questions · 🙋 ขอ Junior ตกลงรูปแบบผลของ SymPy service (`app/math/`) ที่ merge rules จะรับ
- [x] 3. 🤖 `/spec-to-tests` → test ใน `apps/api/tests/unit/` (red) · ใช้ผลของ SymPy ปลอม
- [x] 4. 🙋 Jam review test (+ Junior เพราะอยู่ใน `apps/api/`)
- [x] 5. 🤖 `/implement-feature` จนเขียว

## Definition of done

- feature spec ผ่าน review · ทุก AC มี test ที่ชื่อขึ้นต้นด้วย requirement ID (test strategy §5)
- merge rules เป็น code ล้วนใน `app/domain/` ไม่มี AI call · test ผ่าน · ruff ผ่าน
- ข้อ checklist นี้เสร็จแค่ครึ่ง (merge rules) · LLM classifier `check_answer/v1` แยกเป็นงานต่อไป → ไม่ติ๊ก เพิ่ม sub-bullet

## Decisions

- 2026-10-21 · ทำล่วงหน้าของ S3 · เริ่มได้โดยไม่ต้องรอ SymPy service เพราะ test ใส่ผลของ SymPy ปลอม แต่ต้องตกลงรูปแบบผลกับ Junior ก่อนเขียน test

- 2026-10-21 · (Jam ok ตามคำแนะนำ) open questions 2–7 ของ spec: ไม่จับคำพูด "ไม่รู้" · no answer `decided_by=sympy` · confidence = 1.0 เมื่อ SymPy/code ตัดสิน · ผิดแต่ทุกบรรทัดถูก → first_wrong_line ของ LLM ไม่งั้นบรรทัดสุดท้าย · error_type ของ LLM บังคับด้วย schema + AI-05 · incomplete คงไว้ · เพิ่ม AC-6b, AC-7b, AC-15

- 2026-10-21 · Junior ตกลงตามที่แนะนำ: รูปแบบผลของ SymPy ตาม §3 · merge rules หาบรรทัดแรกที่ผิดเองจาก `line_ok` · `attempts.first_wrong_line` + `method` เพิ่มใน migration ถัดไป (รวม #67) · spec status = approved

- 2026-10-21 · ข้อ 3: `apps/api/tests/unit/test_check_merge_rules.py` 16 test (25 case) ครบ AC-1 ถึง AC-15 · red: `ModuleNotFoundError: app.domain.checker` · API ที่ test กำหนด: `merge_check(answer_format, lines, sympy, llm) -> CheckResult` · `SympyResult`, `LlmResult`, `CheckResult` (field ตาม spec §3)

- 2026-10-21 · ข้อ 5: `app/domain/checker.py` (`merge_check` + 3 dataclass) · 25/25 ผ่าน · red → green 1 รอบ · api ทั้งหมด 218 ผ่าน · **ตัดสินเองนอก spec 3 จุด (Jam ok · เขียนลง spec §2 แล้ว):** (1) SymPy ตัดสินไม่ได้และ LLM ไม่ให้ verdict → `incorrect` (2) `final_answer_correct` = true สำหรับ correct / correct_with_flaw / incomplete, false สำหรับ incorrect (3) `final_equal=None` ถือว่า SymPy ตัดสินไม่ได้

## Next step

ครบทุกขั้นแล้ว · `/work-done` (reviewer Junior · ข้อ checklist P2 ไม่ติ๊ก เพิ่ม sub-bullet ว่า merge rules เสร็จ เหลือ `check_answer/v1`)

## Waiting on

ไม่มี

## Notes for next time

- golden set พร้อมแล้ว: `evals/answers/labels.jsonl` 50 ข้อ (AI ร่าง ต้องตรวจซ้ำ 28 ข้อก่อน report P2 · `evals/README.md` "กฎ")
- `evals/run_eval.py --purpose check_answer` ให้คะแนนจากไฟล์ prediction ได้แล้ว
