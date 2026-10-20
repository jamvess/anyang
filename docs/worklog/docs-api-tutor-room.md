# API contract ของห้องติว (D5) · spec ก่อน stub

| | |
|---|---|
| Owner | Junior |
| Branch | `docs/api-tutor-room` |
| Checklist item | เขียน router หัวฟังก์ชันของทุก API ใน `specs/system/api.md` ให้หน้า `/docs` ครบ (D5) |
| Status | paused · 2026-10-20 · รอ May + Jam review PR #35 |

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

## Done today

- 2026-10-20 · เทียบ api.md กับโค้ดห้องติวของ May แล้วพบ 11 จุดที่ไม่ตรงกัน · ร่างการแก้ api.md 2 รอบตามที่ Junior สั่ง
- 2026-10-20 · api.md v1.2 commit แล้ว: `Room` / `Message`, `GET /sessions/{id}`, `GET /exam-preps/{id}/sessions/active`, event `session`, กฎ degrade · คำถามเปิด 6 ข้อในหัวข้อ "รอตัดสิน"
- 2026-10-20 · PR #35 ready for review · ขอ review จาก May (`@jantarat32443`) + Jam (`@jamvess`) · PR description มีรายการสิ่งที่ May ต้องแก้ใน fixture/types

## Next step

รัน `gh pr view 35 --comments` และ `gh pr view 35 --json reviewDecision,reviews` · ถ้ามีคอมเมนต์ แก้ `specs/system/api.md` บน branch นี้แล้ว push · ถ้า merge แล้ว เริ่มขั้น 6: branch ใหม่ `feat/room-api-stubs` จาก `main` แล้ว stub 4 endpoint (`GET /exam-preps/{id}/sessions/active`, `POST /exam-preps/{id}/sessions`, `GET /sessions/{id}`, `POST /sessions/{id}/messages`) ตาม api.md v1.2

## Waiting on

- 🙋 May: review รูปร่าง `Room` / `Message` + ตอบ "รอตัดสิน" ข้อ 3, 5, 6 · อัปเดต fixture (`session_id`, `card`)
- 🙋 Jam: ตัดสิน "รอตัดสิน" ข้อ 1 (ข้อความกำกับรูปใน flow OCR)

## Notes for next time

- `ai-orchestration.md` (Jam เป็นเจ้าของ) บรรทัด 383 เขียน body `{text}` หรือ `{image_path}` เหมือน api.md เดิม · ต้องให้ Jam แก้ให้ตรงกัน
- ข้อ 1 ของ "รอตัดสิน" (`{text, image_path}`) ห้ามใส่ใน stub จนกว่า Jam จะตัดสิน · stub ตอนนี้ต้องใช้ body แบบเดิม `{text}` หรือ `{image_path}`
- รายการ `error.code` (ข้อ 4) เป็นงานของ Junior · ต้องตอบก่อนทำ `POST /sessions/{id}/messages` จริง
- ร่างที่ใช้ทำงานอยู่ใน scratchpad ของ session นี้ ไม่ต้องใช้แล้ว เพราะเนื้อหาอยู่ใน api.md บน branch นี้ครบ
