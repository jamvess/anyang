# Contract + stub ของ API กลุ่ม scope (D5 · ส่วนแรก)

| | |
|---|---|
| Owner | Jam (item of Junior) |
| Branch | `feat/scope-api-stubs` |
| Checklist item | เขียน router หัวฟังก์ชันของทุก API ใน `specs/system/api.md` ให้หน้า `/docs` ครบ (D5) |
| Status | in progress · 2026-11-01 |

## Plan

ทำเฉพาะ 3 endpoint ที่หน้า scope ของ May (`specs/features/scope/scope-review.md`) ใช้: `GET /exam-preps/{id}/scope`, `GET /topics/{id}/sources`, `POST /exam-preps/{id}/scope/confirm` · `scope/changes` (S14) ยังไม่มี spec หน้าจอ จึงไม่ทำ · กลุ่มอื่น (upload/materials, persona, บัญชี) ทำใน branch ถัดไป

- [x] 1. 🤖 อ่าน `scope-review.md` §3 + §10 (OQ 5–8), ai-orchestration §2.3, data-model (`topics`, `topic_sources`, `past_exam_questions.map_note`, `scope_changes`), UC-02 · ร่าง request/response ของ 3 endpoint พร้อมบอกที่มาของแต่ละ field (ข้อเสนอของ May / data-model / Claude เสนอเอง)
- [x] 2. 🙋 Jam อ่านร่าง ตอบ ok · ส่งข้อความในแชทกลุ่มว่าจะแก้ `api.md` (ไฟล์ร่วม) โดยเขียนเป็นข้อเสนอที่รอ Junior ตัดสิน
- [x] 3. 🤖 ใส่ร่างลง `specs/system/api.md` (v1.6) ในหัวข้อ "Exam prep และ scope" · OQ 5–8 เป็น "รอตัดสิน (Junior)"
- [ ] 4. 🤖 เขียน test `tests/unit/test_scope_api_contract.py` (สิ่งที่ endpoint จริงต้องผ่าน) + `test_scope_stubs.py` (`X-Stub`) · ชื่อ `test_apimd_scope_…` · ต้องแดงก่อน
- [ ] 5. 🙋 Jam review test
- [ ] 6. 🤖 `app/models/scope.py` + `app/routers/scope.py` ที่คืน fixture (copy จาก `apps/web/tests/fixtures/scope/` ไป `app/stubs/`) พร้อม `X-Stub: true` · error envelope แบบเดียวกับห้องติว · test เขียว + ruff
- [ ] 7. 🤖 ตรวจ `/openapi.json` ว่ามี schema ครบ (ให้ May `pnpm gen:api` ได้) · อัปเดตหมายเหตุใน `sprint-checklists.md`

## Definition of done

- `api.md` มีรูปร่าง request/response ของ 3 endpoint ข้างบน · ทุกข้อที่ยังไม่ตัดสินเขียนไว้ใน "รอตัดสิน" ระบุว่ารอ Junior
- `/docs` แสดง 3 endpoint พร้อม schema และ `ErrorResponse` · stub คืน fixture ที่ตรงกับ fixture ของ May
- test contract + stub ผ่าน · CI เขียว
- ข้อ D5 ยังไม่ติ๊ก (ยังเหลือกลุ่มอื่น) · เพิ่มบรรทัดความคืบหน้าใต้ข้อนั้น

## Decisions

- 2026-11-01 · Jam สั่งให้ Claude ทำทุกขั้นจนจบ และขั้นที่ต้องตัดสินใจให้ใช้ข้อเสนอของ Claude · ขั้น 2 (อ่านร่าง) และขั้น 5 (review test) จึงไม่มีคนอ่านทีละขั้น · Jam ต้องอ่าน diff ก่อน `/work-done` และส่งข้อความในแชทกลุ่มเอง
- 2026-11-01 · ไม่ทำ `GET /exam-preps/{id}/scope/changes` · หน้า S14 ยังไม่มี feature spec ถ้าทำตอนนี้ต้องเดารูปร่าง
- 2026-11-01 · ข้อเสนอใน api.md v1.6: `status` ดูจาก `exam_preps.active_scope_version_id` · หัวข้อที่ตัดออกส่งเป็น `stars: 0` · `source_label` = `{ชื่อไฟล์ไม่มีนามสกุล} น.{from}–{to}` · confirm คืน `{scope_version_id, version}` · error `409 scope_not_ready` / `scope_already_confirmed` / `scope_empty` · ทั้งหมดอยู่ใน "รอตัดสิน (v1.6 · Junior)"
- 2026-11-01 · เริ่มจากกลุ่ม scope · หน้า scope ของ May (spec approved 28 ต.ค.) รอ OQ 5–8 และ stub อยู่ · demo รวมต้องแสดง upload → scope
- 2026-11-01 · contract เป็นเรื่องที่ Junior ตัดสิน (`roles.md`) · ช่วง solo จึงเขียนเป็นข้อเสนอใน `api.md` แล้ว stub ตามข้อเสนอ · Junior เปลี่ยนได้ทีหลังใน PR ใหม่
- 2026-11-01 · spec กับ stub อยู่ PR เดียวกัน (ต่างจาก #35/#38) · ไม่ต้องรอ approve แล้ว (ทีมตกลง 31 ต.ค.) แต่ต้องบอกแชทกลุ่มก่อน merge เพราะแก้ `api.md`

## Next step

ขั้น 4: เขียน test contract + stub ของ scope (แบบเดียวกับ `test_room_api_contract.py`)

## Waiting on

- Junior: ตัดสิน contract (OQ 5–8 ของ `scope-review.md` และรายการรอตัดสินใหม่ใน `api.md`) · ทำหลังจาก merge ได้ ถ้าแก้ให้เปิด PR ใหม่
- May: รัน `pnpm gen:api` ฝั่งเว็บหลัง merge (`apps/web/lib/api-schema.ts` เป็นไฟล์ของ May)

## Done today

- 2026-11-01 · ขั้น 1–3: api.md v1.6 หน้าตรวจขอบเขต (`Scope`, `ScopeTopic`, `PastQuestion`, `TopicSources`, `ScopeConfirmed`) + รอตัดสิน 5 ข้อ

## Notes for next time

- แบบของ stub ห้องติว: `app/routers/room.py`, `app/stubs/`, `tests/unit/test_room_api_contract.py`, `test_room_stubs.py` (PR #38)
