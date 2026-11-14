# Feature: จบ session บน DB · สรุปผลการติว (demo ขั้น 9)

| | |
|---|---|
| Area | tutor |
| Requirements | PM-05, TM-13, SA-06 |
| Owner | Jam (endpoint เป็นงานของ Junior · ทำช่วง solo) |
| Reviewer | Jam · Junior ดูย้อนหลัง (การเขียน `tutor_sessions`, repository, api.md รอตัดสินข้อ 1, 6, 7) |
| Status | approved 2026-11-14 (Jam ok spec + test) · implemented 2026-11-14 (PR #136) |
| Related system spec | api.md v1.9 "`POST /sessions/{id}/end`" + รอตัดสิน (v1.9) ข้อ 1, 2, 6, 7 · ai-orchestration §2.2.9 (จบ session), §3 T8 `session_summary` · `room-sessions-db.md` (#123 · ห้องบน DB) · `topic-progress-db.md` (#135 · ระดับของหัวข้อ) · `docs/team/sprint-checklists.md` ⭐ demo ขั้น 9 |

## 1. Context

ปุ่มจบ session เรียก `POST /sessions/{id}/end` ซึ่งยังเป็น stub: ตอบสรุปเดิมทุกครั้งและไม่บันทึกอะไร · session จึงไม่เคยจบจริง (`GET /exam-preps/{id}/sessions/active` ยังคืน session เดิม) และไม่มีสรุปผลการติว (PM-05) · feature นี้ทำ endpoint ในทางที่มี token ตามข้อเสนอของ api.md v1.9 · code รวบรวมผลของ session · `session_summary` (small) เขียนสรุปสั้นๆ (code ตัดสิน · LLM พูด · CLAUDE.md ข้อ 1)

## 2. Behavior

### 2.1 ก่อน SSE (router · JWT ของผู้ใช้ · RLS)

1. ไม่มี token → stub เดิม (`X-Stub` · api.md v1.14 กรณี `AUTH_REQUIRED=false`)
2. session ไม่มี หรือของคนอื่น → `404 not_found` · จบแล้ว (`ended_at` ไม่ว่าง) → `409 session_already_ended` · DB ล่ม → `503 db_unavailable`
3. **ปิด session ก่อนเรียก AI** ด้วยคำสั่งเดียว: `update tutor_sessions set ended_at = now(), end_reason = 'user' where id = … and ended_at is null` · ไม่มีแถวถูกแก้ (request อื่นปิดไปก่อน) → `409 session_already_ended` (api.md v1.9: กดจบพร้อมกันไม่เรียก `session_summary` ซ้ำ)
4. ไม่นับใน rate limit (api.md รอตัดสิน v1.9 ข้อ 2 · จบได้ครั้งเดียว)

### 2.2 ผลของ session (code · pure function ใน `app/domain/room.py`)

1. **คำตอบใน session นี้** = แถว `attempts` ของผู้ใช้ที่ `created_at ≥ tutor_sessions.started_at` และ `topic_id` เป็นหัวข้อของ prep นี้ (attempts ไม่มี `session_id` · เปิดห้องใหม่แล้วโจทย์ค้างของ session ก่อนก็นับใน session ที่ตอบ)
2. ต่อหัวข้อที่มีคำตอบ: ชื่อ · จำนวนคำตอบที่ตรวจ · จำนวนที่ถูก (`is_correct`) · ระดับตอนนี้จาก `topic_progress` (ชื่อระดับภาษาไทยแบบการ์ด · ไม่มีแถว = "ยังไม่เริ่ม") · เรียงตามจำนวนคำตอบมากก่อน แล้ว `order_index`
3. รวม: คำตอบทั้งหมด · ถูกทั้งหมด · `days_left` ของ prep
4. ไม่ได้คำนวณ "mastery เปลี่ยนเท่าไรใน session นี้" (ai-orchestration §2.2.9) เพราะไม่ได้เก็บค่าก่อน session · ใช้ระดับตอนนี้แทน (§9)

### 2.3 สรุป (AI · `session_summary/v1` · tier small)

1. input (string ใน data block): `prep_name` · `days_left` · `topics` (บรรทัดละหัวข้อ `{ชื่อ} · ตอบ {n} ครั้ง ถูก {k} · ระดับตอนนี้ {ระดับ}` · ไม่มีคำตอบ → `none`) · `totals` (`ตอบ {n} ครั้ง ถูก {k}`)
2. output `SessionSummaryResult {lines: [string]}` 1–2 บรรทัดที่ไม่ว่าง (api.md รอตัดสินข้อ 6 · session สั้นอาจมีเรื่องเดียว) · ภาษาไทย · บรรทัดแรก = ทำอะไรไปและผลเป็นอย่างไร · บรรทัดที่สอง (ถ้ามี) = ครั้งหน้าควรทำอะไรต่อ · ไม่มีตัวเลขที่ไม่อยู่ใน facts
3. **AI ล้มหรือ schema ผิดหลัง retry ของ gateway → สรุปจาก template ของ code** (`config/messages.yaml` → `room.session_summary`: มีคำตอบ / ไม่มีคำตอบ · ไฟล์กลาง) · session จบแล้วอยู่ดี

### 2.4 SSE และบันทึก

1. SSE: `session_end {summary_lines}` → `done {message_ids}` (api.md v1.9)
2. บันทึก (JWT ของผู้ใช้) **ก่อน** `done`: `tutor_sessions.summary` = บรรทัดต่อด้วย `\n` · และ**ข้อความ `tutor` ใน `messages`** ของ session (content = บรรทัดต่อด้วย `\n`) → id ใน `done.message_ids` (api.md รอตัดสินข้อ 7 · PM-05 "ในรูปแบบ chat message" · โหลดใหม่ยังเห็นใน `GET /sessions/{id}/messages`)
3. บันทึกไม่ได้ → log แล้ว `done` ไม่มี id นั้น (แบบ #123 AC-5 · session ปิดแล้วตั้งแต่ §2.1 ข้อ 3)

### 2.5 กลับมาติวต่อ (TM-13)

หลังจบ `GET /exam-preps/{id}/sessions/active` → `404 no_active_session` (#123) · หน้าเว็บสร้าง session ใหม่ (`POST /exam-preps/{id}/sessions`) · โจทย์ค้างของ prep (`ended_at` ของโจทย์ว่าง) ได้กลับมา (#131 §2.3 ข้อ 1) · การ์ดตามแถว `topic_progress` (#135) · ไม่มีอะไรใหม่ใน feature นี้ · AC-7 ยืนยันว่าทำงานต่อกัน

## 3. Inputs and outputs

| | Type / schema | ตัวอย่าง |
|---|---|---|
| Input | `POST /sessions/{id}/end` ไม่มี body · token | |
| Output (SSE) | `session_end {summary_lines: [1..2]}` → `done {message_ids}` | `["วันนี้ทำลิมิต 3 ข้อ ถูก 2 ข้อ ตอนนี้อยู่ระดับกำลังดีแล้ว", "ครั้งหน้าลองลิมิตที่มีรากอีกสักข้อ แล้วไปต่อแยกตัวประกอบกัน"]` |
| Output (DB) | `tutor_sessions.ended_at`, `end_reason = 'user'`, `summary` · `messages` 1 แถว `tutor` | |
| `SessionSummaryResult` | `{lines: [string]}` 1–2 บรรทัด | |

## 4. Acceptance criteria

fake room repository (+ ปิด session, บันทึกสรุป) + fake problem repository (+ คำตอบตั้งแต่เวลาหนึ่ง) + fake provider · "DB" = integration บน Supabase ในเครื่อง

- **AC-1 (PM-05)** session มีคำตอบ 3 ครั้ง (ลิมิต ถูก 2 · แยกตัวประกอบ ถูก 0) → SSE `session_end` → `done` · `summary_lines` = บรรทัดของ `session_summary` · session มี `ended_at`, `end_reason = 'user'`, `summary` = บรรทัดต่อด้วย `\n` · `messages` มีแถว `tutor` เดียวกัน และ id อยู่ใน `done.message_ids`
- **AC-2 (PM-05)** input ของ `session_summary`: `topics` = `ลิมิต · ตอบ 2 ครั้ง ถูก 2 · ระดับตอนนี้ {ระดับจาก topic_progress}` ก่อน `แยกตัวประกอบ · ตอบ 1 ครั้ง ถูก 0 · ระดับตอนนี้ ยังไม่เริ่ม` (เรียงตามจำนวนคำตอบ) · `totals` = `ตอบ 3 ครั้ง ถูก 2` · `prep_name`, `days_left` ของ prep · คำตอบก่อน `started_at` และของหัวข้อนอก prep ไม่นับ
- **AC-3 (PM-05)** session ไม่มีคำตอบ → `topics` = `none` · ยังเรียก `session_summary` และจบได้
- **AC-4 (PM-05)** `session_summary` ล้ม (ทุก retry) → `summary_lines` = template ของ `room.session_summary` ใน messages.yaml (มีคำตอบ: แทนค่าจำนวน · ไม่มี: ข้อความไม่มีคำตอบ) · บันทึกเหมือน AC-1
- **AC-5** session จบแล้ว → `409 session_already_ended` ก่อน SSE · ไม่เรียก AI · ไม่มีแถวใหม่
- **AC-6** การปิด session ไม่ได้แก้แถว (request อื่นปิดไปก่อน) → `409` · ไม่เรียก AI
- **AC-7 (TM-13)** หลังจบ → `GET /exam-preps/{id}/sessions/active` = `404 no_active_session` · เปิดห้องใหม่ได้ session ใหม่ และโจทย์ค้างเดิมของ prep
- **AC-8** session ไม่มี → `404 not_found` · DB ล่มตอนอ่านหรือปิด → `503 db_unavailable`
- **AC-9** บันทึก `summary` หรือข้อความไม่ได้ → ยังได้ `session_end` และ `done` (ไม่มี id) · session ปิดแล้ว
- **AC-10** ไม่มี token → stub เดิม (`X-Stub`) · test เดิมของ stub ผ่านโดยไม่แก้
- **AC-tenant (SA-06 · DB)** B จบ session ของ A → `404` · A จบ → แถวของ A ได้ `summary` · B มองไม่เห็นแถวข้อความสรุป

## 5. Data changes

ไม่มี migration · ใช้คอลัมน์ที่มีแล้ว: `tutor_sessions.ended_at`, `end_reason` (check `user`), `summary` · `messages` (role `tutor`) · อ่าน `attempts`, `topics`, `topic_progress`

## 6. API / SSE changes

ไม่มี endpoint หรือ event ใหม่ · `POST /sessions/{id}/end` ในทางที่มี token ทำตาม api.md v1.9 · api.md (ไฟล์กลาง) เขียนว่าทางที่มี token ทำงานจริงแล้ว และตามข้อเสนอรอตัดสินข้อ 1, 2, 6, 7 (Junior ดูย้อนหลัง · §10)

## 7. AI calls

| Purpose | Tier | Output schema | Prompt file |
|---|---|---|---|
| `session_summary` (**prompt ใหม่**) | small | `SessionSummaryResult` | `prompts/session_summary/v1.md` (input `prep_name`, `days_left`, `topics`, `totals`) · `config/ai.yaml` มีแถวแล้ว (`max_tokens: 150`) · ถ้า Gemini 3 ใช้ thinking จนเกิน `max_tokens` ต้องตั้ง `thinking: minimal` (ไฟล์กลาง · ถามก่อน) |

## 8. Test plan

| Test | ระดับ | ครอบคลุม AC |
|---|---|---|
| `tests/unit/test_session_end_db.py` (ไฟล์ใหม่ · subclass ของ fake #123 / #135) | unit | AC-1 ถึง AC-10 |
| test เดิมของ stub (`test_room_rest_stubs.py`, `test_room_rest_api_contract.py`) | unit | AC-10 |
| `test_prompt_data_blocks.py` (เพิ่มแถว `session_summary/v1`) | unit | prompt ใหม่มี data block ครบ |
| `tests/integration/test_session_end_db.py` | integration | AC-tenant, AC-6 บนแถวจริง |
| รันจริงบน Vertex (ขั้น 4 ของ worklog) | มือ | เปิดห้อง → ตอบ 2 ข้อ → จบ → สรุป → เปิดใหม่ |

**ผลรันจริงบน Vertex (14 พ.ย. · ขั้น 4 ของ worklog · API + repository ในหน่วยความจำ · ไม่ใช่ local):** เปิดห้อง → ตอบถูก → ตอบ "ได้ 999" (`incorrect` + `no_answer` · ไม่มี `internal_error` ตาม merge-rules AC-16) → จบ session → `200` `session_end` → `done` · สรุป: "วันนี้เราได้ทบทวนเรื่อง ลิมิต โดยตอบไปทั้งหมด 2 ครั้ง ถูกต้อง 1 ครั้ง ทำให้ระดับตอนนี้ยังอยู่ในระดับ อ่อน" / "ในเซสชันหน้าเรามาพยายามฝึกฝนเรื่อง ลิมิต เพิ่มเติมเพื่อพัฒนาทักษะให้คล่องแคล่วขึ้นกันนะครับ" (ตัวเลขและระดับตรงกับ facts) · `summary` และข้อความ `tutor` ตรงกัน · จบซ้ำ `409` · `sessions/active` `404` · เปิดห้องใหม่ได้ session ใหม่ + โจทย์ค้าง · การ์ดลิมิต `weak`, ความพร้อม 12% · ภาษายังแข็งเล็กน้อย ("เซสชัน", ช่องว่างก่อนชื่อหัวข้อ) · ปรับเป็น `session_summary/v2` ได้ภายหลัง · **Jam รับผล (14 พ.ย.)**

## 9. Out of scope

- จบแบบอื่น: หมดเวลา (`time_budget`), ทำครบแผน (`plan_done`), idle 15 นาที (`idle`) · ระบบเสนอให้จบเอง (TM-12 · S5)
- mastery ที่เปลี่ยนใน session (ต้องเก็บค่าก่อน session · หลัง demo) · `running_summary` (`update_running_summary` ยังไม่มี)
- ใช้ `summary` ตอนเปิดห้องครั้งหน้า (ai-orchestration §2.2.9 · `open_session` v3 หลัง demo)
- หน้าเว็บ: ปุ่มจบ + การ์ดสรุป (May · ใช้ event เดิมของ stub)

## 10. Open questions

1. **(Junior) api.md รอตัดสิน v1.9 ข้อ 1, 2, 6, 7:** feature นี้ทำตามข้อเสนอทั้ง 4 ข้อ (SSE · ไม่นับ rate limit · 1–2 บรรทัด · เก็บเป็นข้อความในแชทด้วย) · ถ้า Junior ตัดสินต่าง แก้ใน PR ใหม่
2. **คำตอบใน session นับจากเวลา:** `attempts` ไม่มี `session_id` · ทางอื่น: เพิ่มคอลัมน์ (migration) · ข้อเสนอ: นับจาก `created_at ≥ started_at` ไปก่อน (ห้องหนึ่งมีผู้ใช้คนเดียว · session ใหม่เปิดได้เมื่อจบอันเก่า)

## 11. Spec changes needed

| ไฟล์ | แก้อะไร | ใคร |
|---|---|---|
| `specs/system/api.md` (ไฟล์กลาง) | `POST /sessions/{id}/end` ทางที่มี token ทำงานจริงตาม §2 · ข้อเสนอรอตัดสินข้อ 1, 2, 6, 7 ใช้แล้ว (รอ Junior ยืนยัน) | Jam · PR นี้ · ถามก่อน |
| `config/messages.yaml` (ไฟล์กลาง) | `room.session_summary` (template สำรอง 2 แบบ) | Jam · PR นี้ · ถามก่อน |
| `config/ai.yaml` (ไฟล์กลาง · ถ้าต้องใช้) | `session_summary` `thinking: minimal` | Jam · PR นี้ · ถามก่อน |
