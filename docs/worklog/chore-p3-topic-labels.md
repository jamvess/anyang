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

- [x] 1. 🙋 May โหลดไฟล์ 6 ไฟล์จาก Drive มาไว้ที่ `evals/topics/mth10101/raw/` (2026-10-19 · ไม่มีไฟล์ 2562)
- [x] 2. 🤖 สร้างไฟล์ร่าง `evals/topics/mth10101/labels-draft.md` (ตารางให้กรอก) · `labels.json` สร้างตอนแปลงในขั้น 7
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
- 2026-10-19 · May เขียนร่างเป็นตาราง Markdown แล้ว Claude แปลงเป็น JSON · คู่มืออนุญาตให้ AI แปลง JSON ได้ และพิมพ์ตารางง่ายกว่าพิมพ์ JSON (May ยืนยันแล้ว)
- 2026-10-19 · ในร่างข้อสอบใส่แค่ skill id ไม่ต้องใส่ topic แยก · topic ดูได้จากหน้า skill id (`t03.s2` → `t03`) May จะได้ไม่ต้องพิมพ์ซ้ำ และไม่มีโอกาสใส่ไม่ตรงกัน
- 2026-10-19 · commit `labels-draft.md` ทุกครั้งที่ May พัก · งานกินเวลาหลายวัน ถ้าเครื่องมีปัญหาจะได้ไม่หาย

- 2026-10-19 · ตอนแปลง: หน้าเดียว `sheet-01:35` → `sheet-01:35-35` · May เขียนในร่างแบบเดิมต่อได้
- 2026-10-19 · ชื่อหัวข้อไม่ใส่วงเล็บที่เป็นคำอธิบาย (ย้ายไปไว้ในหมายเหตุ) แต่เก็บวงเล็บที่เป็นชื่อภาษาอังกฤษ · คำอธิบายในวงเล็บอาจทำให้ P3 เทียบชื่อพลาด ส่วนการเก็บชื่ออังกฤษไว้ คู่มือให้ทำแบบนั้น
- 2026-10-19 · หมายเหตุใน `<!-- -->` ของร่าง (หน้าแบบฝึกหัดรวม, หน้าว่าง, t17 มีแค่แบบฝึกหัด) → ใส่ใน PR description ตอนปิดงาน

## Done 2026-10-19

- ส่วนที่ 1 ของ `sheet-01` เสร็จแล้ว: t01–t27 · ตรวจรูปแบบผ่าน (id ไม่ซ้ำ, prereqs มีจริงและไม่วน, หน้าไม่เกิน 140)
- ⚠️ May แก้ไฟล์ร่างใน `Downloads/` ไม่ใช่ใน repo · Claude copy มาทับไฟล์ใน repo ให้แล้ว ต่อไปให้แก้ที่ `evals/topics/mth10101/labels-draft.md` ใน VS Code

## Next step

May ทำขั้น 3 ต่อ: กรอกหัวข้อจาก `raw/sheet-02.pdf` (t28 เป็นต้นไป) และเพิ่มหน้าแบบฝึกหัดของ `sheet-03`, `sheet-04` เข้าไปในหัวข้อที่มีอยู่

## Waiting on

May: ตัดสินเรื่องวงเล็บของ t02, t07, t11 · กรอก sheet-02

## Notes for next time

- `evals/` เป็นโฟลเดอร์ของ Jam แต่คู่มือกำหนดให้ May เป็นคนเขียน `labels.json`
- ถ้าไม่ทัน ให้ทำ `sheet-01` ก่อน (`sources.md` "สิ่งที่ P3 ต้องรู้")
- Claude ห้ามเสนอหัวข้อ, skill, ดาว หรือการ map ใดๆ แม้ May จะขอ
