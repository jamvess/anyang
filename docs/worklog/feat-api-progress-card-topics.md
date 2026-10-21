# progress_card.topics[] มี type (part of #40)

| | |
|---|---|
| Owner | Junior |
| Branch | `feat/api-progress-card-topics` |
| Checklist item | เขียน router หัวฟังก์ชันของทุก API ใน `specs/system/api.md` ให้หน้า `/docs` ครบ (D5) |
| Status | in progress · 2026-10-21 |

## Plan

- [ ] 1. 🤖 `specs/system/api.md` v1.4: type ของ `progress_card.topics[]` (`id`, `name`: string · `stars`: integer ช่วงตามที่ May ตอบ, ไม่เป็น null · `level`: `not_started` \| `weak` \| `developing` \| `passed` · `review_due`: boolean · `origin`: `doc` \| `user`) + กฎ: backend ไม่ส่งหัวข้อที่ `importance` ยังไม่ได้คำนวณ (ดาวคำนวณในขั้น 5d ก่อนยืนยัน scope และการ์ดแสดงหลังยืนยัน) · ไฟล์ร่วม → May + Jam review, บอกแชทกลุ่ม
- [ ] 2. 🤖 test ใหม่ `apps/api/tests/unit/test_progress_card_topics_contract.py` (red): fixture ของ stub ผ่าน · ปฏิเสธ `level`/`origin` ที่ไม่รู้จัก, `stars` นอกช่วง, `stars = null`, field เกิน · `level` Literal = `learning.yaml` `levels.show` · OpenAPI: `level`/`origin` เป็น enum, `stars` เป็น integer ไม่ nullable และ required · ไม่แก้ `test_room_api_contract.py`
- [ ] 3. 🙋 review test ข้อ 2
- [ ] 4. 🤖 `app/models/room.py`: `ProgressTopic` + `ProgressCardEvent.topics: list[ProgressTopic]` (green) · ruff + pytest
- [ ] 5. 🤖 regenerate `apps/web/lib/api-schema.ts` ด้วย `pnpm gen:api` (ไม่แตะ `ProgressCard.tsx` ของ May)
- [ ] 6. 🙋 May ตอบช่วงของ `stars` (0–3 หรือ 1–3) ใน PR #63 → ปรับ api.md + test + model ให้ตรง

## Definition of done

- api.md มี type ของ `progress_card.topics[]` และกฎ stars ไม่เป็น null
- `ProgressCardEvent.topics` เป็น model ที่มี type · fixture ใน `app/stubs/` ผ่าน · test ใหม่ผ่าน · test ที่ล็อกแล้วไม่ถูกแก้
- `pnpm gen:api` ได้ `stars: number` (ไม่ใช่ `number | null`), `level`/`origin` เป็น union ของ string
- May + Jam approve · **ไม่ merge จนกว่า May ตอบช่วงของ stars**

## Decisions

- 2026-10-21 · PR นี้ "Part of #40" ทำเฉพาะ topics · `error.code` แยก PR ทีหลัง · ไม่ต้องรอ api.md จาก #36
- 2026-10-21 · `stars` ไม่เป็น null ใน progress_card: backend ตัดหัวข้อที่ `importance` ยังเป็น NULL ออก · type ที่ generate จึงเป็น number
- 2026-10-21 · `id` เป็น `str` ไม่ใช่ `UUID` (stub ใช้ `"t1"`, api.md บอก string)
- 2026-10-21 · `progress-card.md` (ของ May) Open questions 3, 4 ตอบแล้ว → แค่บอกใน PR description ไม่แก้ไฟล์เอง

## Next step

ข้อ 1: แก้ `specs/system/api.md` แถว `progress_card` ใน "SSE events" + bump เป็น v1.4

## Waiting on

May: ช่วงของ `stars` (คำถามใน PR #63 https://github.com/jamvess/anyang/pull/63#issuecomment-6312127136)

## Notes for next time

- `topics.importance` ใน DB เป็น nullable 0–3 · `level` ตรงกันทั้ง `learning.yaml` และ check ของ `topic_progress.level`
