# demo D1 + D2 แล้วต่อขั้น 1 (login บน anyang-dev)

| | |
|---|---|
| Owner | Junior |
| Branch | `docs/demo-d1-d2` |
| Checklist item | ⭐ demo D1 + D2: ตัดสิน login ใน demo และ Supabase ในเครื่อง (ภายใน จ. 16 พ.ย.) · และ ⭐ demo ขั้น 1: env ของ API ชี้ `anyang-dev` (cloud · ไม่ต้องลง Docker · hook เปิดใน Dashboard แล้ว) · ยืนยัน `tenant_id` ใน token · `AUTH_REQUIRED=true` วนได้กับหน้า login ของ May (UM-01) |
| Status | in progress · 2026-11-16 |

## Plan

- [x] 1. 🤖 บันทึก D1 + D2 + กติกา (ก)–(ง) ใน `docs/team/sprint-checklists.md` · ร่างข้อความกลุ่ม
- [x] 2. 🙋 ส่งข้อความกลุ่ม (D1 + D2) · ส่งแล้ว 14 พ.ย.
- [x] 3. 🙋+🤖 (14 พ.ย. · `migration list --remote` ครบ `0001`–`0006` · unlink แล้ว) `db push` `0005`, `0006` ขึ้น `anyang-dev`: Junior `link` → Claude `migration list --remote` + `db push --remote --dry-run` → Junior ok → Claude `db push --remote --yes` → Claude `unlink`
- [x] 4. 🙋 (14 พ.ย. · Confirm email ปิด · hook Enabled · บัญชี demo (ถาม Junior) มีแถวใน `profiles` พร้อม `tenant_id`) Dashboard `anyang-dev`: ปิด Confirm email · สร้างบัญชี demo · เช็คว่า Custom Access Token hook ยังเปิด
- [x] 5. 🤖 `docs/team/setup.md` A5: แถว `AUTH_REQUIRED` + หัวข้อ "env สำหรับ demo" (`APP_ENV=local`, `AUTH_REQUIRED=true`, `AI_PROVIDER=live` ชี้ `anyang-dev`) · ไม่แก้ `.env.example`
- [x] 6. 🙋+🤖 (15 พ.ย. · PASS: login OK role `authenticated` · มี `tenant_id` · ไม่มี token → 401 `missing_token` · มี token → 200 ไม่มี `X-Stub` · `[]`) ขั้น 1: Junior ตั้ง `.env` ที่ root ชี้ `anyang-dev` + `AUTH_REQUIRED=true` · Claude เขียน script เล็กใน scratchpad ที่ login ด้วย email/password ของบัญชี demo (ยกเว้นกติกา ก ครั้งเดียว · ดู Decisions · Junior พิมพ์รหัสเอง) แล้ว decode JWT ว่ามี `tenant_id` · เรียก API ไม่มี token → 401 · มี token → `GET /exam-preps` 200
- [x] 7. 🙋+🤖 (15 พ.ย. · `migration list --remote` ครบ `0001`–`0007` · unlink แล้ว · Junior review `0007` แล้ว) `db push` `0007` ขึ้น `anyang-dev` (Jam ฝากไว้ · PR #135): Junior `link` → Claude `db push --remote --dry-run` → Junior ok → Claude `db push --remote --yes` → `migration list --remote` ครบ `0001`–`0007` → `unlink`
- [x] 8. 🤖 (15 พ.ย.) เพิ่มข้อ "reset database password ของ anyang-dev" ใน S4 ของ Junior (`sprint-checklists.md`)
- [x] 9. 🙋+🤖 (16 พ.ย. · ซ้อม login ก่อน advisor update · PASS ทุกข้อ: redirect → `/login?next=…` · กลับหน้า scope "ไม่พบการเตรียมสอบนี้" (API 404) · รหัสผิดขึ้นข้อความถูก · `/logout` → `/login` แล้ว scope เด้งไป login อีก (API 401)) ขั้น 1 ผ่านหน้าเว็บของ May (#138 merge แล้ว): API `AUTH_REQUIRED=true` + `pnpm dev` ชี้ `anyang-dev` · ไม่มี session → `/login?next=…` · login บัญชี demo → กลับหน้าเดิม · หน้าเว็บส่ง `Authorization` แล้ว API ตอบ 200 · `/logout` → `/login`

## Definition of done

- D1, D2 บันทึกใน checklist พร้อมเหตุผลและกติกา · กลุ่มรับทราบ
- `anyang-dev` มี migration ถึง `0007`
- token ของบัญชีใน `anyang-dev` มี claim `tenant_id` · API ในเครื่อง `AUTH_REQUIRED=true` ตอบ 401 เมื่อไม่มี token และ 200 เมื่อมี
- `setup.md` บอกวิธีตั้ง env สำหรับ demo

## Decisions

- 2026-11-14 · D1: login ใน demo = email + password · Google (UM-02) ใน S5 · เพราะไม่ต้องตั้ง OAuth client ในสัปดาห์ที่แน่นที่สุด
- 2026-11-14 · D2: dev + demo ใช้ `anyang-dev` (cloud) · เพราะทีมไม่ใช้ Docker, ข้อมูล demo ใช้ร่วมกันได้, hook เปิดแล้ว · กติกา (ก)–(ง) ใน checklist
- 2026-11-15 · ยกเว้นกติกา ก ครั้งเดียว (Junior): check ข้อ 6 ใช้บัญชี demo เพราะอ่านอย่างเดียว (login + `GET /exam-preps`) · กติกา ก ยังเหมือนเดิม: ทดสอบอื่นใช้บัญชีของตัวเอง
- 2026-11-15 · migration Storage เป็น `0008` (`0007` คือ `topic_progress_d_max` ของ Jam) · Junior rotate secret key ของ `anyang-dev` แล้ว · DB password ยังไม่เปลี่ยน → reset หลัง advisor update (ข้อใน S4)
- 2026-11-14 · "demo วันจันทร์" = advisor update จ. 16 พ.ย. (โชว์ journey) · วิดีโอ 23 พ.ย. เป็น deadline แยก
- 2026-11-14 · `db push`: Junior `link` เอง · Claude รัน dry-run / push / unlink หลัง Junior ok

## Done today (2026-11-15)

- ข้อ 6: check ขั้น 1 ผ่าน (`check_login.py` · บัญชี demo ยกเว้นกติกา ก) · token ของ `anyang-dev` มี `tenant_id` · API ในเครื่อง `AUTH_REQUIRED=true`: ไม่มี token → 401 `missing_token` · มี token → `GET /exam-preps` 200 จาก DB จริง (ไม่มี `X-Stub` · บัญชี demo ยังไม่มี exam prep จึงได้ `[]`)
- ข้อ 7: `db push` `0007` ขึ้น `anyang-dev` (Junior review แล้ว) · remote ครบ `0001`–`0007` · unlink แล้ว
- ข้อ 8: เพิ่มข้อ "reset database password ของ anyang-dev" ใน S4 ของ Junior · โน้ตใต้ขั้น 8 ว่า `0007` ขึ้น dev แล้ว

## Done today (2026-11-16)

- merge `origin/main` (หน้า login ของ May #138) · ข้อ 9 ซ้อม login ผ่านหน้าเว็บ ผ่านทุกข้อ · ติ๊ก ⭐ ขั้น 1 ใน checklist พร้อมโน้ต

## Next step

ทุกข้อใน Plan เสร็จแล้ว · ติ๊ก D1 + D2 และขั้น 1 แล้ว → `/work-done` (PR #134 ยังเป็น draft) · **ถาม Junior ก่อน merge** · แล้วเริ่ม branch ใหม่ `feat/materials-storage` ⭐ demo ขั้น 3 (migration `0008`: bucket + storage policy + isolation test · endpoint 4 ตัวใน `apps/api/app/routers/exam_prep.py` ตอนนี้เป็น stub) ด้วย `/spec-feature`

## Waiting on

- (ไม่มี · หน้า login ของ May merge แล้ว #138)

## Notes for next time

- `db push` / `migration list` ใส่ `--remote` ทุกคำสั่ง · ไม่ใส่ CLI 3.x ชี้ local stack (เจอตอน `0003`) · push จริงใส่ `--yes`
- `anyang-dev` ref = `mnwwhkbizjioibjvpnxl` (ไม่ใช่ secret)
- `get_settings()` คืน `Settings` · ค่า env อยู่ใต้ `.env` (`get_settings().env.supabase_url`) ไม่ใช่ `get_settings().supabase_url` (script รอบแรกพังเพราะข้อนี้)
- script check login: login ด้วย `POST {SUPABASE_URL}/auth/v1/token?grant_type=password` + header `apikey` = anon key · decode payload ของ JWT · อยู่ใน scratchpad ซึ่งอาจถูกลบ ถ้าต้องใช้อีกให้เขียนใหม่ตามนี้
- secret key ของ `anyang-dev` rotate แล้ว 15 พ.ย. · DB password ยังเดิม (ข้อ reset ใน S4)
- `.vscode/` เป็น untracked ในเครื่อง Junior · ไม่ได้ commit
