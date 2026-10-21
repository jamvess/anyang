# Generate API types จาก /openapi.json

| | |
|---|---|
| Owner | May |
| Branch | `chore/gen-api-types` |
| Checklist item | Generate type จาก `/openapi.json` (`pnpm gen:api`) |
| Status | ready for work-done · 2026-10-21 |

## Plan

- [x] 1. 🤖 เปิด API ในเครื่อง (`uv run fastapi dev`) แล้วเช็กว่า `/openapi.json` มี endpoint ห้องติวจาก PR #38
- [x] 2. 🤖 รัน `pnpm gen:api` สร้าง `apps/web/lib/api-schema.ts` ใหม่
- [x] 3. 🤖 รัน `pnpm lint`, `pnpm typecheck`, `pnpm test`, `pnpm build` ให้ผ่าน
- [x] 4. 🤖 เทียบ type ที่ generate กับ type ที่เขียนเองใน `components/chat/types.ts` แล้วจดส่วนที่ไม่ตรงไว้ใช้ตอนต่อ HTTP transport (ไม่แก้ component ใน task นี้)
- [x] 5. 🙋 May ดู diff และสรุปส่วนที่ไม่ตรง แล้วตอบ ok

## Definition of done

- `apps/web/lib/api-schema.ts` มี path ห้องติว (`/exam-preps/{id}/sessions/active`, `/exam-preps/{id}/sessions`, `/sessions/{id}`, `/sessions/{id}/messages`) และ schema `Room`, `Message`
- lint, typecheck, test, build ของ web ผ่าน
- ติ๊ก checklist ได้ถ้า generate ครบทุก endpoint ที่ API มีตอนนี้ (endpoint กลุ่มอื่นยังไม่มีใน API · ถ้า Junior เพิ่มทีหลังให้รัน `pnpm gen:api` ใหม่)

## Decisions

- 2026-10-21 · generate จาก API ที่ยังเป็น api.md v1.2 (stub ของ PR #38) · v1.3 (`attachment_name`, `done.message_ids`) ยังไม่มีใน API · รัน `pnpm gen:api` ใหม่เมื่อ Junior ทำตาม v1.3

## ส่วนที่ไม่ตรงกับ type ที่เขียนเอง (`components/chat/types.ts`) · ใช้ตอนต่อ HTTP transport

- `ChatMessage` ไม่มี `card` แต่ `Message` จาก API มี `card: object | null`
- `RoomData` ไม่มี `session_id` แต่ `Room` จาก API มี
- `SendMessageRequest` รับ `text` หรือ `image_path` อย่างใดอย่างหนึ่ง (api.md รอตัดสินข้อ 1 ของ Jam) แต่ `SendPayload` ของ UI ส่งทั้งสองพร้อมกันได้ และส่ง `File` ไม่ใช่ path (ต้องผ่าน `/uploads` ที่ยังไม่มี stub)
- `DoneEvent` เป็น `{}` และ `Message` ยังไม่มี `attachment_name` (API ยังเป็น v1.2)
- `apps/web/CLAUDE.md` ห้ามเขียน request type เอง → ตอนต่อ HTTP transport ควรให้ `ChatMessage` / `RoomData` มาจาก `components["schemas"]` แทน

## Next step

รัน /work-done

## Waiting on

ไม่มี

## Notes for next time

- `gen:api` ต้องมี API รันอยู่ที่ `http://localhost:8000`
