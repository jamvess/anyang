# Contract + stub ของ ingestion, แชทแก้ขอบเขต และ change log (D5 · ส่วนที่ 5)

| | |
|---|---|
| Owner | Jam (item of Junior) |
| Branch | `feat/scope-edit-stubs` |
| Checklist item | เขียน router หัวฟังก์ชันของทุก API ใน `specs/system/api.md` ให้หน้า `/docs` ครบ (D5) |
| Status | in progress · 2026-11-04 |

## Plan

ครึ่งหลังของ flow 2.3 (UC-02 ขั้น 6–12 · S11, S13, S14): `GET /exam-preps/{id}/ingestion`, `POST /exam-preps/{id}/scope/chat`, `GET /exam-preps/{id}/scope/changes` + ปุ่มของ UC-02 E5: `POST /materials/{id}/retry`, `DELETE /materials/{id}` · persona และบัญชีอยู่ PR อื่น

- [x] 1. 🤖 ร่าง contract (ข้อเสนอรอ Junior) จาก ai-orchestration §2.3.2, §2.3.4, §2.3.6, `ingestion_jobs` / `scope_changes` ใน `0001_init.sql`, UC-02, wireframe S11, S13, S14 และ SM-06, SM-07, SM-08, CM-07
- [x] 2. 🙋 Jam อ่านร่าง ตอบ ok · บอกแชทกลุ่มว่าจะแก้ `api.md` (ไฟล์ร่วม)
- [x] 3. 🤖 ใส่ร่างลง `api.md` v1.11 + "รอตัดสิน (v1.11 · Junior)"
- [x] 4. 🤖 test contract + stub · แดงก่อน
- [x] 5. 🙋 Jam review test
- [x] 6. 🤖 models + stub (`X-Stub: true`) · test เขียว + ruff
- [ ] 7. 🤖 `api-schema.ts` generate ใหม่ + บรรทัดความคืบหน้าใน checklist

## Definition of done

- `api.md` มี request/response/error ของ 5 endpoint และ payload ของ `scope_patch` · ข้อที่ยังไม่ตัดสินอยู่ใน "รอตัดสิน (v1.11 · Junior)"
- `/docs` แสดงครบ · stub ส่ง `X-Stub: true` · test + ruff + CI เขียว
- ข้อ D5 ยังไม่ติ๊ก (เหลือ persona + บัญชี)

## Decisions

- 2026-11-04 · ไม่มี feature spec ของหน้าจอ S11, S13, S14 · contract อิง UC-02 (May approve 2026-10-19), ai-orchestration §2.3, wireframe และ schema
- 2026-11-04 · Jam ok: แก้กฎ `stage` ของ v1.10 (กฎเดิมให้ `scope` ทั้งที่ยังสกัดหัวข้อไม่เสร็จ) · เพิ่ม `retry` กับ `DELETE /materials/{id}` เพราะปุ่มใน S11 ใช้ไม่ได้ถ้าไม่มี · นับ `scope/chat` ใน rate limit เดียวกับห้องติว (`gateway-guards.md` §2.1 + AC-26)
- 2026-11-04 · ย้าย `_stream` จาก `routers/room.py` เป็น `stubs.stream` และ `_RATE_LIMITED` เป็น `RATE_LIMITED_DOCS` ใน `app/rate_limit.py` · ใช้ร่วม 2 router แทนการ import ชื่อ private
- 2026-11-04 · `ScopePatchChanges` ตัด field ที่เป็น null ตอน serialize (model serializer) · หน้าเว็บเอา `changes` ไปทับการ์ด null จึงลบค่าเดิม · ใช้ `exclude_none` ที่ตัว stream ไม่ได้ เพราะ event อื่นมี null ที่ต้องส่ง เช่น `verdict.first_wrong_line`

## Next step

ขั้น 7: generate `apps/web/lib/api-schema.ts` ใหม่ + บรรทัดความคืบหน้า #106 ใน checklist · แล้ว `/work-done`

## Waiting on

- Junior: ตัดสิน contract (รอตัดสิน v1.11)
- May: feature spec ของ S11, S13, S14 · `pnpm gen:api`

## Notes for next time

- แบบของ stub: `app/routers/exam_prep.py` (PR #105) · SSE: `_stream` ใน `app/routers/room.py`
- ช่องว่างของ spec ที่ขั้น 1 ต้องตอบ:
  - `ingestion_jobs.stage` มี 7 ค่าและ `material_id` ห้าม null แต่หัวข้อกับดาวทำต่อ prep ไม่ใช่ต่อไฟล์ · S11 แสดงทั้งรายไฟล์และขั้นรวม
  - UC-02 E5 มีปุ่ม "ลองใหม่" และ "ไปต่อโดยไม่มีไฟล์นี้" แต่ api.md ยังไม่มี endpoint
  - `scope_patch.changes` ยังไม่กำหนดรูปแบบ · `reorder` กับ `add_topic` เปลี่ยนการ์ดมากกว่าใบเดียว
  - ประวัติแชท S13 ไม่มีที่เก็บ (`messages.session_id` ห้าม null)
  - rate limit ของ `gateway-guards.md` นับเฉพาะห้องติว แต่ `scope/chat` ก็เรียก AI ทุกข้อความ
