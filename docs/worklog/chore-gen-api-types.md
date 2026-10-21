# Generate API types จาก /openapi.json

| | |
|---|---|
| Owner | May |
| Branch | `chore/gen-api-types` |
| Checklist item | Generate type จาก `/openapi.json` (`pnpm gen:api`) |
| Status | in progress · 2026-10-21 |

## Plan

- [ ] 1. 🤖 เปิด API ในเครื่อง (`uv run fastapi dev`) แล้วเช็กว่า `/openapi.json` มี endpoint ห้องติวจาก PR #38
- [ ] 2. 🤖 รัน `pnpm gen:api` สร้าง `apps/web/lib/api-schema.ts` ใหม่
- [ ] 3. 🤖 รัน `pnpm lint`, `pnpm typecheck`, `pnpm test`, `pnpm build` ให้ผ่าน
- [ ] 4. 🤖 เทียบ type ที่ generate กับ type ที่เขียนเองใน `components/chat/types.ts` แล้วจดส่วนที่ไม่ตรงไว้ใช้ตอนต่อ HTTP transport (ไม่แก้ component ใน task นี้)
- [ ] 5. 🙋 May ดู diff และสรุปส่วนที่ไม่ตรง แล้วตอบ ok

## Definition of done

- `apps/web/lib/api-schema.ts` มี path ห้องติว (`/exam-preps/{id}/sessions/active`, `/exam-preps/{id}/sessions`, `/sessions/{id}`, `/sessions/{id}/messages`) และ schema `Room`, `Message`
- lint, typecheck, test, build ของ web ผ่าน
- ติ๊ก checklist ได้ถ้า generate ครบทุก endpoint ที่ API มีตอนนี้ (endpoint กลุ่มอื่นยังไม่มีใน API · ถ้า Junior เพิ่มทีหลังให้รัน `pnpm gen:api` ใหม่)

## Decisions

## Next step

ขั้น 1: เปิด API ในเครื่องแล้วเช็ก `/openapi.json`

## Waiting on

ไม่มี

## Notes for next time

- `gen:api` ต้องมี API รันอยู่ที่ `http://localhost:8000`
