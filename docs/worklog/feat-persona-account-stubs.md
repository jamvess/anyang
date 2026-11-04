# Contract + stub ของ persona และบัญชี (D5 · ส่วนสุดท้าย)

| | |
|---|---|
| Owner | Jam (item of Junior) |
| Branch | `feat/persona-account-stubs` |
| Checklist item | เขียน router หัวฟังก์ชันของทุก API ใน `specs/system/api.md` ให้หน้า `/docs` ครบ (D5) |
| Status | in progress · 2026-11-04 |

## Plan

กลุ่มสุดท้ายของ D5 (flow 2.7 · UC-01 · S04–S06): `GET /personas/presets`, `POST /personas/extract`, `PUT /me/tutor-profile`, `PUT /me/buddy-profile`, `GET`/`PUT /me/profile`, `DELETE /me`, `DELETE /exam-preps/{id}`

- [x] 1. 🤖 ร่าง contract (ข้อเสนอรอ Junior) จาก ai-orchestration §2.7, `profiles` / `tutor_profiles` / `buddy_profiles` ใน `0001_init.sql`, UC-01, wireframe S04–S06 และ UM-03–UM-10, CM-10
- [x] 2. 🙋 Jam อ่านร่าง ตอบ ok · บอกแชทกลุ่มว่าจะแก้ `api.md` (ไฟล์ร่วม)
- [x] 3. 🤖 ใส่ร่างลง `api.md` v1.12 + "รอตัดสิน (v1.12 · Junior)"
- [ ] 4. 🤖 test contract + stub · แดงก่อน
- [ ] 5. 🙋 Jam review test
- [ ] 6. 🤖 models + stub (`X-Stub: true`) · test เขียว + ruff
- [ ] 7. 🤖 `api-schema.ts` generate ใหม่ + ติ๊กข้อ D5 ใน checklist ถ้า `/docs` ครบทุก endpoint ใน `api.md`

## Definition of done

- `api.md` มี request/response/error ของทุก endpoint กลุ่มนี้ · ข้อที่ยังไม่ตัดสินอยู่ใน "รอตัดสิน (v1.12 · Junior)"
- test เทียบรายการ endpoint ใน `api.md` กับ `/openapi.json` แล้วครบ · `/docs` แสดงครบ · stub ส่ง `X-Stub: true` · test + ruff + CI เขียว
- ข้อ D5 ติ๊กได้ตามข้อความในข้อ ("ให้หน้า `/docs` ครบ") · ส่วนที่ Junior ยังไม่ตัดสินคงอยู่ใน "รอตัดสิน" ทุกรุ่น

## Decisions

- 2026-11-04 · ไม่มี feature spec ของหน้าจอ S04–S06 · contract อิง UC-01 (May approve 2026-10-19), ai-orchestration §2.7, wireframe และ schema
- 2026-11-04 · Jam ok: เพิ่ม `GET` ของ persona 2 ตัวและ `setup_step` (UM-09, UC-01 E6) · นับ `/personas/extract` ใน rate limit เดียวกับห้องติว (`gateway-guards.md` §2.1 + AC-27) · threshold `guards.max_persona_text_chars: 20` ป้าย `[C]` เพราะ `name`, `self_pronoun`, `call_user` เข้า prompt · `description` ใช้ `guards.max_message_chars` เดิม

## Next step

ขั้น 4: เขียน test contract + stub จาก api.md v1.12 และ AC-11, AC-27 ของ `gateway-guards.md` · รวม test เทียบรายการ endpoint ใน api.md กับ `/openapi.json` · ให้แดงก่อน · ค่า config ใส่ตอนขั้น 6 พร้อม settings

## Waiting on

- Junior: ตัดสิน contract (รอตัดสิน v1.12)
- May: feature spec ของ S04–S06 และหน้าตั้งค่า (UM-09) · `pnpm gen:api`

## Notes for next time

- แบบของ stub: `app/routers/exam_prep.py`, `app/routers/scope.py` · `stubs.error`, `stubs.stream`, `error_docs`
- ช่องว่างของ spec ที่ขั้น 1 ต้องตอบ:
  - ตาราง api.md มีแต่ `PUT` ของ persona แต่ UM-09 ต้องแก้ทีหลัง และ UC-01 E6 ต้องรู้ว่าตั้งค่าถึงขั้นไหน จึงต้องมีทางอ่าน
  - สวิตช์อ่านออกเสียงอัตโนมัติ (TM-09 · UC-01 A3 ข้อ 4) ยังไม่มีที่เก็บ
  - `/personas/extract` เรียก AI แต่ `gateway-guards.md` ยังไม่นับใน rate limit
  - `DELETE /me` ต้องลบ `auth.users` ด้วย service role และลบไฟล์ใน Storage
