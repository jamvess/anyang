# `check_answer/v2`: ย้าย `reference_answer` เข้า data block

| | |
|---|---|
| Owner | Jam |
| Branch | `feat/check-answer-v2` |
| Checklist item | ไม่มีข้อตรง · ต้องทำก่อนต่อ P2 เข้าห้อง (PR #110, #111) |
| Status | in progress · 2026-11-07 |

## Plan

- [ ] 1. 🤖 test ให้แดงก่อน · สร้าง `prompts/check_answer/v2.md` ที่ต่างจาก v1 แค่ `reference_answer` อยู่ใน `<document>` · เปลี่ยน `config/ai.yaml` เป็น v2 · แก้ `check-answer-classifier.md` §2.2
- [ ] 2. 🙋 Jam อ่าน diff ของ v1 กับ v2 · บอกแชทกลุ่มว่าจะแก้ `config/ai.yaml`
- [ ] 3. 🙋 Jam รัน eval กับ model จริงจากเครื่องตัวเอง (คำสั่งอยู่ในรายงานขั้น 1)
- [ ] 4. 🤖 บันทึกผลเทียบกับ v1 · ถ้าไม่ถึงเกณฑ์ไม่ merge

## Definition of done

- `check_answer/v2` ไม่มีข้อความจากชีทหรือจากผู้ใช้นอก data block · `OUTSIDE_BY_PROMPT` ของ v2 ไม่มี `reference_answer`
- eval ของ v2 ผ่านเกณฑ์ P2 ทั้งสามข้อ: verdict ≥ 95% (47/50), error_type ≥ 80%, first_wrong_line ≥ 85% · แนบผลเทียบกับ v1 (100%, 96.4%, 100%)
- ไม่แก้ `prompts/check_answer/v1.md` · test + ruff + CI เขียว

## Decisions

- 2026-11-07 · v2 แก้แค่ที่เดียว เพื่อให้ผล eval เทียบกับ v1 ได้ตรงๆ และถ้าผลเปลี่ยนจะรู้สาเหตุ

## Next step

ขั้น 1: เขียน test และ v2

## Waiting on

ไม่มี

## Notes for next time

- คำสั่ง eval: `AI_PROVIDER=live uv run --project apps/api python evals/run_checker.py --pause 1` แล้ว `uv run --project apps/api python evals/run_eval.py --purpose check_answer --prompt v2 --predictions evals/answers/predictions/v2.jsonl`
- golden set ไม่มีเคส injection · eval ที่จะรันวัดว่า v2 ไม่ทำผลเดิมตก ไม่ได้วัดว่ากันการโจมตีได้
- `file_name` ยังเหลือเป็น `RISK:` ใน prompt อื่น · ไม่ได้อยู่ในงานนี้
