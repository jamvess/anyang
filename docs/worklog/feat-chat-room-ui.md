# เริ่มหน้าแชท (ห้องติว): layout, bubble, composer

| | |
|---|---|
| Owner | May |
| Branch | `feat/chat-room-ui` |
| Checklist item | เริ่มหน้าแชท: layout, bubble ของ tutor/buddy/user, composer (พิมพ์ + ส่งรูป) |
| Status | in progress · 2026-10-19 |

## Plan

ขอบเขต S2: หน้าจอห้องติวที่แสดงข้อความจาก**ข้อมูลตัวอย่าง (fixture)** ยังไม่ต่อ API/SSE จริง (ต่อใน S3 P4-lite) · ใช้ wireframe S15–S26 เป็นแบบ

- [ ] 1. 🤖 `/spec-feature` ร่าง `specs/features/tutor-room/chat-room-ui.md` จาก TM-06, TM-08 และ wireframe S15–S26 (layout, bubble 3 แบบ, composer พิมพ์ + ส่งรูป) · ระบุชัดว่าอะไรอยู่นอกขอบเขต (SSE, เสียง, progress card, OCR preview)
- [ ] 2. 🙋 May อ่าน spec โดยเฉพาะส่วน Acceptance criteria แล้วตอบ ok หรือบอกข้อที่อยากแก้ (Claude จะถามเป็นตัวเลือก)
- [ ] 3. 🤖 `/spec-to-tests` เขียน test ที่ยัง fail จาก acceptance criteria (Vitest + Testing Library)
- [ ] 4. 🙋 May review test: อ่านชื่อ test ทีละข้อว่าตรงกับ spec (Claude สรุปเป็นภาษาไทยให้)
- [ ] 5. 🤖 `/implement-feature` เขียน component จน test ผ่าน + `pnpm lint`, `pnpm typecheck`, `pnpm test`, `pnpm build`
- [ ] 6. 🙋 May เปิดดูใน browser: รัน `pnpm dev` ใน `apps/web` แล้วเปิด URL ที่ Claude บอก เทียบกับ wireframe S15–S23

## Definition of done

- มี feature spec ที่ May approve แล้ว
- test ทุกข้อชื่อขึ้นต้นด้วย requirement ID และผ่าน
- หน้าห้องติวแสดง bubble ของ tutor / buddy / user ต่างกันชัดเจน, render สมการด้วย KaTeX, composer พิมพ์และแนบรูปได้, ไม่มีปุ่มตัวเลือกคำตอบ
- CI เขียว · Junior review PR

## Decisions

- 2026-10-19 · ใช้ type `feat` · มี requirement ID จึงทำตาม spec flow
- 2026-10-19 · ใช้ข้อมูลตัวอย่างแทน API · API ห้องติวยังไม่มี (Junior ทำใน S3) และ checklist S2 ขอแค่ layout + bubble + composer

## Next step

Claude ทำขั้น 1: `/spec-feature` สำหรับหน้าแชท

## Waiting on

ไม่มี

## Notes for next time

- May ชอบตอบการตัดสินใจเป็นตัวเลือก (AskUserQuestion) มากกว่าแก้ไฟล์เอง
