# API contract ของห้องติว (D5) · spec ก่อน stub

| | |
|---|---|
| Owner | Junior |
| Branch | `docs/api-tutor-room` |
| Checklist item | เขียน router หัวฟังก์ชันของทุก API ใน `specs/system/api.md` ให้หน้า `/docs` ครบ (D5) |
| Status | in progress · 2026-10-20 · May ขอให้ทำก่อน (ใช้ต่อ HTTP transport ของห้องติว) |

## Plan

- [x] 1. 🤖 อ่าน api.md "ห้องติว" + "SSE events" และโค้ดของ May (`components/chat/types.ts`, `tests/fixtures/room/`, `tests/fixtures/sse/`) · สรุป endpoint ที่ห้องติวต้องใช้ก่อน และจุดที่ spec ไม่ตรงกับ UI
- [x] 2. 🤖 ร่างการแก้ api.md: `limits` ในข้อมูลห้อง + endpoint ที่ส่ง · เรื่องรูปแบบสมการใน `content` เป็น open question ให้ May
- [x] 3. 🙋 Junior อ่านร่าง ตอบ ok · บอกแชทกลุ่มว่าจะแก้ api.md (ไฟล์ร่วม)
- [x] 4. 🤖 ใส่ร่างลง `specs/system/api.md` · เปลี่ยน PR เป็น ready for review · ขอ review จาก May + Jam
- [ ] 5. 🙋 May + Jam review และตอบ open questions · merge
- [ ] 6. 🤖 (branch ใหม่หลัง merge) stub router 4 endpoint แรกของห้องติว ให้ขึ้นใน `/docs`

## Definition of done

- api.md มี response ของข้อมูลห้อง (รวม `limits`) และ body ของ `POST /sessions/{id}/messages` ตรงกับที่ UI ส่ง
- mismatch ทุกข้อมีคำตอบหรืออยู่ใน open questions ของ PR
- May + Jam approve PR ของ spec · ยังไม่มีโค้ด router ใน PR นี้

## Decisions

- 2026-10-20 · spec แยก PR จาก stub · ให้ May + Jam review contract ก่อนเขียนโค้ด
- 2026-10-20 · ข้อมูลห้องอยู่ที่ `GET /sessions/{id}` (`Room` รวม `limits` + `messages`) · `GET /sessions/{id}/messages` คืนแค่รายการข้อความ · ตอนกลับมาต่อ (TM-13) ต้องมี `limits` ด้วย และ POST เรียกซ้ำไม่ได้
- 2026-10-20 · หา session ที่เปิดอยู่ด้วย `GET /exam-preps/{id}/sessions/active` (404 ถ้าไม่มี) แทนให้ POST คืน session เดิม · GET ไม่เรียก AI และ POST มีความหมายเดียว
- 2026-10-20 · ข้อความ degrade ของ tutor ส่งเป็น `token` แล้ว `done` · ส่ง `error` เฉพาะเมื่อไม่มีอะไรให้แสดง (ai-orchestration.md §2.10)
- 2026-10-20 · body `{text, image_path}` เป็นแค่ข้อเสนอ รอ Jam ตัดสิน · กระทบ flow OCR · ไม่แก้ ai-orchestration.md ใน PR นี้
- 2026-10-20 · คำถามเปิดทุกข้อเขียนไว้ใน api.md "รอตัดสิน" ข้อ 1–6 ไม่เขียนแค่ใน PR description (หายหลัง merge) · api.md เปลี่ยนเป็น v1.2

## Next step

รอ May + Jam review PR #35 · ถ้ามีคอมเมนต์ แก้ใน api.md บน branch นี้ · หลัง merge เริ่มขั้น 6 ใน branch ใหม่

## Waiting on

- 🙋 May: review รูปร่าง `Room` / `Message` + ตอบ "รอตัดสิน" ข้อ 3, 5, 6 · อัปเดต fixture (`session_id`, `card`)
- 🙋 Jam: ตัดสิน "รอตัดสิน" ข้อ 1 (ข้อความกำกับรูปใน flow OCR)

## Notes for next time

- `ai-orchestration.md` (Jam เป็นเจ้าของ) บรรทัด 383 เขียน body `{text}` หรือ `{image_path}` เหมือน api.md เดิม · ต้องให้ Jam แก้ให้ตรงกัน
