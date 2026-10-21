# ห้องติว · การ์ดโจทย์ (event `problem`)

| | |
|---|---|
| Owner | May |
| Branch | `feat/problem-card` |
| Checklist item | ไม่มีข้อตรงใน checklist · ส่วนหนึ่งของหน้าห้องติว (S15) ที่ demo ช่วง 3 ใช้ (`docs/design/demo-flow.md`) · stub ส่ง event `problem` แล้วแต่หน้าเว็บยังไม่แสดง |
| Status | in progress · 2026-10-21 |

## Plan

- [x] 1. 🤖 `/spec-feature`: `specs/features/tutor/problem-card.md` (TM-04, TM-08, TM-14, AM-11) · แสดง event `problem` (`{problem_id, text_latex, difficulty, purpose}`) เป็นการ์ดที่ render สมการ · 🙋 May ตัดสินเรื่องที่ spec ยังไม่กำหนด
- [x] 2. 🙋 May review spec
- [ ] 3. 🤖 `/spec-to-tests`
- [ ] 4. 🙋 May review test
- [ ] 5. 🤖 `/implement-feature` + lint, typecheck, test, build

## Definition of done

- ได้ event `problem` แล้วเห็นการ์ดโจทย์ที่ render สมการด้วย `Tex` ในตำแหน่งที่ event มา · ไม่มีปุ่มตัวเลือกคำตอบ (TM-06) · test เดิมผ่าน
- lint, typecheck, test, build ผ่าน

## Decisions

- 2026-10-21 · การ์ดโจทย์ไม่แสดง difficulty และ purpose (May เลือก) · การ์ดแยก ไม่อยู่ใน bubble (api.md §2.2.8)

## Next step

ขั้น 3: `/spec-to-tests` (May อนุมัติตัดบรรทัด problem ใน chat-streaming AC-7 แล้ว)

## Waiting on

ไม่มี

## Notes for next time

- payload: api.md "SSE events" `problem {problem_id, text_latex, difficulty, purpose}` (ไม่มีเฉลย) · `text_latex` เป็น LaTeX ล้วนไม่มีตัวคั่น (api.md Conventions) · stub: `apps/api/app/stubs/session_start.sse`
- `Message.role` ใน api.md ไม่มี `problem` → โจทย์ไม่อยู่ในประวัติ `GET /sessions/{id}` · ถาม Junior
