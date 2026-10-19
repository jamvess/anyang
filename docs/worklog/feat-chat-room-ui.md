# เริ่มหน้าแชท (ห้องติว): layout, bubble, composer

| | |
|---|---|
| Owner | May |
| Branch | `feat/chat-room-ui` |
| Checklist item | เริ่มหน้าแชท: layout, bubble ของ tutor/buddy/user, composer (พิมพ์ + ส่งรูป) |
| Status | in progress · 2026-10-19 |

## Plan

ขอบเขต S2: หน้าจอห้องติวที่แสดงข้อความจาก**ข้อมูลตัวอย่าง (fixture)** ยังไม่ต่อ API/SSE จริง (ต่อใน S3 P4-lite) · ใช้ wireframe S15–S26 เป็นแบบ

- [x] 1. 🤖 `/spec-feature` ร่าง `specs/features/tutor/chat-room-ui.md` จาก TM-06, TM-08 และ wireframe S15–S26 (layout, bubble 3 แบบ, composer พิมพ์ + ส่งรูป) · ระบุชัดว่าอะไรอยู่นอกขอบเขต (SSE, เสียง, progress card, OCR preview) · 2026-10-19 ร่างแล้ว 20 AC + 2 boundary, open questions 7 ข้อ
- [x] 2. 🙋 May อ่าน spec โดยเฉพาะส่วน Acceptance criteria แล้วตอบ ok หรือบอกข้อที่อยากแก้ (Claude จะถามเป็นตัวเลือก) · 2026-10-19 May approve จากสรุป 13 ข้อในแชท
- [x] 3. 🤖 `/spec-to-tests` เขียน test ที่ยัง fail จาก acceptance criteria (Vitest + Testing Library) · 2026-10-19 เขียน 4 ไฟล์ใน `apps/web/tests/chat/` + fixture `tests/fixtures/room/session-s15.json` · fail ทุกไฟล์เพราะยังไม่มี component (ถูกเหตุผล) · test เดิม 2 ไฟล์ยังผ่าน
- [x] 4. 🙋 May review test: อ่านชื่อ test ทีละข้อว่าตรงกับ spec (Claude สรุปเป็นภาษาไทยให้) · 2026-10-19 May approve 36 test (หลังแก้ AC-18 และ avatar)
- [ ] 5. 🤖 `/implement-feature` เขียน component จน test ผ่าน + `pnpm lint`, `pnpm typecheck`, `pnpm test`, `pnpm build`
- [ ] 6. 🙋 May เปิดดูใน browser: รัน `pnpm dev` ใน `apps/web` แล้วเปิด URL ที่ Claude บอก เทียบกับ wireframe S15–S23

## Definition of done

- มี feature spec ที่ May approve แล้ว
- test ทุกข้อชื่อขึ้นต้นด้วย requirement ID และผ่าน
- หน้าห้องติวแสดง bubble ของ tutor / buddy / user ต่างกันชัดเจน, render สมการด้วย KaTeX, composer พิมพ์และแนบรูปได้, ไม่มีปุ่มตัวเลือกคำตอบ
- CI เขียว · Junior review PR

## Decisions

- 2026-10-19 · ใช้ type `feat` · มี requirement ID จึงทำตาม spec flow
- 2026-10-19 · May ตอนดู test: ไฟล์ที่ไม่ใช่รูปต้องขึ้นข้อความ "แนบได้เฉพาะรูป" (เดิมเงียบ) · avatar ใช้อักษรย่อแบบ wireframe (ตัดคำนำหน้า พี่/น้อง/ครู + ข้ามสระหน้า) → พี่ตาล = ต · เพิ่ม `user_name` ใน RoomData สำหรับ avatar ของ user · แก้ spec + test แล้ว
- 2026-10-19 · test อยู่ที่ `apps/web/tests/chat/` ไม่ได้วางข้าง component · `vitest.config.mts` หา test เฉพาะ `tests/**` และ `apps/web/CLAUDE.md` กำหนดแบบนี้
- 2026-10-19 · spec อยู่ที่ `specs/features/tutor/` (ไม่ใช่ `tutor-room/`) · ให้ตรงกับค่า Area ใน `_TEMPLATE.md`
- 2026-10-19 · May ตอบ open questions: Enter = ส่ง · ส่งรูปพร้อมข้อความได้ (ต้องแก้ api.md) · สมการ `$…$`/`$$…$$` · ค่าขีดจำกัดมากับข้อมูลห้องจาก API (S2 ใช้ fixture) · ข้อเสนอแก้ api.md อยู่ใน spec ข้อ 11 ต้องให้ Junior/Jam อนุมัติ
- 2026-10-19 · ใช้ข้อมูลตัวอย่างแทน API · API ห้องติวยังไม่มี (Junior ทำใน S3) และ checklist S2 ขอแค่ layout + bubble + composer

## Next step

Claude ทำขั้น 5: `/implement-feature` ให้ test ใน `apps/web/tests/chat/` ผ่าน (ห้ามแก้ test ที่ May review แล้ว)

## Waiting on

ไม่มี

## Notes for next time

- May ชอบตอบการตัดสินใจเป็นตัวเลือก (AskUserQuestion) มากกว่าแก้ไฟล์เอง
