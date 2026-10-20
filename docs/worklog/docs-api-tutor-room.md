# API contract ของห้องติว (D5) · spec ก่อน stub

| | |
|---|---|
| Owner | Junior |
| Branch | `docs/api-tutor-room` |
| Checklist item | เขียน router หัวฟังก์ชันของทุก API ใน `specs/system/api.md` ให้หน้า `/docs` ครบ (D5) |
| Status | in progress · 2026-10-20 · May ขอให้ทำก่อน (ใช้ต่อ HTTP transport ของห้องติว) |

## Plan

- [x] 1. 🤖 อ่าน api.md "ห้องติว" + "SSE events" และโค้ดของ May (`components/chat/types.ts`, `tests/fixtures/room/`, `tests/fixtures/sse/`) · สรุป endpoint ที่ห้องติวต้องใช้ก่อน และจุดที่ spec ไม่ตรงกับ UI
- [ ] 2. 🤖 ร่างการแก้ api.md: `limits` ในข้อมูลห้อง + endpoint ที่ส่ง · เรื่องรูปแบบสมการใน `content` เป็น open question ให้ May
- [ ] 3. 🙋 Junior อ่านร่าง ตอบ ok · บอกแชทกลุ่มว่าจะแก้ api.md (ไฟล์ร่วม)
- [ ] 4. 🤖 ใส่ร่างลง `specs/system/api.md` · เปลี่ยน PR เป็น ready for review · ขอ review จาก May + Jam
- [ ] 5. 🙋 May + Jam review และตอบ open questions · merge
- [ ] 6. 🤖 (branch ใหม่หลัง merge) stub router 4 endpoint แรกของห้องติว ให้ขึ้นใน `/docs`

## Definition of done

- api.md มี response ของข้อมูลห้อง (รวม `limits`) และ body ของ `POST /sessions/{id}/messages` ตรงกับที่ UI ส่ง
- mismatch ทุกข้อมีคำตอบหรืออยู่ใน open questions ของ PR
- May + Jam approve PR ของ spec · ยังไม่มีโค้ด router ใน PR นี้

## Decisions

- 2026-10-20 · spec แยก PR จาก stub · ให้ May + Jam review contract ก่อนเขียนโค้ด

## Next step

รอ Junior ตอบ ok กับร่าง api.md ในแชท แล้วทำขั้น 4

## Waiting on

- 🙋 Junior: review ร่าง api.md

## Notes for next time

- `ai-orchestration.md` (Jam เป็นเจ้าของ) บรรทัด 383 เขียน body `{text}` หรือ `{image_path}` เหมือน api.md เดิม · ต้องให้ Jam แก้ให้ตรงกัน
