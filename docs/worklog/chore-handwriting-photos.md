# รวบรวมรูปลายมือ ≥ 30 รูป + ขอความยินยอม (D8)

| | |
|---|---|
| Owner | Jam |
| Branch | `chore/handwriting-photos` |
| Checklist item | รวบรวมรูปลายมือจากทุกคนให้ได้ ≥ 30 รูป + ขอความยินยอมเพื่อน (D8) |
| Status | in progress · 2026-10-19 |

## Plan

- [x] 1. 🤖 `evals/handwriting/README.md`: วิธีถ่ายรูป, การตั้งชื่อไฟล์, เป้าความหลากหลายของชุดรูป, ที่เก็บใน Drive, ขั้นตอนขอความยินยอม
- [x] 2. 🤖 `evals/handwriting/problems.md`: โจทย์ ~15 ข้อจาก MTH10101 (limit, อนุพันธ์, chain rule, implicit, แยกตัวประกอบ, สมการ) ครอบคลุม `answer_format` ทั้ง 3 แบบ เพื่อให้ P2 นำไปใช้ต่อได้
- [x] 3. 🤖 `evals/handwriting/consent.md`: ข้อความขอความยินยอมสำหรับทำ Google Form + template ตารางรหัสคนเขียน (เก็บใน Drive เท่านั้น)
- [x] 4. 🤖 `evals/handwriting/make_labels.py` (stdlib อย่างเดียว): อ่าน `photos.csv` + `raw/` แล้วสร้าง `labels.jsonl` แบบโครง (`lines` ว่างไว้ให้ May) เช็คไฟล์ที่ขาดหรือซ้ำ และสรุปความหลากหลายของชุดรูป
- [ ] 5. 🙋 Jam: อัปโหลดใบลอก + เฉลยขึ้น Drive, สร้างโฟลเดอร์ `inbox`/`raw` + Google Form แล้วส่งใบลอกให้เพื่อน 5 คน (คนละ 4 รูป) และส่ง `problems.md` ให้ Junior, May (คนละ 10 รูป)
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
- 2026-10-19 · เป้าชุดรูป: ≥ 30 รูป, ≥ 5 คนเขียน, ≤ 10 รูปต่อคน, แต่ละ answer_format ≥ 5, มีบรรทัดผิด ≥ 8, มีขีดฆ่า ≥ 3 · เพื่อให้ P2 ใช้รูปชุดเดียวกันได้และไม่มีลายมือคนใดมีน้ำหนักมากเกินไป
- 2026-10-19 · ใช้ `photos.csv` (มีแค่รหัส) เป็นที่จดว่ารูปไหนใครเขียน ส่วนตารางที่จับคู่รหัสกับชื่อจริงอยู่ใน Drive
- 2026-10-19 · โจทย์ 17 ข้อ แบ่ง 3 หมวด (ก factored 4 ข้อ, ข expression 10 ข้อ, ค equation 3 ข้อ) · ให้คนเขียนทำอย่างน้อยหมวดละ 1 ข้อ · ถ้าคนเขียน ≥ 5 คน ทุก answer_format จะมี ≥ 5 รูปได้โดยไม่ต้องคุมรายคน
- 2026-10-19 · ถ้ารูปที่มีบรรทัดผิดยังไม่ถึง 8 รูป Jam เขียนคำตอบผิดเพิ่มเองโดยไม่จด error type ที่ตั้งใจไว้ · เพื่อให้ May label error type แบบไม่รู้คำตอบล่วงหน้า
- 2026-10-19 · consent บอกชัดว่าส่งรูปให้ Gemini, Claude, Mathpix ผ่าน API · เก็บถึง 31 พ.ค. 2570 · ถอนได้ (ลบใน 7 วัน) · ขออนุญาตแยกถ้าจะใส่รูปในรายงาน · ไม่รับรูปจากคนอายุต่ำกว่า 18 ปี (PDPA)
- 2026-10-19 · `make_labels.py` ใช้ stdlib อย่างเดียว รันผ่าน `uv run --project apps/api` · test อยู่ข้างๆ กัน (`evals/handwriting/test_make_labels.py`) แต่ CI ยังไม่รัน เพราะ CI รันแค่ `apps/api/tests`
- 2026-10-19 · เพื่อนนอกทีมทำโจทย์เลขไม่เป็น จึงเปลี่ยนให้**ลอก**วิธีทำจากใบลอกแทน (5 คน × 4 รูป) ส่วน Junior กับ May ทำโจทย์เอง (2 × 10) · ใบลอกตั้งใจให้มีบรรทัดผิด 8 ใบ (ครอบคลุม error type 5 แบบ) และมีการขีดฆ่า 3 ใบ · ข้อดีคือรูปที่ผิดมาจากลายมือหลายคน · ใบลอกและเฉลยเก็บใน Drive เท่านั้น เพื่อให้ May label แบบไม่รู้คำตอบล่วงหน้า · ทุกบรรทัดตรวจด้วย SymPy แล้ว
- 2026-10-19 · ลบตาราง "คำตอบผิดที่พบบ่อย" ออกจาก `problems.md` · เพราะเฉลยของใบลอกไม่ควรอยู่ใน repo

## Next step

ขั้น 5 (🙋 Jam): อัปโหลด `copy_sheets.html`, `copy_sheets_key.md`, `build_sheets.py` จาก scratchpad ขึ้น Drive `evals/handwriting/` แล้วทำตามคำแนะนำ A–C ในแชท (Drive folders, Google Form, ส่งข้อความ)

## Waiting on

ไม่มี

## Notes for next time

- กติกาการ label ลายมือ (LaTeX รายบรรทัด, `writer` เป็นรหัส) อยู่ใน `evals/README.md` ของ PR #10 (`docs/label-guide`)
- โจทย์ต้องไม่มาจากข้อสอบกลางภาค 2562/1 เพราะเป็นชุด held-out ของ P3
