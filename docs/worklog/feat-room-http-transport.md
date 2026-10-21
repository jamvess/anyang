# ต่อหน้าห้องติวเข้ากับ API (HTTP transport · P4-lite)

| | |
|---|---|
| Owner | May |
| Branch | `feat/room-http-transport` |
| Checklist item | หน้าแชท P4-lite: อ่าน SSE ผ่าน `lib/sse.ts`, แสดงข้อความที่ไหลออกมา, render KaTeX, ส่งรูป |
| Status | in progress · 2026-10-21 |

## Plan

- [x] 1. 🤖 `/spec-feature`: เขียน `specs/features/tutor/room-http.md` (TM-20, TM-13, TM-06, TM-21) · หน้าห้องหา session ด้วย `GET /exam-preps/{id}/sessions/active` → `GET /sessions/{id}` หรือ `POST /exam-preps/{id}/sessions` · ส่งข้อความด้วย `POST /sessions/{id}/messages` (SSE) · ใช้ type จาก `lib/api-schema.ts`
- [x] 2. 🙋 May review spec และตัดสินเรื่องที่ยังไม่ชัด (Claude ถามเป็นตัวเลือก)
- [x] 3. 🤖 `/spec-to-tests`: เขียน test ที่ fail จาก acceptance criteria
- [x] 4. 🙋 May review test
- [x] 5. 🤖 `/implement-feature`: เขียนโค้ดจน test ผ่าน + lint, typecheck, build
- [ ] 6. 🙋 May ลองจริงในเครื่อง: เปิด API + web แล้วคุยในห้องติว เห็นข้อความไหลจาก stub (Claude ให้ขั้นตอนทีละคลิก)
- [x] 7. 🤖 spec: `chat-room-ui.md` เพิ่ม AC-6b ชื่อไฟล์รูปมาจาก `attachment_name` (api.md v1.3 · PR #43) · ถ้าเป็น null ใช้ท้าย `attachment_path` ตามเดิม (AC-6 เดิมผ่านโดยไม่แก้) · 🙋 May review
- [x] 8. 🤖 test ใหม่ใน `MessageList.test.tsx` + `ChatRoomStream`/`RoomPageHttp` ถ้าจำเป็น · 🙋 May review
- [x] 9. 🤖 implement `MessageList.tsx` + ข้อความในเครื่องของ ChatRoom ใช้ `attachment_name`

## Definition of done

- หน้าห้องติวเปิดได้จาก API stub (กลับเข้า session เดิม หรือสร้างใหม่) และส่งข้อความแล้วเห็นคำตอบ stream จาก `POST /sessions/{id}/messages`
- test จาก acceptance criteria ผ่าน และ lint, typecheck, test, build ของ web ผ่าน
- ไม่ติ๊ก checklist ทั้งข้อ (ยังเหลือส่งรูปจริงเมื่อมี `/uploads` และทดสอบบน staging) · เพิ่ม sub-bullet ว่าทำส่วนไหนแล้ว

## Done today (2026-10-21)

- (รอบ 2) merge main (PR #43, #46, #48) ไม่มี conflict · ขั้น 7–9: กล่องรูปใช้ `attachment_name` (chat-room-ui.md AC-6b, AC-6c) · test 103/103

- spec `specs/features/tutor/room-http.md` · May ตัดสิน 4 เรื่อง และ approve
- test จาก AC (23 ตัวใหม่) · May review · แก้ test helper 2 จุดที่ May อนุมัติ
- โค้ด: `lib/httpTransport.ts`, `components/chat/TutorRoom.tsx`, prop `opening` ใน ChatRoom, `imagesEnabled` ใน Composer, page.tsx ใช้ API · ลบ DemoRoom
- lint (0 error), typecheck, test 91/91, build ผ่าน

## Decisions

- 2026-10-21 · spec room-http.md: May ตัดสิน 4 เรื่อง (ข้อความเปิดไหลเข้าห้อง, โหลดไม่สำเร็จมีลองใหม่ + กลับหน้าหลัก, ปุ่มแนบรูปกดได้แต่แจ้งว่ายังส่งไม่ได้, ลบโหมด demo)
- 2026-10-21 · May อนุมัติ spec และให้เลิกใช้ test "Room page (S3, fake transport)" (chat-streaming.md AC-21) ใน RoomPage.test.tsx · แทนด้วย AC-6 ใน RoomPageHttp.test.tsx

- 2026-10-21 · implement: May อนุมัติแก้ test helper 2 จุด (`new Response(text)` แทน `Blob.stream()` ที่ jsdom ไม่มี · ใช้ข้อความ 2–4 ของ fixture เพราะข้อความแรกเป็น card ไม่มี bubble) · ไม่เปลี่ยนสิ่งที่ test ตรวจ
- 2026-10-21 · implement: `ChatMessage.card` ไม่บังคับ และ `RoomData.messages` เป็น `ChatMessage[]` เพื่อให้ test เดิมที่ review แล้ว typecheck ผ่านโดยไม่แก้ · บันทึกใน spec §2 แล้ว
- 2026-10-21 · page.tsx อ่าน `params` ใน `<Suspense>` เพราะ Next 16 ไม่ให้ prerender อ่าน request data นอก Suspense
- red → green: 3 รอบ (transport + Composer · TutorRoom + opening ของ ChatRoom · หลังแก้ test helper) + แก้ lint/typecheck/build อีก 3 รอบ
- 2026-10-21 · merge main (PR #43 attachment_name): `ChatMessage.attachment_name` ไม่บังคับเหมือน `card` เพื่อให้ test เดิมที่ review แล้ว typecheck ผ่าน
- 2026-10-21 · ขั้น 9: MessageList ใช้ `attachment_name` ก่อน ถ้า null ใช้ท้าย `attachment_path` · ChatRoom สร้างข้อความรูปด้วย `attachment_name` · red → green 1 รอบ · test 103/103, lint 0 error, typecheck, build ผ่าน

## Next step

ขั้น 6: เมื่อ Junior เพิ่ม CORS ใน FastAPI แล้ว merge main เข้ามา · ตั้ง `NEXT_PUBLIC_API_URL=http://localhost:8000` ใน `apps/web/.env.local` (🙋 May) · เปิด API (`uv run uvicorn app.main:app --port 8000` ใน apps/api) + web (`pnpm dev`) · May เปิด `http://localhost:3000/preps/11111111-1111-4111-8111-111111111111/room` แล้วส่งข้อความ ดูคำตอบไหลจาก stub

## Waiting on

ไม่มี · CORS merge แล้ว (PR #49) · OQ 5–7 Junior ตอบแล้ว

## Notes for next time

- CORS: `apps/api/app/cors.py` (PR #49) · ค่าเริ่มต้นอนุญาต `http://localhost:3000` ไม่ต้องแก้ `.env` ของ API
- ต้องตั้ง `NEXT_PUBLIC_API_URL=http://localhost:8000` ใน `apps/web/.env.local` ก่อนลองจริง (🙋 May ตั้งเอง · Claude ห้ามอ่าน .env)
- stub ตรวจว่า path param เป็น uuid · ใช้ uuid จริงใน URL เช่น `/preps/11111111-1111-4111-8111-111111111111/room`
- jsdom ไม่มี `Blob.stream()` · ใน test ใช้ `new Response(text)` สร้าง stream
- lint warning 2 ตัว (`_` ใน httpTransport.test.ts) เป็นของ test ที่ review แล้ว ไม่ใช่ error
- Bash heredoc บนเครื่องนี้ตัด `\\` เหลือ `\` · ไฟล์หรือ PR body ที่มี backslash หลายตัวให้เขียนด้วย Edit/Write tool แล้วเช็กผล

- รูปยังส่งไม่ได้: ไม่มี stub `POST /sessions/{id}/uploads` และ api.md "รอตัดสิน" ข้อ 1 (Jam)
