# แยกประเภท 5 ข้อของ schema จากผล P3 แล้วแก้ schema ตามที่ตัดสิน (D3)

| | |
|---|---|
| Owner | Junior |
| Branch | `docs/schema-p3-triage` |
| Checklist item | ปรับ `schema.sql` ตามที่เจอระหว่าง P3 + วาด ERD (D3) |
| Status | in progress · 2026-10-21 |

## Plan

- [ ] 1. 🤖 แก้ตาราง "สิ่งที่อาจต้องแก้ใน schema จาก P3a" ใน `specs/system/data-model.md` ให้แต่ละข้อมีประเภท (ยืนยันแล้วจาก P3 / ตัดสินด้วย design กับ Jam / รอ A6–A7 บน Vertex) พร้อมหลักฐานจาก `poc/P3/results/` และ report P3 (PR #37)
- [ ] 2. 🙋 คุยกับ Jam เรื่องข้อที่ต้องตัดสินด้วย design (ใช้ข้อความที่ Claude ร่างให้) แล้วจดผลลงใน Decisions
- [ ] 3. 🤖 เขียน migration `0003` ตามที่ตัดสิน (ถ้ามีตารางใหม่ ต้องมี `tenant_id` + RLS + isolation test) + อัปเดต ERD · ถ้าตัดสินว่าไม่ต้องแก้ ข้ามขั้นนี้
- [ ] 4. 🙋 ยืนยันก่อนรัน `npx supabase db push` ขึ้น `anyang-dev` และ `anyang-staging`
- [ ] 5. 🤖 อัปเดต `sprint-checklists.md` และ `data-model.md` เป็นสถานะสุดท้าย

## Definition of done

- ทั้ง 5 ข้อใน `data-model.md` มีข้อสรุป (แก้ / ไม่แก้ / เลื่อนไปขั้นไหน พร้อมเหตุผล)
- ข้อที่ตัดสินว่าแก้ มี migration + ERD ตรงกัน และ CI (รวม `test_SA06_tenant_isolation`) ผ่าน

## Decisions

- 2026-10-21 · ไม่มีข้อไหนต้องรอ A6/A7 บน Vertex · รูปแบบ output มาจาก Pydantic schema (`scope_ai.py`) ไม่ได้มาจาก model และ flash-lite รัน A6 กับ A7 ผ่าน schema แล้ว · ข้อ 3 กับ 4 ใช้ข้อมูล MTH10101 วัดไม่ได้อยู่แล้ว (label ไม่มีข้อ unmapped และรันโดย `user_notes = "ไม่มี"`)

## Next step

ขั้น 1: แก้ตารางใน `specs/system/data-model.md` บรรทัด 365–377

## Waiting on

ไม่มี

## Notes for next time

- ผล P3 อยู่บน branch `origin/poc/P3` (PR #37 draft) ยังไม่อยู่บน main · ดู `poc/P3/results/gemini-3.5-flash-lite-a5v1/`
