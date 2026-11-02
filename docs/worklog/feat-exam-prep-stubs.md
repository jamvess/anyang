# Contract + stub ของ exam prep และ materials (D5 · ส่วนที่ 4)

| | |
|---|---|
| Owner | Jam (item of Junior) |
| Branch | `feat/exam-prep-stubs` |
| Checklist item | เขียน router หัวฟังก์ชันของทุก API ใน `specs/system/api.md` ให้หน้า `/docs` ครบ (D5) |
| Status | in progress · 2026-11-02 |

## Plan

ครึ่งแรกของ flow 2.3 (UC-02 ขั้น 1–5 · S07–S10): `POST /exam-preps`, `GET /exam-preps`, `POST /exam-preps/{id}/materials`, `POST /materials/{id}/uploaded`, `GET /exam-preps/{id}/materials`, `POST /exam-preps/{id}/materials/confirm` · `GET /exam-preps/{id}/ingestion` ทำใน PR ถัดไป

- [x] 1. 🤖 ร่าง contract (ข้อเสนอรอ Junior) จาก ai-orchestration §2.3.2, `exam_preps` / `materials` ใน `0001_init.sql`, UC-02 และ CM-01–CM-07
- [x] 2. 🙋 Jam อ่านร่าง ตอบ ok · บอกแชทกลุ่มว่าจะแก้ `api.md` (ไฟล์ร่วม)
- [x] 3. 🤖 ใส่ร่างลง `api.md` v1.10 + "รอตัดสิน (v1.10 · Junior)"
- [x] 4. 🤖 test contract + stub · แดงก่อน
- [x] 5. 🙋 Jam review test
- [x] 6. 🤖 models + stub (`X-Stub: true`) · test เขียว + ruff
- [ ] 7. 🤖 `api-schema.ts` generate ใหม่ + บรรทัดความคืบหน้าใน checklist

## Definition of done

- `api.md` มี request/response/error ของ 6 endpoint · ข้อที่ยังไม่ตัดสินอยู่ใน "รอตัดสิน (v1.10 · Junior)" รวมคำถามเปิดของ UC-02 (ชนิดและขนาดไฟล์, วันสอบในอดีต)
- `/docs` แสดงครบ · stub ส่ง `X-Stub: true` · test + ruff + CI เขียว
- ข้อ D5 ยังไม่ติ๊ก

## Decisions

- 2026-11-02 · แบ่งกลุ่ม exam prep เป็น 2 PR · `ingestion` (S11) อยู่ PR ถัดไป
- 2026-11-02 · ไม่มี feature spec ของหน้าจอ S07–S10 · contract อิง UC-02 (May approve 2026-10-19), ai-orchestration §2.3 และ schema
- 2026-11-02 · ย้าย `_stub_error`, `_STUB_STORAGE`, `_STUB_TENANT` จาก `routers/room.py` ไป `app/stubs` (`stubs.error`, `STORAGE_URL`, `tenant_of`) และ `_bare_type` ไป `models/room.py` (`bare_content_type`) · ใช้ร่วม 2 router แทนการ import ชื่อ private
- 2026-11-02 · `exam_preps.json` เก็บ `days_left` ไม่เก็บ `exam_date` · router นับวันจากวันนี้ fixture จึงไม่กลายเป็นอดีต

## Next step

ขั้น 7: generate `apps/web/lib/api-schema.ts` ใหม่ + บรรทัดความคืบหน้า #105 ใน checklist · แล้ว `/work-done`

## Waiting on

- Junior: ตัดสิน contract (รอตัดสิน v1.10) + คำถามเปิดของ UC-02 ข้อ 1–2
- Jam (threshold): ขนาดไฟล์สูงสุดของ materials ถ้าจะเพิ่มค่าใน `config/ai.yaml`
- May: หน้าจอ S07–S10 (feature spec) · `pnpm gen:api`

## Notes for next time

- แบบของ stub: `app/routers/scope.py` (PR #100), `app/routers/room.py`
