# การ์ดความคืบหน้า + การ์ดโจทย์ใช้ type ที่ generate จาก API

| | |
|---|---|
| Owner | May |
| Branch | `chore/web-generated-card-types` |
| Checklist item | ไม่มีข้อตรงใน checklist · ต่อจาก #71 (api.md v1.4 `ProgressTopic`) · `apps/web/CLAUDE.md`: ห้ามเขียน request type เอง |
| Status | in progress · 2026-10-28 |

## Plan

- [ ] 1. 🤖 `ProgressCard.tsx` และ `ProblemCard.tsx` ใช้ `components["schemas"]` (`ProgressCardEvent`, `ProgressTopic`, `ProblemEvent`) แทน type ที่เขียนเอง · ไม่เปลี่ยนพฤติกรรม
- [ ] 2. 🙋 May อนุมัติการแก้ test ที่ review แล้ว เฉพาะให้ข้อมูลตัวอย่างตรง type (ไม่เปลี่ยนสิ่งที่ test ตรวจ)
- [ ] 3. 🤖 lint, typecheck, test, build · อัปเดต spec ให้อ้าง api.md v1.4 (ปิด OQ 3, 4 ของ progress-card.md)

## Definition of done

- ไม่มี type ของ payload SSE ที่เขียนเองใน `components/chat/` · test เดิมตรวจสิ่งเดิม · lint, typecheck, test, build ผ่าน

## Decisions

## Next step

ขั้น 1

## Waiting on

ไม่มี

## Notes for next time

- api.md v1.4: `level` = not_started/weak/developing/passed · `origin` = doc/user · `stars` ไม่เป็น null (#71)
