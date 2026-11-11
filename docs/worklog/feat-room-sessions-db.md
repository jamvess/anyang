# ห้องติวบันทึกลง DB: `tutor_sessions` + `messages` และ resume (TM-13)

| | |
|---|---|
| Owner | Junior |
| Branch | `feat/room-sessions-db` |
| Checklist item | เตรียม staging สำหรับ demo รวม (ลำดับ 3 ของ journey วันจันทร์: บันทึก messages + resume) |
| Status | in progress · 2026-11-11 |

## Plan

- [x] 1. 🤖 api.md v1.15: ปิด "รอตัดสิน" ของ session (PR #35 ข้อ 2, v1.9 ข้อ 3 และ 9) + กฎการบันทึก + หัวห้องเมื่อยังไม่มี persona · `data-model.md`: `scope_version_id` เป็น null ได้ (กฎสำหรับ planner ของ Jam) · Junior ดูก่อน commit
- [ ] 2. 🙋 Junior บอกกลุ่ม: migration `0004` + ไฟล์กลาง `api.md`
- [x] 3. 🤖 `/spec-feature` → `specs/features/tutor/room-sessions-db.md` (TM-13, PM-05 บางส่วน, SA-06) · 🙋 Junior review
- [x] 4. 🤖 `/spec-to-tests` (unit กับ fake repository + integration กับ anyang-dev) · 🙋 Junior review
- [ ] 5. 🤖 migration `supabase/migrations/0004_tutor_sessions_scope_nullable.sql` + `/implement-feature`
- [ ] 6. 🙋 Junior `npx supabase db push --remote` ขึ้น anyang-dev แล้ว anyang-staging (dry-run ก่อน)
- [ ] 7. 🤖 `/work-done` → ถาม Junior ก่อน merge

## Definition of done

- มี token: `POST /exam-preps/{id}/sessions` สร้างแถว `tutor_sessions` จริง · ข้อความ user และ tutor บันทึกใน `messages` · `GET /exam-preps/{id}/sessions/active`, `GET /sessions/{id}`, `GET /sessions/{id}/messages` คืนข้อมูลจริง · เปิดห้องใหม่แล้วเห็นประวัติ
- ไม่มี token + `AUTH_REQUIRED=false` → stub เดิม (`X-Stub`) · ไม่มี token + `true` → 401
- isolation ระหว่าง tenant (SA-06) · test ที่ review แล้วไม่ถูกแก้ · CI เขียว

## Decisions

- 2026-11-11 · (1ก) migration `0004`: `tutor_sessions.scope_version_id` เป็น nullable · null = session เริ่มก่อนยืนยัน scope (ทางของ demo) · เมื่อ ingestion + confirm จริงแล้ว session ใหม่ต้องผูก active scope version (กฎของ planner · Jam) · Junior บอกกลุ่มและ `db push` เอง
- 2026-11-11 · (2) หัวห้อง: `user_name` = `nickname` ไม่มีใช้ "คุณ" · `tutor_name` = tutor profile ล่าสุด ไม่มีใช้ preset tutor ตัวแรก · `buddy_name` = null เมื่อไม่มี profile
- 2026-11-11 · (3) เปิด session ที่มี token: แถวจริง + `session` id จริง + ทักทายด้วย `open_session` · ไม่ส่ง `problem` · **ไม่ส่ง `progress_card` จนกว่า prep จะมี scope ที่ยืนยันแล้ว** (fixture readiness จะดูเหมือนคำนวณคะแนนแล้ว ซึ่งอาจารย์เพิ่งถามเรื่องนี้ · Junior ok) (ยังไม่มี planner/`problems`) · บันทึกคำทักเป็นข้อความ tutor
- 2026-11-11 · `0004` Junior push ขึ้นทั้ง anyang-dev และ anyang-staging ในรอบเดียวกัน (dry-run ก่อน, `--remote`, unlink หลังเสร็จ) · staging ต้องมีก่อน #120 เปิด auth ไม่งั้นเปิด session จริงจะล้มที่ NOT NULL
- 2026-11-11 · (4) บันทึก user ก่อน stream · tutor ทั้งก้อนหลัง stream จบ (รวม degrade) · id จริงใน `done.message_ids` · ล้มกลาง stream ไม่บันทึกครึ่ง · tenant อื่น 404 · session จบแล้ว 409 `session_already_ended` · รูป/OCR/verdict ยังไม่บันทึก (ลำดับ 4)

## Next step

ข้อ 5: เขียน `0004` แล้ว Junior push ขึ้น dev + staging · ต่อด้วย `/implement-feature`

## Waiting on

- May: หน้าห้องติวต้องรองรับ session ที่ไม่มี `progress_card` และไม่มี `problem` (api.md v1.15)

## Notes for next time

- 2026-11-11 · คำทักเปิดห้องเป็น template ใน `config/messages.yaml` (ไม่ใช่ `prompts/` เพราะ README ของ prompts = 1 โฟลเดอร์ต่อ AI purpose และ `test_prompt_data_blocks.py` ไล่ตรวจทุก `prompts/*/v*.md`) · AI greeting ด้วย `open_session` v2 = follow-up ของ Jam

- ลำดับของ Junior สำหรับวันจันทร์: 1) login + #120 2) exam prep API (#121 merged) 3) branch นี้ 4) upload + Storage 5) ingestion (Jam)
