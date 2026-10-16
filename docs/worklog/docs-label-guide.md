# คู่มือ label: golden set คำตอบ + ลายมือ + หัวข้อ P3

| | |
|---|---|
| Owner | Jam |
| Branch | `docs/label-guide` |
| Checklist item | เขียนคู่มือ label golden set (verdict, error type, บรรทัดแรกที่ผิด) ใน `evals/README.md` |
| Status | in progress · 2026-10-16 |

## Plan

- [x] 1. 🤖 สร้าง branch, worklog และ Draft PR
- [x] 2. 🙋 ตัดสินใจ 3 เรื่อง: ขนาดของหัวข้อ, map ข้อสอบรายข้อย่อยหรือข้อใหญ่, ดาวใน label ให้คนตัดสินเองหรือคำนวณจากสูตร
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
- 2026-10-16 · **หัวข้อขนาดกลาง** (~15–20 หัวข้อสำหรับ MTH10101 เช่น "related rates", "L'Hôpital") ส่วนที่ละเอียดกว่านั้นเป็น skill · ถ้าหยาบเกิน ทุกหัวข้อได้ ★★★ · ถ้าละเอียดเกิน ส่วนใหญ่ได้ ★ · ขนาดนี้พอดีกับการติว 1 หัวข้อต่อ 1 session
- 2026-10-16 · **map ข้อสอบรายข้อย่อย** (`midterm-2559-1:ค2.3`) ข้อละ 1 หัวข้อ + 1 skill · ตรงกับ output ของ A7 `{q_id, topic_id, skill_id}` · รวมเป็นข้อใหญ่ทีหลังได้ แต่แยกกลับไม่ได้ · แทนกติกา "นับข้อย่อยรวมกับข้อหลัก" ใน `sources.md` (PR #7)
- 2026-10-16 · **คนตัดสินดาวเอง** ("ถ้าเป็นรุ่นพี่จะบอกน้องว่าสำคัญแค่ไหน") แล้ว script คำนวณดาวจากสูตรมาเทียบ · ใช้ทดสอบ `three_star_min_r` ตามที่ P3 ต้องได้ "ค่า stars.* ที่ยืนยันแล้ว"
- 2026-10-16 · branch นี้ merge `chore/p3-pilot-subject` (PR #7) เข้ามา เพราะต้องแก้ `evals/topics/README.md` และ `sources.md` ที่ยังไม่ขึ้น main · ต้อง merge PR #7 ก่อน PR นี้

## Next step

ขั้นที่ 3: เขียนคู่มือ label หัวข้อใน `evals/topics/README.md` ตาม Decisions

## Waiting on

ไม่มี

## Notes for next time

- error_type 6 ค่า: ai-orchestration.md บรรทัด 81 และ §2.4.4 · verdict: §2.4.5 · A5/A6/A7 output: บรรทัด 179–181
