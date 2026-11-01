# Contract + stub ของ uploads, transcribe, ocr/confirm (D5 · ส่วนที่ 2)

| | |
|---|---|
| Owner | Jam (item of Junior) |
| Branch | `feat/room-media-stubs` |
| Checklist item | เขียน router หัวฟังก์ชันของทุก API ใน `specs/system/api.md` ให้หน้า `/docs` ครบ (D5) |
| Status | in progress · 2026-11-01 |

## Plan

3 endpoint ของห้องติวที่งานรูปและเสียงของ May รออยู่ (`room-http.md`, `chat-streaming.md` §11, `voice-input.md` OQ 6, `ocr-confirm-card.md` OQ 5–6) + schema ของ event `ocr_preview` และ `verdict` ใน OpenAPI

- [ ] 1. 🤖 ร่าง contract (ข้อเสนอรอ Junior): `POST /sessions/{id}/uploads`, `POST /sessions/{id}/transcribe`, `POST /sessions/{id}/ocr/confirm` + payload ของ `ocr_preview` / `verdict` · ใช้ข้อเสนอของ May เป็นหลัก · ค่าจำกัดอ่านจาก `config/ai.yaml` → `guards`
- [ ] 2. 🙋 Jam อ่านร่าง ตอบ ok · ส่งข้อความในแชทกลุ่มว่าจะแก้ `api.md` (ไฟล์ร่วม)
- [ ] 3. 🤖 ใส่ร่างลง `api.md` v1.7 + "รอตัดสิน (v1.7 · Junior)"
- [ ] 4. 🤖 test contract + stub (`test_apimd_room_media_…` / requirement ID สำหรับพฤติกรรม) · แดงก่อน
- [ ] 5. 🙋 Jam review test
- [ ] 6. 🤖 models + stub 3 endpoint (`X-Stub: true`) · `OcrPreviewEvent`, `VerdictEvent` ใน `EVENT_MODELS` · ข้อความรูปใน stub stream `ocr_preview` · test เขียว + ruff
- [ ] 7. 🤖 `pnpm gen:api` (ลง `apps/web/lib/api-schema.ts`) + บรรทัดความคืบหน้าใน checklist

## Definition of done

- `api.md` มี request/response/error ของ 3 endpoint และ payload ของ `ocr_preview` / `verdict` · ข้อที่ยังไม่ตัดสินอยู่ใน "รอตัดสิน (v1.7 · Junior)"
- `/docs` แสดง 3 endpoint + schema ของ event ทั้งสอง · stub ส่ง `X-Stub: true`
- test + ruff + CI เขียว · ข้อ D5 ยังไม่ติ๊ก (เหลือกลุ่มอื่น)

## Decisions

- 2026-11-01 · stub ของ `/uploads` คืน `upload_url` ที่ไม่ใช่ URL จริงของ Storage · PUT จริงยังทำไม่ได้จนกว่าจะเขียน endpoint จริงที่ต่อ Supabase Storage (ต้องมี service role / RLS ของ bucket · เรื่องของ Junior)
- 2026-11-01 · ไม่ทำในรอบนี้: `input_mode: "voice"` ใน `SendMessageRequest` (voice-input OQ 7) และ body `{text, image_path}` พร้อมกัน (api.md v1.3 ยอมแล้ว แต่ test ที่ review แล้วยังบังคับอย่างใดอย่างหนึ่ง · ต้องให้คน review อนุญาตแก้ test ก่อน)

## Next step

ขั้น 1: ร่าง contract

## Waiting on

- Junior: ตัดสิน contract (รอตัดสิน v1.7) · ทำ `/uploads` จริงที่ต่อ Storage
- May: `pnpm gen:api` แล้วต่อ HTTP transport ของรูป/เสียง/OCR

## Notes for next time

- แบบของ stub: `app/routers/scope.py` (PR #100), `app/routers/room.py`
