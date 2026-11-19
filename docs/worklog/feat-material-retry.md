# POST /materials/{id}/retry ใช้งานจริง (API)

| | |
|---|---|
| Owner | Junior |
| Branch | `feat/material-retry` |
| Checklist item | (ใหม่ · ก่อนอัดวิดีโอ) `POST /materials/{id}/retry` ใช้งานจริง ให้ไฟล์ที่ "ลองใหม่ได้" ลองใหม่ได้จริง (UC-02 E5 · CM-07) |
| Status | in progress · 2026-11-19 |

## Plan

- [ ] 1. 🤖 Spec: `specs/features/exam-prep/material-retry.md` (`/spec-feature`) · เส้น JWT/RLS · `failed` → `uploaded` (ล้มตอน classify) หรือ `confirmed` (ล้มตอน ingest) แบบมีเงื่อนไข `status = failed` · `404` · `409 not_failed` · `503 db_unavailable` · เริ่ม `runner.classify` / `runner.start` ใต้ `ai_call_context` ไม่รอ · ไม่แก้ `ingestion.py` ของ Jam
- [ ] 2. 🙋 Junior review spec
- [ ] 3. 🤖 Red tests (`/spec-to-tests`)
- [ ] 4. 🙋 Junior review tests
- [ ] 5. 🤖 Implement (`/implement-feature`) · `api.md` ลบ "ยังเป็น stub" ของ `/retry` (ไฟล์กลาง · แจ้งกลุ่ม)
- [ ] 6. 🙋 ลองกด retry จริงบน dev (หลังปุ่มของ May หรือยิงด้วย curl/`/docs`)

## Definition of done

- `/retry` ด้วย token ของเจ้าของไฟล์ → ไฟล์ที่ล้มกลับไปทำงานใหม่ และจบที่ `classified`/`ready` หรือ `failed` อีกครั้ง (ไม่ค้าง)
- ไม่มี token → stub เดิม (test สัญญาที่ review แล้วผ่านโดยไม่แก้)
- test ทุก AC ผ่าน · CI เขียว

## Decisions

- 2026-11-19 · ทำก่อนอัดวิดีโอ · ไฟล์ค้าง "ลองใหม่ได้" ไม่มีปุ่มเป็นครั้งที่ 3 แล้ว (ครั้งล่าสุด `midterm-2559-1.pdf` ถูกตัดที่ max_tokens 300 · #170)
- 2026-11-19 · ปุ่มในแถว S10/S11 + แก้ AC-19 ของ `upload-page.md` เป็นงานของ May · ถ้า May ทำไม่ทันพรุ่งนี้ Claude ทำแบบ solo หลัง May อนุมัติ AC-19

## Next step

Junior review test ใน `apps/api/tests/unit/test_material_retry_api.py` และ `apps/api/tests/integration/test_material_retry_db.py` แล้วรัน `/implement-feature`

## Waiting on

- May: ตอบว่าทำปุ่ม + AC-19 ทันพรุ่งนี้ไหม

## Notes for next time

- `IngestionRunner.retry` ของ Jam รอ classify จบใน request · router จึงเรียก `runner.classify` / `runner.start` เองแทน
