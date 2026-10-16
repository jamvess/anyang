# คู่มือ label: golden set คำตอบ + ลายมือ + หัวข้อ P3

| | |
|---|---|
| Owner | Jam |
| Branch | `docs/label-guide` |
| Checklist item | เขียนคู่มือ label golden set (verdict, error type, บรรทัดแรกที่ผิด) ใน `evals/README.md` |
| Status | in progress · 2026-10-16 |

## Plan

- [x] 1. 🤖 สร้าง branch, worklog และ Draft PR
- [ ] 2. 🙋 ตัดสินใจ 3 เรื่อง: ขนาดของหัวข้อ, map ข้อสอบรายข้อย่อยหรือข้อใหญ่, ดาวใน label ให้คนตัดสินเองหรือคำนวณจากสูตร
- [ ] 3. 🤖 คู่มือ label หัวข้อ P3 ใน `evals/topics/README.md` + รูปแบบ `labels.json` ให้ตรงกับ output ของ A5/A6/A7 (ai-orchestration §2.3.4) + ตัวอย่างจาก MTH10101
- [ ] 4. 🤖 คู่มือ label ลายมือ P1 ใน `evals/README.md`: กติกาการพิมพ์ LaTeX รายบรรทัด (สิ่งที่อ่านไม่ออก, ขีดฆ่า, ลูกศร)
- [ ] 5. 🤖 คู่มือ label golden set คำตอบ P2 ใน `evals/README.md`: verdict 5 ค่า, error_type 6 ค่าพร้อมนิยามและตัวอย่างแคลคูลัส, กติกา first_wrong_line, answer_format
- [ ] 6. 🙋 Jam อ่านคู่มือทั้งหมดแล้วลอง label ตัวอย่าง 2 ข้อ (ใช้ข้อสอบ MTH10101) ดูว่าตัดสินได้โดยไม่ต้องถามไหม
- [ ] 7. 🤖 ติ๊ก checklist และร่างข้อความถึง May

## Definition of done

- `evals/README.md` มีนิยาม verdict, error_type และ first_wrong_line พร้อมตัวอย่าง อ่านแล้ว label ได้โดยไม่ต้องถาม
- `evals/topics/README.md` มีรูปแบบ `labels.json` และขั้นตอน label หัวข้อ ให้ May เริ่ม label MTH10101 ได้วันจันทร์ 19 ต.ค.
- ทุกนิยามตรงกับ `specs/system/ai-orchestration.md` §2.3–2.4 (ไม่คิดค่าใหม่เอง)

## Decisions

- 2026-10-16 · รวมคู่มือ label หัวข้อ P3 ไว้ในงานนี้ด้วย แม้ checklist จะพูดถึงแค่ golden set · May ต้องใช้ label MTH10101 ก่อน 23 ต.ค. และตอนนี้รูปแบบ `labels.json` ยังไม่พอ (map ได้ข้อละ 1 หัวข้อ ไม่มี skills ราย skill, ไม่มี pages, ไม่มี prereqs)

## Next step

Jam ตัดสินใจ 3 เรื่องในขั้นที่ 2

## Waiting on

ไม่มี

## Notes for next time

- error_type 6 ค่า: ai-orchestration.md บรรทัด 81 และ §2.4.4 · verdict: §2.4.5 · A5/A6/A7 output: บรรทัด 179–181
