# คำถาม 20 ข้อสำหรับวัด embedding (P3b)

| | |
|---|---|
| Owner | May |
| Branch | `docs/p3b-questions` (แตกจาก `poc/P3b-embedding` ของ Jam · PR เข้า `poc/P3b-embedding`) |
| Checklist item | เขียนคำถาม 20 ข้อ + หน้าที่มีคำตอบ สำหรับวัด embedding (P3b) ลง `evals/topics/mth10101/retrieval_questions.md` (เทมเพลตและกติกาอยู่ใน branch `poc/P3b-embedding`) · คนเขียนต้องไม่ใช่ Jam · ส่งให้ Jam ภายใน จ. 26 ต.ค. |
| Status | ready for work-done · 2026-10-21 |

## Plan

- [x] 1. 🤖 แตก branch จาก `poc/P3b-embedding` + worklog + draft PR เข้า branch ของ Jam
- [x] 2. 🙋 May เขียนคำถาม 20 ข้อ + หน้าที่มีคำตอบ ใน `evals/topics/mth10101/retrieval_questions.md` **เอง ห้ามใช้ AI ช่วย** (กติกาข้อ 6 ของเทมเพลต)
- [x] 3. 🤖 เช็กรูปแบบและการกระจายตามกติกาเท่านั้น (ครบ 20 แถว, รูปแบบหน้า `sheet-0N:หน้า`, หน้าอยู่ในช่วงของไฟล์, ≥ 12 หัวข้อ, ≤ 2 ข้อต่อหัวข้อ, sheet-02 ≥ 3 ข้อ, สัดส่วนแบบคำถาม) · ไม่แนะนำเนื้อหาคำถามหรือหน้า
- [x] 4. 🙋 May แก้ตามที่เช็กเจอ (ถ้ามี) แล้วกรอกชื่อผู้เขียน + วันที่

## Definition of done

- ตาราง 20 แถวครบ ผ่านกติกาข้อ 1–5 ของเทมเพลต · May เขียนเองทั้งหมด
- PR เข้า `poc/P3b-embedding` ให้ Jam ภายใน จ. 26 ต.ค.

## Decisions

- 2026-10-21 · ทำบน branch ที่แตกจาก `poc/P3b-embedding` เพราะเทมเพลตอยู่ที่นั่น (ยังไม่อยู่ใน main) · PR เข้า branch ของ Jam
- 2026-10-21 · Claude ไม่อ่านชีทหรือเสนอคำถาม/หน้า · ช่วยแค่เช็กรูปแบบ

- 2026-10-21 · May เขียนเองครบ 20 ข้อ (ไฟล์จาก Downloads คัดลอกเข้า repo ตามตัวอักษร) · เช็กรูปแบบผ่านทุกข้อ: 20 แถว, 19 หัวข้อ, ≤ 2 ข้อต่อหัวข้อ, sheet-02 5 ข้อ, แบบ 5/8/4/3
- 2026-10-21 · ข้อสังเกต (ไม่ผิดกติกา · May คงไว้): #15 `sheet-01:103` นอกช่วงประมาณของ t19 · #19 `sheet-02:32` นอกช่วงประมาณของ t26
- 2026-10-21 · กติกาข้อ 6 ของเทมเพลตถูกลบไปโดยไม่ตั้งใจตอนกรอก · ใส่คืนแล้ว (May ยืนยันว่าเขียนเอง)

## Next step

รัน /work-done (PR #46 เข้า `poc/P3b-embedding` · reviewer Jam)

## Waiting on

ไม่มี

## Notes for next time

- ชีทอยู่ใน Drive (ลิงก์ใน `evals/topics/mth10101/sources.md`) · เลขหน้าใช้ตาม PDF viewer · sheet-01 มี 140 หน้า, sheet-02 33 หน้า, sheet-03/04 3 หน้า
