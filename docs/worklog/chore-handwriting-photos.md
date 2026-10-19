# รวบรวมรูปลายมือ ≥ 30 รูป + ขอความยินยอม (D8)

| | |
|---|---|
| Owner | Jam |
| Branch | `chore/handwriting-photos` |
| Checklist item | รวบรวมรูปลายมือจากทุกคนให้ได้ ≥ 30 รูป + ขอความยินยอมเพื่อน (D8) |
| Status | in progress · 2026-10-19 |

## Plan

- [ ] 1. 🤖 `evals/handwriting/README.md`: วิธีถ่ายรูป, การตั้งชื่อไฟล์, เป้าความหลากหลายของชุดรูป, ที่เก็บใน Drive, ขั้นตอนขอความยินยอม
- [ ] 2. 🤖 `evals/handwriting/problems.md`: โจทย์ ~15 ข้อจาก MTH10101 (limit, อนุพันธ์, chain rule, implicit, แยกตัวประกอบ, สมการ) ครอบคลุม `answer_format` ทั้ง 3 แบบ เพื่อให้ P2 นำไปใช้ต่อได้
- [ ] 3. 🤖 `evals/handwriting/consent.md`: ข้อความขอความยินยอมสำหรับทำ Google Form + template ตารางรหัสคนเขียน (เก็บใน Drive เท่านั้น)
- [ ] 4. 🤖 `evals/handwriting/make_labels.py` (stdlib อย่างเดียว): อ่าน `photos.csv` + `raw/` แล้วสร้าง `labels.jsonl` แบบโครง (`lines` ว่างไว้ให้ May) เช็คไฟล์ที่ขาดหรือซ้ำ และสรุปความหลากหลายของชุดรูป
- [ ] 5. 🙋 Jam: สร้างโฟลเดอร์ใน Drive + Google Form ขอความยินยอม แล้วส่งโจทย์และวิธีถ่ายรูปให้ Junior, May และเพื่อน
- [ ] 6. 🙋 Jam: เก็บรูปให้ได้ ≥ 30 รูป เปลี่ยนชื่อเป็น `hw_001.jpg` … กรอกตารางรหัสใน Drive และ `photos.csv` แล้วก๊อปรูปลง `evals/handwriting/raw/`
- [ ] 7. 🤖 รัน `make_labels.py` แล้ว commit `labels.jsonl` แบบโครง เช็คว่าครบตามเป้า ติ๊ก checklist และเขียนข้อความส่งงานให้ May

## Definition of done

- มีรูปลายมือ ≥ 30 รูป ทั้งใน Drive ทีม และใน `evals/handwriting/raw/` บนเครื่อง
- คนเขียนทุกคนมีหลักฐานการให้ความยินยอมเก็บอยู่ใน Drive
- มี `evals/handwriting/labels.jsonl` แบบโครง 1 บรรทัดต่อ 1 รูป (มี `id`, `image`, `writer`, `problem`) ให้ May พิมพ์ `lines` ต่อได้
- ใน git ไม่มีรูปและไม่มีชื่อจริงของคนเขียน
- ติ๊ก checklist ข้อนี้ใน `docs/team/sprint-checklists.md`

## Decisions

- 2026-10-19 · เขียนวิธีเก็บรูปไว้ในไฟล์ใหม่ `evals/handwriting/README.md` ไม่แก้ `evals/README.md` · เพราะ PR #10 ยังแก้ไฟล์นั้นอยู่ ถ้าแก้ทั้งสองที่จะ conflict

## Next step

ขั้น 1: เขียน `evals/handwriting/README.md`

## Waiting on

ไม่มี

## Notes for next time

- กติกาการ label ลายมือ (LaTeX รายบรรทัด, `writer` เป็นรหัส) อยู่ใน `evals/README.md` ของ PR #10 (`docs/label-guide`)
- โจทย์ต้องไม่มาจากข้อสอบกลางภาค 2562/1 เพราะเป็นชุด held-out ของ P3
