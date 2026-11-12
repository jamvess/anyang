# ห้องติวบันทึกลง DB: `tutor_sessions` + `messages` และ resume (TM-13)

| | |
|---|---|
| Owner | Junior |
| Branch | `feat/room-sessions-db` |
| Checklist item | เตรียม staging สำหรับ demo รวม (ลำดับ 3 ของ journey วันจันทร์: บันทึก messages + resume) |
| Status | in progress · 2026-11-12 |

## Plan

- [x] 1. 🤖 api.md v1.15: ปิด "รอตัดสิน" ของ session (PR #35 ข้อ 2, v1.9 ข้อ 3 และ 9) + กฎการบันทึก + หัวห้องเมื่อยังไม่มี persona · `data-model.md`: `scope_version_id` เป็น null ได้ (กฎสำหรับ planner ของ Jam) · Junior ดูก่อน commit
- [ ] 2. 🙋 Junior บอกกลุ่ม: migration `0004` + ไฟล์กลาง `api.md`
- [x] 3. 🤖 `/spec-feature` → `specs/features/tutor/room-sessions-db.md` (TM-13, PM-05 บางส่วน, SA-06) · 🙋 Junior review
- [x] 4. 🤖 `/spec-to-tests` (unit กับ fake repository + integration กับ anyang-dev) · 🙋 Junior review
- [ ] 5. 🤖 migration `supabase/migrations/0004_tutor_sessions_scope_nullable.sql` (✅ `43a66e9`) + `/implement-feature` (เกือบเสร็จ · commit เป็น wip · ดู Next step)
- [ ] 6. 🙋 Junior `npx supabase db push --remote` ขึ้น anyang-dev แล้ว anyang-staging (dry-run ก่อน)
- [ ] 7. 🤖 `/work-done` → ถาม Junior ก่อน merge

## Definition of done

- มี token: `POST /exam-preps/{id}/sessions` สร้างแถว `tutor_sessions` จริง · ข้อความ user และ tutor บันทึกใน `messages` · `GET /exam-preps/{id}/sessions/active`, `GET /sessions/{id}`, `GET /sessions/{id}/messages` คืนข้อมูลจริง · เปิดห้องใหม่แล้วเห็นประวัติ
- ไม่มี token + `AUTH_REQUIRED=false` → stub เดิม (`X-Stub`) · ไม่มี token + `true` → 401
- isolation ระหว่าง tenant (SA-06) · test ที่ review แล้วไม่ถูกแก้ · CI เขียว

## Decisions

- 2026-11-11 · (1ก) migration `0004`: `tutor_sessions.scope_version_id` เป็น nullable · null = session เริ่มก่อนยืนยัน scope (ทางของ demo) · เมื่อ ingestion + confirm จริงแล้ว session ใหม่ต้องผูก active scope version (กฎของ planner · Jam) · Junior บอกกลุ่มและ `db push` เอง
- 2026-11-11 · (2) หัวห้อง: `user_name` = `nickname` ไม่มีใช้ "คุณ" · `tutor_name` = tutor profile ล่าสุด ไม่มีใช้ preset tutor ตัวแรก · `buddy_name` = null เมื่อไม่มี profile
- 2026-11-11 · (3) เปิด session ที่มี token: แถวจริง + `session` id จริง + ทักทายด้วย template ใน `config/messages.yaml` (ไม่เรียก AI) · ไม่ส่ง `problem` · **ไม่ส่ง `progress_card` จนกว่า prep จะมี scope ที่ยืนยันแล้ว** (fixture readiness จะดูเหมือนคำนวณคะแนนแล้ว ซึ่งอาจารย์เพิ่งถามเรื่องนี้ · Junior ok) (ยังไม่มี planner/`problems`) · บันทึกคำทักเป็นข้อความ tutor
- 2026-11-11 · `0004` Junior push ขึ้นทั้ง anyang-dev และ anyang-staging ในรอบเดียวกัน (dry-run ก่อน, `--remote`, unlink หลังเสร็จ) · staging ต้องมีก่อน #120 เปิด auth ไม่งั้นเปิด session จริงจะล้มที่ NOT NULL
- 2026-11-11 · (4) บันทึก user ก่อน stream · tutor ทั้งก้อนหลัง stream จบ (รวม degrade) · id จริงใน `done.message_ids` · ล้มกลาง stream ไม่บันทึกครึ่ง · tenant อื่น 404 · session จบแล้ว 409 `session_already_ended` · รูป/OCR/verdict ยังไม่บันทึก (ลำดับ 4)

## Done today (2026-11-11)

- api.md v1.15 + data-model.md (scope null ได้, RLS ของ messages กรองแค่ tenant) · spec `room-sessions-db.md` approved · test 4 ไฟล์ review แล้ว (`a0bdfb4`) · migration `0004` เขียนแล้ว (`43a66e9`) · **ยังไม่ได้ push ขึ้น dev/staging**
- implement เกือบเสร็จ (commit `wip`): `config/messages.yaml` + `RoomGreetingConfig`, `app/domain/room.py`, `app/db/room.py`, `app/db/errors.py` (ใช้ร่วมกับ exam_preps), `app/services/room_db.py`, router ห้องติว 5 endpoint, `DoneEvent.message_ids` (ไม่ส่ง key เมื่อ None ให้ test เดิมยังได้ `{}`)
- unit ของ feature นี้ผ่านครบ 95 · integration ยังรันไม่ได้ (รอ `0004` บน dev)

## Next step

1. **Junior ตัดสิน (ค้างจาก 11 พ.ย.):** suite เต็มล้ม 3 test เดิมที่ review แล้วของ Jam (`test_api_auth.py::test_AI04_chat_turn_writes_ai_calls_row_for_the_token_user`, `test_rate_limit.py::test_TM21_message_over_the_limit_is_429_without_an_ai_call`, `test_rate_limit.py::test_TM21_other_room_endpoints_are_not_limited`) · สาเหตุ: override `get_auth` ด้วย token ปลอม → ตอนนี้วิ่งทาง DB → ยิง Supabase จริงจาก unit test (ผิดกฎ no network) แล้วได้ 503
   - ทางเลือก 1 (Claude แนะนำ): autouse fixture ใน `tests/unit/conftest.py` ให้ `get_room_repository` และ `get_exam_prep_repository` คืน `None` เป็นค่าเริ่มต้น · ไม่แก้ไฟล์ test ที่ review แล้ว · test ที่ต้องการ DB override fake เองอยู่แล้ว
   - ทางเลือก 2: แก้ 3 test ของ Jam (ต้องได้ ok + บอก Jam)
2. **Junior push `0004` ขึ้นทั้ง anyang-dev และ anyang-staging ในรอบเดียว** ก่อน #120 เปิด auth (ไม่งั้นเปิด session จริงบน staging ล้มที่ NOT NULL): `npx supabase projects list` → `link --project-ref mnwwhkbizjioibjvpnxl` → `db push --remote --dry-run` (ต้องเห็นแค่ `0004`) → `db push --remote` → `migration list --remote` → `unlink` · แล้วซ้ำกับ `sfapuygntxuelsxsgkay`
3. Claude: รัน integration `tests/integration/test_room_sessions_db.py` กับ anyang-dev → refactor → ruff + suite เต็ม → `pnpm gen:api` (dump OpenAPI ลงไฟล์แล้ว `pnpm exec openapi-typescript`) → commit `feat: … green` → `/work-done` (ถาม Junior ก่อน merge)

## Waiting on

- Junior: ทางเลือก 1/2 ของ 3 test เดิม · push `0004` ขึ้น dev + staging
- May: หน้าห้องติวต้องรองรับ session ที่ไม่มี `progress_card` และไม่มี `problem` (api.md v1.15)

## Notes for next time

- 2026-11-11 · ระวัง: test ที่ใช้ชื่อเดียวกับ fixture ของ stub (`app/stubs/room.json`: "ปาล", "พี่ตาล", "มีน") จะผ่านทั้งที่ยังไม่ implement · test ของ branch นี้ใช้ "นนท์", "พี่ฟ้า", "ต้นกล้า"
- 2026-11-11 · bash heredoc ที่มี `'` ซ้อนกันหลายชั้นใน Bash tool พังทั้ง command (ไม่รันอะไรเลย) · ไฟล์ใหม่ใช้ Write tool

- 2026-11-11 · คำทักเปิดห้องเป็น template ใน `config/messages.yaml` (ไม่ใช่ `prompts/` เพราะ README ของ prompts = 1 โฟลเดอร์ต่อ AI purpose และ `test_prompt_data_blocks.py` ไล่ตรวจทุก `prompts/*/v*.md`) · AI greeting ด้วย `open_session` v2 = follow-up ของ Jam

- ลำดับของ Junior สำหรับวันจันทร์: 1) login + #120 2) exam prep API (#121 merged) 3) branch นี้ 4) upload + Storage 5) ingestion (Jam)
