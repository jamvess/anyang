# ERD ของ data model ให้ครบตาม `0001_init.sql` (D3)

| | |
|---|---|
| Owner | Junior |
| Branch | `docs/erd-d3` |
| Checklist item | ปรับ `schema.sql` ตามที่เจอระหว่าง P3 + วาด ERD (D3) |
| Status | in progress · 2026-10-19 |

## Plan

- [ ] 1. 🤖 เทียบ ERD ใน `specs/system/data-model.md` กับ foreign key ทุกตัวใน `supabase/migrations/0001_init.sql` แล้วจดส่วนที่ขาดหรือผิด
- [ ] 2. 🤖 วาด ERD ใหม่ แยกเป็น 3 รูปตามกลุ่ม (Tenancy + User · Content + Scope · Tutoring + Progress + Logs) ใส่ PK/FK และ column สำคัญ · ไม่ลากเส้น `tenant_id` ไปหา `tenants` ทุกตาราง แต่เขียนเป็นกฎไว้แทน
- [ ] 3. 🙋 Junior เปิดไฟล์บน GitHub (branch `docs/erd-d3` → `specs/system/data-model.md`) แล้วดูว่า diagram ทั้ง 3 รูปแสดงผลได้และอ่านรู้เรื่อง
- [ ] 4. 🤖 อ่าน `poc/P3` แล้วจดสิ่งที่อาจต้องแก้ใน schema ลงหัวข้อ "สิ่งที่ยังรอผล PoC" (ยังไม่เขียน migration จนกว่า P3 จะมีผล)
- [ ] 5. 🤖 `/work-check` แล้ว `/work-done`

## Definition of done

- ERD มีครบทุกตาราง (28 ตาราง) และทุก foreign key ใน `0001_init.sql`
- ทั้ง 3 diagram แสดงผลบน GitHub ได้
- สิ่งที่ต้องแก้ใน schema หลัง P3 มีจดไว้ชัดเจน · ข้อใน checklist ยังไม่ติ๊กจนกว่าจะแก้ schema ตามผล P3

## Decisions

- 2026-10-19 · แก้ ERD ก่อน ยังไม่แก้ schema · ผล P3 ยังไม่ออก (Jam รันต่อ 20 ต.ค.) ส่วน ERD ทำจาก schema ปัจจุบันได้เลย

## Next step

ขั้น 1: เทียบ ERD กับ foreign key ใน `0001_init.sql`

## Waiting on

ไม่มี

## Notes for next time

- `data-model.md` อยู่ใน `specs/` แต่ D3 เป็นงานของ Junior (`roles.md`) · แก้แค่ภาพและคำอธิบาย ไม่เปลี่ยน behavior
