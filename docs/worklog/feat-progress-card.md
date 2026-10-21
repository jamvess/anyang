# ห้องติว · การ์ดความคืบหน้า (TM-15, TM-11)

| | |
|---|---|
| Owner | May |
| Branch | `feat/progress-card` |
| Checklist item | ไม่มีข้อตรงใน checklist · ส่วนหนึ่งของหน้าห้องติว (S15) ที่ demo ช่วง 3 ใช้ (`docs/design/demo-flow.md`) · stub ส่ง event `progress_card` แล้วแต่หน้าเว็บยังไม่แสดง |
| Status | in progress · 2026-10-21 |

## Plan

- [x] 1. 🤖 `/spec-feature`: `specs/features/tutor/progress-card.md` (TM-15, TM-11, PM-03, PM-04) · แสดง event `progress_card` และข้อความ role `card` ในประวัติ ตาม wireframe S15 และ api.md · 🙋 May ตัดสินเรื่องที่ spec ยังไม่กำหนด
- [x] 2. 🙋 May review spec (รวมการเปลี่ยน chat-room-ui AC-4 ที่ตอนนี้ซ่อน role `card`)
- [ ] 3. 🤖 `/spec-to-tests`
- [ ] 4. 🙋 May review test
- [ ] 5. 🤖 `/implement-feature` + lint, typecheck, test, build

## Definition of done

- เปิดห้องแล้วเห็นการ์ด (หัวข้อ ดาว ระดับ ความพร้อม %) จาก event `progress_card` · ย้อนดูประวัติเห็นการ์ดเดิมจาก `messages` role `card` · ตัวเลขทุกตัวมาจาก API ไม่คำนวณในหน้าเว็บ (apps/web/CLAUDE.md)
- test ผ่าน · lint, typecheck, build ผ่าน

## Decisions

- 2026-10-21 · หัวข้อเกิน 6 แสดง 6 + ปุ่ม "อีก n หัวข้อ" · `review_due` และ `origin = user` เป็นป้ายเล็กข้างชื่อ (May เลือก)

## Next step

ขั้น 3: `/spec-to-tests specs/features/tutor/progress-card.md`

## Waiting on

ไม่มี

## Notes for next time

- payload: api.md "SSE events" `progress_card {days_left, passed, total, readiness, topics: [{id, name, stars, level, review_due, origin}]}` · ระดับ 4 ขั้น: ai-orchestration §2.2.2 · stub: `apps/api/app/stubs/session_start.sse`
