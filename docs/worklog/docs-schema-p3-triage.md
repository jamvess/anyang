# แยกประเภท 5 ข้อของ schema จากผล P3 แล้วแก้ schema ตามที่ตัดสิน (D3)

| | |
|---|---|
| Owner | Junior |
| Branch | `docs/schema-p3-triage` |
| Checklist item | ปรับ `schema.sql` ตามที่เจอระหว่าง P3 + วาด ERD (D3) |
| Status | in progress · 2026-10-28 |

## Plan

- [x] 1. 🤖 แก้ตาราง "สิ่งที่อาจต้องแก้ใน schema จาก P3a" ใน `specs/system/data-model.md` ให้แต่ละข้อมีประเภท (ยืนยันแล้วจาก P3 / ตัดสินด้วย design กับ Jam / รอ A6–A7 บน Vertex) พร้อมหลักฐานจาก `poc/P3/results/` และ report P3 (PR #37)
- [x] 2. 🙋 คุยกับ Jam เรื่องข้อที่ต้องตัดสินด้วย design (ใช้ข้อความที่ Claude ร่างให้) แล้วจดผลลงใน Decisions
- [ ] 3. 🤖 เขียน migration `0003` ตามที่ตัดสิน (ถ้ามีตารางใหม่ ต้องมี `tenant_id` + RLS + isolation test) + อัปเดต ERD · ถ้าตัดสินว่าไม่ต้องแก้ ข้ามขั้นนี้
- [ ] 4. 🙋 ยืนยันก่อนรัน `npx supabase db push` ขึ้น `anyang-dev` และ `anyang-staging`
- [ ] 5. 🤖 อัปเดต `sprint-checklists.md` และ `data-model.md` เป็นสถานะสุดท้าย

## Definition of done

- ทั้ง 5 ข้อใน `data-model.md` มีข้อสรุป (แก้ / ไม่แก้ / เลื่อนไปขั้นไหน พร้อมเหตุผล)
- ข้อที่ตัดสินว่าแก้ มี migration + ERD ตรงกัน และ CI (รวม `test_SA06_tenant_isolation`) ผ่าน

## Done today

- 2026-10-21 · ขั้น 1: แยกประเภท 5 ข้อใน `specs/system/data-model.md` พร้อมหลักฐานและข้อเสนอ (commit `d7b48c2`)
- 2026-10-21 · ร่างข้อความถึง Jam + May ให้ Junior ส่งในแชทกลุ่ม (ข้อเสนอ = คอลัมน์ "ข้อเสนอ" ใน `data-model.md`)

## Decisions

- 2026-10-28 · Jam ok ข้อ 1, 2, 4, 5 ตามข้อเสนอใน `data-model.md` · May ข้อ 3: หน้า scope แสดงเหตุผลของการ map → เพิ่ม `past_exam_questions.map_note` เก็บ `note` ของ A7 ทุกข้อ (ไม่ใช่เฉพาะข้อที่ map ไม่ได้) · migration `0003` จึงมี 2 อย่าง: ตาราง `topic_sources` + column `map_note`
- 2026-10-21 · ไม่มีข้อไหนต้องรอ A6/A7 บน Vertex · รูปแบบ output มาจาก Pydantic schema (`scope_ai.py`) ไม่ได้มาจาก model และ flash-lite รัน A6 กับ A7 ผ่าน schema แล้ว · ข้อ 3 กับ 4 ใช้ข้อมูล MTH10101 วัดไม่ได้อยู่แล้ว (label ไม่มีข้อ unmapped และรันโดย `user_notes = "ไม่มี"`)

## Next step

ขั้น 3: เขียน `supabase/migrations/0003_topic_sources.sql` (ตาราง `topic_sources` มี `tenant_id` + RLS policy `tenant_rows` + FK `on delete cascade` ไป `topics` และ `materials` · และ `alter table past_exam_questions add column map_note text`) แล้วเพิ่ม `topic_sources` ใน `test_SA06_tenant_isolation` + ERD

## Waiting on

- ไม่มี

## Notes for next time

- เวลา pipe ข้อความไทยเข้า python บนเครื่อง Windows นี้ ให้ตั้ง `PYTHONUTF8=1` (หรือ `PYTHONIOENCODING=utf-8`) ก่อน ไม่งั้น python อ่าน pipe ด้วย encoding default ของ Windows แล้วพิมพ์ออกมาเป็น mojibake (ข้อมูลจริงไม่เสีย) เช่น `git show ... | PYTHONUTF8=1 python -c ...`
- CI `api-integration` บางครั้งแดงเพราะ Docker Hub rate limit ตอน `supabase start` ไม่ได้เกิดจากโค้ด · ให้ rerun เฉพาะ job ที่ fail (`gh run rerun <run-id> --failed`) · ติดตามที่ issue #66
- ข้อเท็จจริงที่ใช้ในข้อ 1: `chunks` มี `material_id` + `page_from/page_to` และ FK ทุกตัวที่ชี้ไป `materials` เป็น `on delete cascade` (`0001_init.sql`)
- ผล P3 อยู่บน branch `origin/poc/P3` (PR #37 draft) ยังไม่อยู่บน main · ดู `poc/P3/results/gemini-3.5-flash-lite-a5v1/`
