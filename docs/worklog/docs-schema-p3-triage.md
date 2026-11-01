# แยกประเภท 5 ข้อของ schema จากผล P3 แล้วแก้ schema ตามที่ตัดสิน (D3)

| | |
|---|---|
| Owner | Junior · ทำต่อโดย Jam (2026-11-01) |
| Branch | `docs/schema-p3-triage` |
| Checklist item | ปรับ `schema.sql` ตามที่เจอระหว่าง P3 + วาด ERD (D3) |
| Status | in progress · 2026-11-01 |

## Plan

- [x] 1. 🤖 แก้ตาราง "สิ่งที่อาจต้องแก้ใน schema จาก P3a" ใน `specs/system/data-model.md` ให้แต่ละข้อมีประเภท (ยืนยันแล้วจาก P3 / ตัดสินด้วย design กับ Jam / รอ A6–A7 บน Vertex) พร้อมหลักฐานจาก `poc/P3/results/` และ report P3 (PR #37)
- [x] 2. 🙋 คุยกับ Jam เรื่องข้อที่ต้องตัดสินด้วย design (ใช้ข้อความที่ Claude ร่างให้) แล้วจดผลลงใน Decisions
- [x] 3. 🤖 เขียน migration `0003` ตามที่ตัดสิน (ถ้ามีตารางใหม่ ต้องมี `tenant_id` + RLS + isolation test) + อัปเดต ERD · ถ้าตัดสินว่าไม่ต้องแก้ ข้ามขั้นนี้
- [ ] 4. 🙋 ยืนยันก่อนรัน `npx supabase db push` ขึ้น `anyang-dev` และ `anyang-staging`
- [x] 5. 🤖 อัปเดต `sprint-checklists.md` และ `data-model.md` เป็นสถานะสุดท้าย

## Definition of done

- ทั้ง 5 ข้อใน `data-model.md` มีข้อสรุป (แก้ / ไม่แก้ / เลื่อนไปขั้นไหน พร้อมเหตุผล)
- ข้อที่ตัดสินว่าแก้ มี migration + ERD ตรงกัน และ CI (รวม `test_SA06_tenant_isolation`) ผ่าน

## Done today

- 2026-11-01 · (Jam ช่วง solo) ขั้น 3: test ใหม่ `test_SM04_bad_page_range_is_rejected` (แดง `PGRST205` ก่อนมีตาราง) · `supabase/migrations/0003_topic_sources.sql` (ตาราง + check + index 2 ตัว + RLS `tenant_rows` + `map_note`) · ERD รูป 2 + ตาราง migration ใน `data-model.md` v1.3
- 2026-10-28 · ขั้น 2: จดผลการตัดสิน 5 ข้อใน `data-model.md` (commit `5996f69`) · ตรวจแล้วว่า check ของ `scope_changes.op/actor` รับ `'exclude'`/`'ai'` อยู่แล้ว ข้อ 4 จึงไม่ต้องแก้
- 2026-10-28 · ขั้น 3 (test ก่อน): เพิ่ม `topic_sources` ใน `test_SA06_tenant_isolation` + ไฟล์ใหม่ `tests/integration/test_scope_sources.py` (SM-04 ช่วงหน้าข้ามไฟล์, CM-10 cascade จากไฟล์และหัวข้อ, SM-04 `map_note`) · ทุกตัวแดงเพราะยังไม่มีตาราง/column (PGRST205, PGRST204) · commit `07c5de3` (wip, ยังไม่ผ่าน review)

- 2026-10-21 · ขั้น 1: แยกประเภท 5 ข้อใน `specs/system/data-model.md` พร้อมหลักฐานและข้อเสนอ (commit `d7b48c2`)
- 2026-10-21 · ร่างข้อความถึง Jam + May ให้ Junior ส่งในแชทกลุ่ม (ข้อเสนอ = คอลัมน์ "ข้อเสนอ" ใน `data-model.md`)

## Decisions

- 2026-11-01 · Jam (ช่วง solo) ตอบแทน 2 คำถามของขั้น 3: (1) test ใน `07c5de3` ผ่าน review ไม่ต้องแก้ (2) ใส่ `check (page_from >= 1 and page_to >= page_from)` ตามที่ Claude แนะนำ + test `test_SM04_bad_page_range_is_rejected` (ช่วงกลับด้าน, หน้า 0) · การตัดสินเรื่อง DB เป็นของ Junior จึงให้ Junior ยืนยันทีหลัง ถ้าไม่เอาให้ลบด้วย migration ใหม่
- 2026-11-01 · เพิ่ม index `topic_sources (topic_id)` และ `(material_id)` ตามแบบ `0001_init.sql` (FK ที่ใช้ค้นและ cascade)
- 2026-10-28 · Jam ok ข้อ 1, 2, 4, 5 ตามข้อเสนอใน `data-model.md` · May ข้อ 3: หน้า scope แสดงเหตุผลของการ map → เพิ่ม `past_exam_questions.map_note` เก็บ `note` ของ A7 ทุกข้อ (ไม่ใช่เฉพาะข้อที่ map ไม่ได้) · migration `0003` จึงมี 2 อย่าง: ตาราง `topic_sources` + column `map_note`
- 2026-10-21 · ไม่มีข้อไหนต้องรอ A6/A7 บน Vertex · รูปแบบ output มาจาก Pydantic schema (`scope_ai.py`) ไม่ได้มาจาก model และ flash-lite รัน A6 กับ A7 ผ่าน schema แล้ว · ข้อ 3 กับ 4 ใช้ข้อมูล MTH10101 วัดไม่ได้อยู่แล้ว (label ไม่มีข้อ unmapped และรันโดย `user_notes = "ไม่มี"`)

## Next step

ขั้น 3 และ 5 เสร็จแล้ว · `/work-done` (ติ๊ก D3 ใน `sprint-checklists.md`) · ขั้น 4 (`db push`) Junior ทำหลัง merge

## Waiting on

- 🙋 Junior: ยืนยันการตัดสินของ Jam เรื่อง check ของช่วงหน้า (Decisions 2026-11-01)
- 🙋 Junior: ขั้น 4 `npx supabase db push` ขึ้น `anyang-dev` และ `anyang-staging` หลัง merge (Junior เท่านั้นที่รันได้) · CI `api-integration` ใช้ Supabase local จึงผ่านได้ก่อน push · แต่ test ในเครื่องที่ชี้ไป cloud จะแดงจนกว่าจะ push
- Junior: `topics.order_index` เริ่มที่ 0 หรือ 1 · api.md v1.6 (PR #100) บอกว่า `ScopeTopic.order` นับจาก 1 · ingest เขียนเลขเริ่มที่ 1 หรือให้ API บวก 1 · test ตอนนี้ใส่ 0

## Notes for next time

- เวลา pipe ข้อความไทยเข้า python บนเครื่อง Windows นี้ ให้ตั้ง `PYTHONUTF8=1` (หรือ `PYTHONIOENCODING=utf-8`) ก่อน ไม่งั้น python อ่าน pipe ด้วย encoding default ของ Windows แล้วพิมพ์ออกมาเป็น mojibake (ข้อมูลจริงไม่เสีย) เช่น `git show ... | PYTHONUTF8=1 python -c ...`
- CI `api-integration` บางครั้งแดงเพราะ Docker Hub rate limit ตอน `supabase start` ไม่ได้เกิดจากโค้ด · ให้ rerun เฉพาะ job ที่ fail (`gh run rerun <run-id> --failed`) · ติดตามที่ issue #66
- ข้อเท็จจริงที่ใช้ในข้อ 1: `chunks` มี `material_id` + `page_from/page_to` และ FK ทุกตัวที่ชี้ไป `materials` เป็น `on delete cascade` (`0001_init.sql`)
- ผล P3 อยู่บน branch `origin/poc/P3` (PR #37 draft) ยังไม่อยู่บน main · ดู `poc/P3/results/gemini-3.5-flash-lite-a5v1/`
- 2026-10-28 · `uv run pytest tests/integration` ในเครื่องนี้รันกับ Supabase cloud host `mnwwhkbizjioibjvpnxl` (ยังไม่ได้ยืนยันว่าคือ `anyang-dev`) ไม่ใช่ local · test สร้าง user ชั่วคราวแล้วลบเอง · ถ้าอยากรันกับ migration ใหม่ก่อน `db push` ต้องรันกับ local Supabase (`npx supabase start` + ชี้ env ไป local)
- SA06 ใช้ข้อมูลตั้งต้นชุดเดียวกันทุกกรณี ตอนนี้จึงแดงทั้ง 4 กรณี (ไม่ใช่แค่ `topic_sources`) จนกว่า `0003` จะขึ้น DB ที่ test ชี้อยู่ · อย่าเปลี่ยน PR #67 จาก draft ก่อนนั้น
- 2026-11-01 · รัน integration กับ local ต้องส่ง env เอง: `eval "$(npx supabase status -o env)"` แล้ว `SUPABASE_URL="$API_URL" SUPABASE_ANON_KEY="$ANON_KEY" SUPABASE_SERVICE_ROLE_KEY="$SERVICE_ROLE_KEY" uv run pytest tests/integration` (env ชนะ `.env`) · เครื่องนี้ `supabase start` ล้มเพราะ studio/pg-meta ไม่ healthy ให้ใช้ `npx supabase start -x studio,postgres-meta` · หลังเปิด Docker ใหม่ๆ fixture อาจ timeout ตอนสร้าง user (ไม่ใช่ปัญหาของ migration) รันซ้ำแล้วผ่าน
