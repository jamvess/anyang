# หน้าแชทส่งรูปได้ผ่าน stub `/uploads` จนถึง verdict

| | |
|---|---|
| Owner | Jam (item of May) |
| Branch | `feat/room-photo-send` |
| Checklist item | หน้าแชท P4-lite: อ่าน SSE ผ่าน `lib/sse.ts`, แสดงข้อความที่ไหลออกมา, render KaTeX, ส่งรูป |
| Status | in progress · 2026-11-05 |

## Plan

เปิดการส่งรูปในห้องติวที่ต่อ API: Composer → `POST /sessions/{id}/uploads` → `PUT` ไฟล์ → `POST /sessions/{id}/messages` → การ์ดยืนยันลายมือ → `POST /sessions/{id}/ocr/confirm` → verdict · ทำได้บางส่วน เพราะ `/uploads` ตัวจริงที่ต่อ Storage รอ Junior

- [x] 1. 🤖 `/spec-feature`: ร่าง `specs/features/tutor/room-photo-send.md` จาก TM-06, TM-21, AM-01, AM-02 · แก้ข้อความเก่าใน `room-http.md`
- [x] 2. 🙋 Jam อ่าน spec และตัดสิน 2 ข้อ (test ที่ขัดกับการตัดสิน PR #45 · วิธี `PUT` กับ stub) · บอกแชทกลุ่มถ้าแก้ `api.md`
- [x] 3. 🤖 `/spec-to-tests`: test ฝั่งเว็บและ API · แดงก่อน
- [x] 4. 🙋 Jam review test
- [x] 5. 🤖 `/implement-feature`: API รับข้อความพร้อมรูป + `PUT` ของ stub · เว็บ `transport`, `TutorRoom` · test เขียว
- [x] 6. 🙋 Jam ลองในเบราว์เซอร์ตามขั้นตอนที่ให้ (ส่งรูป → การ์ด → ยืนยัน → verdict)
- [x] 7. 🤖 `api-schema.ts` ถ้าเปลี่ยน + บรรทัดความคืบหน้าใน checklist

## Definition of done

- ในห้องติวที่ต่อ API เลือกรูป ส่ง เห็นการ์ดยืนยันลายมือ กดยืนยัน แล้วเห็น verdict
- ข้อผิดพลาดทุกแบบมีข้อความไทย (ชนิดไฟล์, ขนาด, `PUT` ล้ม, rate limit) และไม่เสียรูปหรือข้อความที่พิมพ์ไว้ตามที่ spec กำหนด
- test + lint + CI เขียว · ลองในเบราว์เซอร์ผ่าน
- ข้อ "หน้าแชท P4-lite" ยังไม่ติ๊ก (เหลือ `/uploads` จริง และทดสอบบน staging กับ AI จริง)

## Decisions

- 2026-11-05 · การส่งข้อความพร้อมรูปตัดสินแล้ว (Jam 2026-10-21 · PR #45 · api.md "รอตัดสิน (PR #35)" ข้อ 1) · `room-http.md` ยังเขียนว่ารอ Jam เพราะไม่ได้แก้ตาม

## Next step

ทุกขั้นเสร็จ · `/work-done`

## Waiting on

- Junior: `/uploads` ตัวจริงที่ต่อ Supabase Storage (bucket + policy · api.md รอตัดสิน v1.7 ข้อ 2)

## Notes for next time

- `apps/api/app/models/room.py` `SendMessageRequest` รับได้ทีละอย่าง ขัดกับ api.md แถว `POST /sessions/{id}/messages` · test ที่ review แล้ว (`test_apimd_room_send_message_needs_exactly_one_of_text_or_image`) มี comment ว่าให้แก้พร้อม spec ถ้า Jam อนุญาต
- `upload_url` ของ stub คือ `https://stub.invalid/storage/...` browser `PUT` ไปไม่ได้
- `TutorRoom` ยังไม่ส่ง `confirmOcr` ให้ `ChatRoom` (`createHttpOcrConfirm` มีแล้ว) และ `imagesEnabled={false}`
- Vitest timeout เมื่อ Docker เปิดอยู่ · ใช้ `--testTimeout=30000` เช็คว่าเป็น load หรือของจริง
