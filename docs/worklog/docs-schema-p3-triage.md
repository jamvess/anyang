# แยกประเภท 5 ข้อของ schema จากผล P3 แล้วแก้ schema ตามที่ตัดสิน (D3)

| | |
|---|---|
| Owner | Junior |
| Branch | `docs/schema-p3-triage` |
| Checklist item | ปรับ `schema.sql` ตามที่เจอระหว่าง P3 + วาด ERD (D3) |
| Status | paused · 2026-10-28 |

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

- 2026-10-28 · ขั้น 2: จดผลการตัดสิน 5 ข้อใน `data-model.md` (commit `5996f69`) · ตรวจแล้วว่า check ของ `scope_changes.op/actor` รับ `'exclude'`/`'ai'` อยู่แล้ว ข้อ 4 จึงไม่ต้องแก้
- 2026-10-28 · ขั้น 3 (test ก่อน): เพิ่ม `topic_sources` ใน `test_SA06_tenant_isolation` + ไฟล์ใหม่ `tests/integration/test_scope_sources.py` (SM-04 ช่วงหน้าข้ามไฟล์, CM-10 cascade จากไฟล์และหัวข้อ, SM-04 `map_note`) · ทุกตัวแดงเพราะยังไม่มีตาราง/column (PGRST205, PGRST204) · commit `07c5de3` (wip, ยังไม่ผ่าน review)

- 2026-10-21 · ขั้น 1: แยกประเภท 5 ข้อใน `specs/system/data-model.md` พร้อมหลักฐานและข้อเสนอ (commit `d7b48c2`)
- 2026-10-21 · ร่างข้อความถึง Jam + May ให้ Junior ส่งในแชทกลุ่ม (ข้อเสนอ = คอลัมน์ "ข้อเสนอ" ใน `data-model.md`)

## Decisions

- 2026-10-28 · Jam ok ข้อ 1, 2, 4, 5 ตามข้อเสนอใน `data-model.md` · May ข้อ 3: หน้า scope แสดงเหตุผลของการ map → เพิ่ม `past_exam_questions.map_note` เก็บ `note` ของ A7 ทุกข้อ (ไม่ใช่เฉพาะข้อที่ map ไม่ได้) · migration `0003` จึงมี 2 อย่าง: ตาราง `topic_sources` + column `map_note`
- 2026-10-21 · ไม่มีข้อไหนต้องรอ A6/A7 บน Vertex · รูปแบบ output มาจาก Pydantic schema (`scope_ai.py`) ไม่ได้มาจาก model และ flash-lite รัน A6 กับ A7 ผ่าน schema แล้ว · ข้อ 3 กับ 4 ใช้ข้อมูล MTH10101 วัดไม่ได้อยู่แล้ว (label ไม่มีข้อ unmapped และรันโดย `user_notes = "ไม่มี"`)

## Next step

ขั้น 3 ต่อ: ถาม Junior 2 อย่างก่อน (1) test ใน commit `07c5de3` ผ่าน review ไหม (ถ้าแก้ ให้แก้ test ก่อน) (2) ใส่ `check (page_from >= 1 and page_to >= page_from)` ใน `topic_sources` ไหม (Claude แนะนำให้ใส่ · ถ้าใส่ ให้เพิ่ม test ที่ insert ช่วงกลับด้านแล้วต้องได้ `APIError` ใน `test_scope_sources.py` ก่อน) · จากนั้นเขียน `supabase/migrations/0003_topic_sources.sql`: ตาราง `topic_sources (id uuid pk default gen_random_uuid(), tenant_id → tenants on delete cascade, topic_id → topics on delete cascade, material_id → materials on delete cascade, page_from int not null, page_to int not null)` + `enable row level security` + policy `tenant_rows` แบบเดียวกับ `0001_init.sql:462` + `alter table public.past_exam_questions add column map_note text` (comment บอกว่าเก็บ note ของ A7 ทุกข้อ · data-model.md ข้อ 3) · แล้ว `npx supabase db reset` ในเครื่อง + อัปเดต ERD

## Waiting on

- 🙋 Junior: review test ขั้น 3 (`07c5de3`) + ตัดสินเรื่อง check ของช่วงหน้า

## Notes for next time

- เวลา pipe ข้อความไทยเข้า python บนเครื่อง Windows นี้ ให้ตั้ง `PYTHONUTF8=1` (หรือ `PYTHONIOENCODING=utf-8`) ก่อน ไม่งั้น python อ่าน pipe ด้วย encoding default ของ Windows แล้วพิมพ์ออกมาเป็น mojibake (ข้อมูลจริงไม่เสีย) เช่น `git show ... | PYTHONUTF8=1 python -c ...`
- CI `api-integration` บางครั้งแดงเพราะ Docker Hub rate limit ตอน `supabase start` ไม่ได้เกิดจากโค้ด · ให้ rerun เฉพาะ job ที่ fail (`gh run rerun <run-id> --failed`) · ติดตามที่ issue #66
- ข้อเท็จจริงที่ใช้ในข้อ 1: `chunks` มี `material_id` + `page_from/page_to` และ FK ทุกตัวที่ชี้ไป `materials` เป็น `on delete cascade` (`0001_init.sql`)
- ผล P3 อยู่บน branch `origin/poc/P3` (PR #37 draft) ยังไม่อยู่บน main · ดู `poc/P3/results/gemini-3.5-flash-lite-a5v1/`
- 2026-10-28 · `uv run pytest tests/integration` ในเครื่องนี้รันกับ Supabase cloud host `mnwwhkbizjioibjvpnxl` (ยังไม่ได้ยืนยันว่าคือ `anyang-dev`) ไม่ใช่ local · test สร้าง user ชั่วคราวแล้วลบเอง · ถ้าอยากรันกับ migration ใหม่ก่อน `db push` ต้องรันกับ local Supabase (`npx supabase start` + ชี้ env ไป local)
- SA06 ใช้ข้อมูลตั้งต้นชุดเดียวกันทุกกรณี ตอนนี้จึงแดงทั้ง 4 กรณี (ไม่ใช่แค่ `topic_sources`) จนกว่า `0003` จะขึ้น DB ที่ test ชี้อยู่ · อย่าเปลี่ยน PR #67 จาก draft ก่อนนั้น
