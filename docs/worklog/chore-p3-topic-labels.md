# Label หัวข้อ ดาว และ map ข้อสอบของ MTH10101 ให้ P3

| | |
|---|---|
| Owner | May |
| Branch | `chore/p3-topic-labels` |
| Checklist item | Label หัวข้อ ดาว และ map ข้อสอบรายข้อของวิชา pilot ร่วมกับ Jam ลง `evals/topics/` (ให้ P3) |
| Status | in progress · 2026-10-19 |

## Plan

คู่มือ: `evals/topics/README.md` หัวข้อ "คู่มือ label" · ไฟล์ที่ได้: `evals/topics/mth10101/labels.json`

**กฎสำคัญ:** ห้ามใช้ AI ช่วย label (Claude ช่วยได้แค่แปลงสิ่งที่ May เขียนเป็น JSON และตรวจ format) · ห้ามเปิดตาราง "ข้อสอบแต่ละข้ออยู่ในชีทไหน" ใน `sources.md` ก่อน label เสร็จ · ห้ามโหลดข้อสอบ 2562 (held-out)

- [ ] 1. 🙋 May โหลดไฟล์ 6 ไฟล์จาก Drive มาไว้ที่ `evals/topics/mth10101/raw/`
- [ ] 2. 🤖 สร้างไฟล์ร่าง `evals/topics/mth10101/labels-draft.md` (ตารางให้กรอก) + โครง `labels.json`
- [ ] 3. 🙋 May อ่าน `sheet-01`, `sheet-02` แล้วแบ่งหัวข้อ + หน้า (ขั้น 1 ของคู่มือ)
- [ ] 4. 🙋 May เขียน skills 2–5 ข้อต่อหัวข้อ + prereqs (ขั้น 2–3)
- [ ] 5. 🙋 May map ข้อสอบ 2559 และ 2561 ทีละข้อย่อย + trap + unmapped (ขั้น 4)
- [ ] 6. 🙋 May ให้ดาวทีละหัวข้อ (ขั้น 5)
- [ ] 7. 🤖 แปลงร่างเป็น `labels.json` (ไม่แก้เนื้อหา) + ตรวจ format: id ไม่ซ้ำ, prereqs/topic/skill ที่อ้างถึงมีจริง, ดาว 1–3, ทุกข้อย่อยอยู่ใน `question_map` หรือ `unmapped` · ลบ `labels-draft.md`
- [ ] 8. 🤖 ติ๊ก checklist · 🙋 May แจ้ง Jam และขอ Junior review

## Definition of done

- `evals/topics/mth10101/labels.json` ตรงรูปแบบในคู่มือ: ทุกหัวข้อมี `pages`, `skills`, `prereqs`, `stars_human`
- ทุกข้อย่อยของ `midterm-2559-1` และ `midterm-2561-1` อยู่ใน `question_map` หรือ `unmapped`
- `labeled_by: May`, `reviewed_by: Junior` (Junior ตรวจใน PR)
- ส่งให้ Jam **ก่อน ศ. 23 ต.ค.** (23 ต.ค. เป็นวันหยุด จึงตั้งเป้าเสร็จ พฤ. 22 ต.ค.)

## Decisions

- 2026-10-19 · ใช้ type `chore` · เป็นงาน label ข้อมูล ไม่ใช่ feature
- 2026-10-19 · May เขียนร่างเป็นตาราง Markdown แล้ว Claude แปลงเป็น JSON · คู่มืออนุญาตให้ AI แปลง JSON ได้ และพิมพ์ตารางง่ายกว่าพิมพ์ JSON (รอ May ยืนยัน)

## Next step

May ทำขั้น 1: โหลดไฟล์จาก Drive (ดูคำแนะนำในแชท)

## Waiting on

May: อนุมัติแผน

## Notes for next time

- `evals/` เป็นโฟลเดอร์ของ Jam แต่คู่มือกำหนดให้ May เป็นคนเขียน `labels.json`
- ถ้าไม่ทัน ให้ทำ `sheet-01` ก่อน (`sources.md` "สิ่งที่ P3 ต้องรู้")
- Claude ห้ามเสนอหัวข้อ, skill, ดาว หรือการ map ใดๆ แม้ May จะขอ
