# ต่อหน้าห้องติวเข้ากับ API (HTTP transport · P4-lite)

| | |
|---|---|
| Owner | May |
| Branch | `feat/room-http-transport` |
| Checklist item | หน้าแชท P4-lite: อ่าน SSE ผ่าน `lib/sse.ts`, แสดงข้อความที่ไหลออกมา, render KaTeX, ส่งรูป |
| Status | in progress · 2026-10-21 |

## Plan

- [ ] 1. 🤖 `/spec-feature`: เขียน `specs/features/tutor/room-http.md` (TM-20, TM-13, TM-06, TM-21) · หน้าห้องหา session ด้วย `GET /exam-preps/{id}/sessions/active` → `GET /sessions/{id}` หรือ `POST /exam-preps/{id}/sessions` · ส่งข้อความด้วย `POST /sessions/{id}/messages` (SSE) · ใช้ type จาก `lib/api-schema.ts`
- [ ] 2. 🙋 May review spec และตัดสินเรื่องที่ยังไม่ชัด (Claude ถามเป็นตัวเลือก)
- [ ] 3. 🤖 `/spec-to-tests`: เขียน test ที่ fail จาก acceptance criteria
- [ ] 4. 🙋 May review test
- [ ] 5. 🤖 `/implement-feature`: เขียนโค้ดจน test ผ่าน + lint, typecheck, build
- [ ] 6. 🙋 May ลองจริงในเครื่อง: เปิด API + web แล้วคุยในห้องติว เห็นข้อความไหลจาก stub (Claude ให้ขั้นตอนทีละคลิก)

## Definition of done

- หน้าห้องติวเปิดได้จาก API stub (กลับเข้า session เดิม หรือสร้างใหม่) และส่งข้อความแล้วเห็นคำตอบ stream จาก `POST /sessions/{id}/messages`
- test จาก acceptance criteria ผ่าน และ lint, typecheck, test, build ของ web ผ่าน
- ไม่ติ๊ก checklist ทั้งข้อ (ยังเหลือส่งรูปจริงเมื่อมี `/uploads` และทดสอบบน staging) · เพิ่ม sub-bullet ว่าทำส่วนไหนแล้ว

## Decisions

## Next step

ขั้น 1: `/spec-feature` สำหรับ `specs/features/tutor/room-http.md`

## Waiting on

ไม่มี

## Notes for next time

- รูปยังส่งไม่ได้: ไม่มี stub `POST /sessions/{id}/uploads` และ api.md "รอตัดสิน" ข้อ 1 (Jam)
