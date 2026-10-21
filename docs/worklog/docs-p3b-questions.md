# คำถาม 20 ข้อสำหรับวัด embedding (P3b)

| | |
|---|---|
| Owner | May |
| Branch | `docs/p3b-questions` (แตกจาก `poc/P3b-embedding` ของ Jam · PR เข้า `poc/P3b-embedding`) |
| Checklist item | เขียนคำถาม 20 ข้อ + หน้าที่มีคำตอบ สำหรับวัด embedding (P3b) ลง `evals/topics/mth10101/retrieval_questions.md` (เทมเพลตและกติกาอยู่ใน branch `poc/P3b-embedding`) · คนเขียนต้องไม่ใช่ Jam · ส่งให้ Jam ภายใน จ. 26 ต.ค. |
| Status | in progress · 2026-10-21 |

## Plan

- [x] 1. 🤖 แตก branch จาก `poc/P3b-embedding` + worklog + draft PR เข้า branch ของ Jam
- [ ] 2. 🙋 May เขียนคำถาม 20 ข้อ + หน้าที่มีคำตอบ ใน `evals/topics/mth10101/retrieval_questions.md` **เอง ห้ามใช้ AI ช่วย** (กติกาข้อ 6 ของเทมเพลต)
- [ ] 3. 🤖 เช็กรูปแบบและการกระจายตามกติกาเท่านั้น (ครบ 20 แถว, รูปแบบหน้า `sheet-0N:หน้า`, หน้าอยู่ในช่วงของไฟล์, ≥ 12 หัวข้อ, ≤ 2 ข้อต่อหัวข้อ, sheet-02 ≥ 3 ข้อ, สัดส่วนแบบคำถาม) · ไม่แนะนำเนื้อหาคำถามหรือหน้า
- [ ] 4. 🙋 May แก้ตามที่เช็กเจอ (ถ้ามี) แล้วกรอกชื่อผู้เขียน + วันที่

## Definition of done

- ตาราง 20 แถวครบ ผ่านกติกาข้อ 1–5 ของเทมเพลต · May เขียนเองทั้งหมด
- PR เข้า `poc/P3b-embedding` ให้ Jam ภายใน จ. 26 ต.ค.

## Decisions

- 2026-10-21 · ทำบน branch ที่แตกจาก `poc/P3b-embedding` เพราะเทมเพลตอยู่ที่นั่น (ยังไม่อยู่ใน main) · PR เข้า branch ของ Jam
- 2026-10-21 · Claude ไม่อ่านชีทหรือเสนอคำถาม/หน้า · ช่วยแค่เช็กรูปแบบ

## Next step

ขั้น 2: May เขียนคำถามในไฟล์ แล้วบอก Claude ให้เช็ก

## Waiting on

🙋 May เขียนคำถาม

## Notes for next time

- ชีทอยู่ใน Drive (ลิงก์ใน `evals/topics/mth10101/sources.md`) · เลขหน้าใช้ตาม PDF viewer · sheet-01 มี 140 หน้า, sheet-02 33 หน้า, sheet-03/04 3 หน้า
