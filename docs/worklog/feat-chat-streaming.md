# หน้าแชท P4-lite · stream ข้อความจาก SSE

| | |
|---|---|
| Owner | May |
| Branch | `feat/chat-streaming` |
| Checklist item | หน้าแชท P4-lite: อ่าน SSE ผ่าน `lib/sse.ts`, แสดงข้อความที่ไหลออกมา, render KaTeX, ส่งรูป |
| Status | in progress · 2026-10-20 |

## Plan

- [x] 1. 🤖 `/spec-feature` ร่าง `specs/features/tutor/chat-streaming.md` (TM-20, TM-08, TM-06, TM-21): ChatRoom ส่งข้อความผ่าน transport ที่ inject ได้, event `token` ต่อท้าย bubble ของ `speaker` ทีละส่วน, จัดการ `done` / `error`, ส่งรูป · ใช้ fake transport ที่เล่น `tests/fixtures/sse/*.txt` จนกว่า endpoint ของ Junior จะมา
- [x] 2. 🙋 May review spec และตอบ open questions (Claude ถามเป็นตัวเลือก) · บอก Junior ในกลุ่มเรื่อง api.md ที่ต้องแก้
- [ ] 3. 🤖 `/spec-to-tests` เขียน test ที่ fail จาก AC + เปลี่ยนชื่อ test เดิม TM04/TM05 → TM20/TM21 ตามที่ `chat-room-ui.md` §10 ข้อ 1 ตกลงไว้
- [ ] 4. 🙋 May review test (ชื่อใหม่ + test ใหม่)
- [ ] 5. 🤖 `/implement-feature` จน test ผ่าน + lint + typecheck
- [ ] 6. 🙋 May ลองในเบราว์เซอร์: `cd apps/web` → `pnpm dev` → เปิด `http://localhost:3000/preps/demo/room` → พิมพ์ข้อความแล้วกด Enter → ดูว่าตัวอักษรไหลออกมาทีละส่วนและสมการ render ถูก

## Definition of done

- Spec `chat-streaming.md` approved by May และส่ง Junior review ใน PR
- Test จาก AC ผ่านทั้งหมด (`pnpm test`), `pnpm lint` และ `pnpm typecheck` ผ่าน
- หน้า room เห็นข้อความ tutor ไหลออกมาจาก fake stream และ KaTeX render ถูก
- ยังไม่รวม: ต่อ staging จริง + วัด TTFT (ต้องรอ endpoint `POST /sessions/{id}/messages` ของ Junior · ทำใน branch ถัดไป)

## Decisions

- 2026-10-20 · ทำกับ fake stream ก่อน · backend ยังมีแค่ `/health` และ `gen:api` ยังไม่มี type ห้องติวให้ใช้
- 2026-10-20 · ระหว่างกำลังตอบ พิมพ์ร่างได้แต่ส่งไม่ได้ · backend ประกอบ context ใหม่ทุก turn ส่งซ้อนจะได้คำตอบสลับกัน (May)
- 2026-10-20 · ก่อน token แรกแสดง bubble tutor จุดสามจุด · ช่วง TTFT ยาวได้ถึง 2 วินาที (May)
- 2026-10-20 · ผิดพลาดแสดง "ส่งไม่สำเร็จ ลองส่งอีกทีนะ" ข้อความเดียวเหนือ composer ไม่แสดง message จาก server · ยังไม่มีรายการ error.code (May)
- 2026-10-20 · `$` ที่ยังไม่ปิดระหว่าง stream ซ่อนไว้ แสดงทั้งหมดเมื่อจบ · ไม่ให้เห็น LaTeX ดิบกระพริบ แต่ไม่ทำให้ข้อความหาย (May)
- 2026-10-20 · เลื่อนจอตาม stream ทำในงานนี้ เฉพาะเมื่ออยู่ใกล้ล่างสุด · stream ยาวจะล้นจอตอน demo (May)

## Next step

รัน `/spec-to-tests specs/features/tutor/chat-streaming.md` (spec approved by May 2026-10-20)

## Waiting on

- Junior: api.md ยังเขียน `{text}` หรือ `{image_path}` อย่างใดอย่างหนึ่ง และยังไม่มี `limits` ในข้อมูลห้อง (`chat-room-ui.md` §11) · ต้องตกลงก่อนต่อ API จริง

## Notes for next time

- `pnpm gen:api` มีอยู่แล้ว รอ router D5 ของ Junior แล้วค่อยรันใหม่
