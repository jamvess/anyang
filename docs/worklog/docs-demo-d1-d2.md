# demo D1 + D2 แล้วต่อขั้น 1 (login บน anyang-dev)

| | |
|---|---|
| Owner | Junior |
| Branch | `docs/demo-d1-d2` |
| Checklist item | ⭐ demo D1 + D2: ตัดสิน login ใน demo และ Supabase ในเครื่อง (ภายใน จ. 16 พ.ย.) · และ ⭐ demo ขั้น 1: env ของ API ชี้ Supabase ในเครื่อง (hook เปิดใน `supabase/config.toml` แล้ว) · ยืนยัน `tenant_id` ใน token · `AUTH_REQUIRED=true` วนได้กับหน้า login ของ May (UM-01) |
| Status | in progress · 2026-11-14 |

## Plan

- [x] 1. 🤖 บันทึก D1 + D2 + กติกา (ก)–(ง) ใน `docs/team/sprint-checklists.md` · ร่างข้อความกลุ่ม
- [ ] 2. 🙋 ส่งข้อความกลุ่ม (D1 + D2)
- [ ] 3. 🙋+🤖 `db push` `0005`, `0006` ขึ้น `anyang-dev`: Junior `link` → Claude `db push --dry-run` → Junior ok → Claude `db push` → Claude `unlink`
- [ ] 4. 🙋 Dashboard `anyang-dev`: ปิด Confirm email · สร้างบัญชี demo · เช็คว่า Custom Access Token hook ยังเปิด
- [ ] 5. 🤖 `docs/team/setup.md` A5: env สำหรับ demo (`AUTH_REQUIRED=true` ชี้ `anyang-dev`) · `.env.example` (shared file · ถาม Junior ก่อน)
- [ ] 6. 🙋+🤖 ขั้น 1: Junior ตั้ง `apps/api/.env` ชี้ `anyang-dev` + `AUTH_REQUIRED=true` · Claude เขียน script เล็กใน scratchpad ที่ login ด้วย email/password (Junior พิมพ์รหัสเอง) แล้ว decode JWT ว่ามี `tenant_id` · เรียก API ไม่มี token → 401 · มี token → `GET /exam-preps` 200

## Definition of done

- D1, D2 บันทึกใน checklist พร้อมเหตุผลและกติกา · กลุ่มรับทราบ
- `anyang-dev` มี migration ถึง `0006`
- token ของบัญชีใน `anyang-dev` มี claim `tenant_id` · API ในเครื่อง `AUTH_REQUIRED=true` ตอบ 401 เมื่อไม่มี token และ 200 เมื่อมี
- `setup.md` บอกวิธีตั้ง env สำหรับ demo

## Decisions

- 2026-11-14 · D1: login ใน demo = email + password · Google (UM-02) ใน S5 · เพราะไม่ต้องตั้ง OAuth client ในสัปดาห์ที่แน่นที่สุด
- 2026-11-14 · D2: dev + demo ใช้ `anyang-dev` (cloud) · เพราะทีมไม่ใช้ Docker, ข้อมูล demo ใช้ร่วมกันได้, hook เปิดแล้ว · กติกา (ก)–(ง) ใน checklist
- 2026-11-14 · "demo วันจันทร์" = advisor update จ. 16 พ.ย. (โชว์ journey) · วิดีโอ 23 พ.ย. เป็น deadline แยก
- 2026-11-14 · `db push`: Junior `link` เอง · Claude รัน dry-run / push / unlink หลัง Junior ok · migration Storage จะเป็น `0007`

## Next step

ข้อ 2–3: Junior ส่งข้อความกลุ่ม แล้วรัน `npx supabase link --project-ref <ref ของ anyang-dev>` · จากนั้น Claude รัน `npx supabase db push --dry-run` ให้ดู

## Waiting on

- May: หน้า login ที่ส่ง `Authorization` (ขั้น 1 ฝั่งเว็บ)

## Notes for next time

- งานต่อไปวันนี้: ⭐ demo ขั้น 3 (materials + Storage · migration `0007`) branch ใหม่
