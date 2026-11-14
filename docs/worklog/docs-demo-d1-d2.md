# demo D1 + D2 แล้วต่อขั้น 1 (login บน anyang-dev)

| | |
|---|---|
| Owner | Junior |
| Branch | `docs/demo-d1-d2` |
| Checklist item | ⭐ demo D1 + D2: ตัดสิน login ใน demo และ Supabase ในเครื่อง (ภายใน จ. 16 พ.ย.) · และ ⭐ demo ขั้น 1: env ของ API ชี้ `anyang-dev` (cloud · ไม่ต้องลง Docker · hook เปิดใน Dashboard แล้ว) · ยืนยัน `tenant_id` ใน token · `AUTH_REQUIRED=true` วนได้กับหน้า login ของ May (UM-01) |
| Status | in progress · 2026-11-14 |

## Plan

- [x] 1. 🤖 บันทึก D1 + D2 + กติกา (ก)–(ง) ใน `docs/team/sprint-checklists.md` · ร่างข้อความกลุ่ม
- [x] 2. 🙋 ส่งข้อความกลุ่ม (D1 + D2) · ส่งแล้ว 14 พ.ย.
- [x] 3. 🙋+🤖 (14 พ.ย. · `migration list --remote` ครบ `0001`–`0006` · unlink แล้ว) `db push` `0005`, `0006` ขึ้น `anyang-dev`: Junior `link` → Claude `migration list --remote` + `db push --remote --dry-run` → Junior ok → Claude `db push --remote --yes` → Claude `unlink`
- [x] 4. 🙋 (14 พ.ย. · Confirm email ปิด · hook Enabled · บัญชี demo (ถาม Junior) มีแถวใน `profiles` พร้อม `tenant_id`) Dashboard `anyang-dev`: ปิด Confirm email · สร้างบัญชี demo · เช็คว่า Custom Access Token hook ยังเปิด
- [x] 5. 🤖 `docs/team/setup.md` A5: แถว `AUTH_REQUIRED` + หัวข้อ "env สำหรับ demo" (`APP_ENV=local`, `AUTH_REQUIRED=true`, `AI_PROVIDER=live` ชี้ `anyang-dev`) · ไม่แก้ `.env.example`
- [ ] 6. 🙋+🤖 ขั้น 1: Junior ตั้ง `.env` ที่ root ชี้ `anyang-dev` + `AUTH_REQUIRED=true` · Claude เขียน script เล็กใน scratchpad ที่ login ด้วย email/password (Junior พิมพ์รหัสเอง) แล้ว decode JWT ว่ามี `tenant_id` · เรียก API ไม่มี token → 401 · มี token → `GET /exam-preps` 200

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

ข้อ 6: Junior แก้ `.env` ที่ root ตาม `setup.md` "env สำหรับ demo" แล้วรัน API (`cd apps/api && uv run fastapi dev app/main.py`) · Claude เขียน script ใน scratchpad: login `anyang-dev` (Junior พิมพ์อีเมล/รหัสเอง) → decode JWT ดู `tenant_id` → เรียก `GET /exam-preps` ไม่มี token ต้องได้ 401 `missing_token` · มี token ต้องได้ 200

## Waiting on

- May: หน้า login ที่ส่ง `Authorization` (ขั้น 1 ฝั่งเว็บ)

## Notes for next time

- `db push` / `migration list` ใส่ `--remote` ทุกคำสั่ง · ไม่ใส่ CLI 3.x ชี้ local stack (เจอตอน `0003`) · push จริงใส่ `--yes`
- `anyang-dev` ref = `mnwwhkbizjioibjvpnxl` (ไม่ใช่ secret)

- งานต่อไปวันนี้: ⭐ demo ขั้น 3 (materials + Storage · migration `0007`) branch ใหม่
