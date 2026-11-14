# Feature: ห้องติวบน DB · ตอบ → ตรวจ → ใบ้ → ข้อต่อไป

| | |
|---|---|
| Area | tutor |
| Requirements | TM-06 (พิมพ์ + รูป/canvas), AM-01, AM-02, AM-04, AM-05, AM-07, AM-13, PM-01, TM-10, TM-13, SA-06 |
| Owner | Jam |
| Reviewer | Jam · Junior ดูย้อนหลัง (`0006`, repository) |
| Status | approved 2026-11-13 (Jam ok spec + test) · implemented 2026-11-14 (PR #132) |
| Related system spec | `room-problems-db.md` (#131 · โจทย์ในห้องบน DB) · `demo-room.md` §2 E, G–K (บทสนทนา, พิมพ์คำตอบ, วิธีทำ, hint ladder) · `photo-check-in-room.md` · `room-sessions-db.md` · api.md v1.18 · data-model.md รูป 3 · `docs/team/sprint-checklists.md` ⭐ demo ขั้น 7 |

## 1. Context

ห้องที่มี token ให้โจทย์ได้แล้ว (#131) แต่คำตอบที่พิมพ์ไปถึง `tutor_reply` อย่างเดียว และรูป/canvas ยังวิ่งทางเดโม่ที่ใช้โจทย์ตายตัว · ทางตรวจทั้งหมด (`typed_answer` → ตรวจ → `explain_check` → hint ladder → ข้อต่อไป · รูป → `ocr_preview` → ยืนยัน → ตรวจ) มีแล้วใน `photo_check.py` / `room_chat.py` และคุยกับ state ผ่าน interface `RoomState` เท่านั้น · feature นี้ทำ `DbRoomState` ที่อ่าน/เขียน DB แล้วให้ทางที่มี token ใช้ flow เดิมทั้งหมด · บันทึกทุกคำตอบที่ตรวจลง `attempts` (PM-01) · BKT ลง `topic_progress` เป็นขั้น 8 (§9)

## 2. Behavior

### 2.1 ทางไหนใช้ `DbRoomState`

1. **ข้อความพิมพ์** (`POST /sessions/{id}/messages` `{text}`, มี token, มี problem repository · #131): ตรวจ session ก่อน SSE ตามเดิม (404, 409, 503) · session มี**โจทย์ค้าง** (§2.2 ข้อ 1) → `text_message_events` (room_chat) กับ `DbRoomState` และ `typed_answer` ทำงาน **ทุก env** (เดิมเฉพาะในเครื่อง เพราะทางเดโม่ไม่มีโจทย์จริงนอกเครื่อง · demo-room §2 G ข้อ 7) · ไม่มีโจทย์ค้าง → ทางเดิมของ #131 (`tutor_reply` + บันทึก)
2. **รูป / canvas** (`{image_path}`, มี token): มี `ImageStore` **และ** `APP_ENV=local` (เดโม่ในเครื่อง · Storage ยังไม่มี) → ตรวจ session (404, 409, 503) แล้ว `photo_events` กับ `DbRoomState` · นอก local → ทางเดิม (stub หรือ `ImageStore` ที่ test ใส่ · เปิดเมื่อมี Storage · S5) · ไม่มี `ImageStore` → stub เดิม
3. **ยืนยันลายมือ** (`POST /sessions/{id}/ocr/confirm`, มี token, มี `ImageStore`, `APP_ENV=local` ตามข้อ 2): ตรวจ session แล้ว `confirm_events` กับ `DbRoomState`
4. ไม่มี token → ทุกอย่างเหมือนเดิม (stub หรือเดโม่ในเครื่อง)

### 2.2 `DbRoomState` (`app/services/room_db_state.py` · 1 ตัวต่อ request · ผูกกับ session เดียว)

1. `pending_problem` = โจทย์ที่**ยังไม่จบ** (`problems.ended_at is null`) ล่าสุดของ prep ของ session (#131 §2.4) → `PendingProblem` (`problem_id`, `CheckProblem(text, reference_answer, answer_format, solution_steps)`, `text_latex` จาก `text_latex_of`, `difficulty`, `topic_id`) · **"ค้าง" เปลี่ยนจาก "ไม่มี attempt" (#131) เป็น "`ended_at` ว่าง"** เพราะตอนนี้คำตอบที่ผิดก็มีแถว `attempts` แล้ว แต่โจทย์ยังไม่จบ (hint ladder)
2. `ladder` · เฉพาะ `APP_ENV=local` (AM-07 · demo-room §2 K): `wrong_before` = จำนวนแถว `attempts` ของโจทย์ที่ `verdict = incorrect` · `steps_before` = `problems.working_steps` · นอก local → None (เฉลยทันที)
3. `note_try(steps=n)` (ส่งขั้นที่ยังไม่จบ · `continue`) → `problems.working_steps += n` · `note_try(wrong=True)` → ไม่ทำอะไร (แถว `attempts` ของคำตอบนั้นนับให้แล้ว · §2.3)
4. `record_check` (code ตัดสินว่าโจทย์จบ: ถูก, เฉลย, ยอมแพ้) → **ตั้ง `ended_at` ทันที ก่อนคำอธิบาย** (self-review PR #132: ถ้ารอให้คำอธิบายจบ tutor ล้มหรือ client ออกกลางทาง โจทย์จะค้างทั้งที่มีแถว `attempts` แล้ว · ตอบซ้ำได้ attempt ซ้ำ) · โจทย์ที่ไม่ใช่โจทย์ค้างแล้ว (พรีวิวรูปที่ค้าง) ไม่ทำอะไร · แล้ว BKT ลง `topic_progress` เฉพาะเมื่อ request นี้ปิดโจทย์สำเร็จ (`topic-progress-db.md` · PR #135)
5. `next_problem(answered)` → โจทย์ที่ตอบต้องจบแล้ว (ข้อ 4 · ยังไม่จบก็ตั้งตอนนี้) แล้วเลือกหัวข้อและสร้างโจทย์ใหม่ด้วยกฎและ generator ของ #131 (§2.2 ข้อ 3, §2.3) ใน session ปัจจุบัน → `PendingProblem` · ตั้ง `ended_at` ไม่สำเร็จ → None (ไม่งั้น generator ได้โจทย์เดิมกลับมาเป็นโจทย์ค้างของหัวข้อ) · สร้างไม่ได้ → None (flow ไม่ส่ง `ข้อต่อไปนะ` และ `problem`) · พรีวิวที่ค้าง (โจทย์ที่ตอบไม่ใช่โจทย์ค้างแล้ว) → None และ `ladder` / `note_try` ไม่ขยับอะไร (แบบเดโม่ · demo-room §2 K ข้อ 9)
6. `remember(role, text)` → insert `messages` ของ session:
   - ข้อความที่พูดจริง → `role` = `user` (นักเรียน · `input_mode = "text"`) หรือ `tutor` · ข้อความที่นักเรียนพิมพ์ใน request นั้นเป็น `user` เสมอ แม้ขึ้นต้นด้วย `(ยืนยันคำตอบ)` (self-review)
   - **บรรทัดภายใน** ที่ขึ้นต้นด้วย `(ผลตรวจ)`, `(โจทย์)`, `(ยืนยันคำตอบ)`, `(ส่งรูปวิธีทำ)` → `role = "system"` (หน้าเว็บไม่แสดง · `MessageList` แสดงเฉพาะ `user`/`tutor`/`buddy`/`card`) แต่ tutor ยังเห็นในบทสนทนา (ข้อ 7)
   - บันทึกไม่ได้ (DB ล่ม) → log แล้วไปต่อ (คำตอบอยู่บนจอแล้ว · แบบ #123 AC-5)
7. `conversation` = `session.context_recent_turns` turn ล่าสุดจาก `messages` ของ session (ไม่รวมข้อความที่กำลังตอบ · demo-room §2 E ข้อ 4) · `system` ที่ขึ้นต้นด้วย `(ยืนยันคำตอบ)` / `(ส่งรูปวิธีทำ)` เป็นของนักเรียน · `system` อื่นเป็นของติวเตอร์ · ทางเดิมของ #131 (ไม่มีโจทย์ค้าง) ใช้กฎเดียวกัน จึงเห็นบรรทัด `system` ของการตรวจด้วย (self-review)
8. `set_preview` / `take_preview` / `restore_preview` → เก็บในหน่วยความจำของ process แบบเดิม (ภาพที่รอยืนยันอยู่ไม่กี่วินาที · instance เดียวพอสำหรับ demo · ตารางจริงหลัง demo)
9. `progress_card` → None (การ์ดมาตอนเปิดห้อง · #131) · `start_session` → ไม่ทำอะไร

### 2.3 บันทึก `attempts` (PM-01 · hook ใหม่ `record_answer` ของ `RoomState`)

1. ทุกคำตอบที่ได้ event `verdict` (ใบ้, ชมแล้วเฉลย, เฉลย) → 1 แถว `attempts`: `tenant_id`, `user_id` จาก token · `problem_id`, `topic_id`, `skill_id` จากโจทย์ · `answer_text` = บรรทัดที่ตรวจ ต่อด้วย `\n` · `verdict`, `is_correct`, `final_answer_correct`, `error_type`, `first_wrong_line`, `evidence`, `method`, `decided_by`, `confidence` จาก `CheckResult` · `independent` = ตามกฎ demo-room §2 K ข้อ 8 (`attempt_outcome` เมื่อโจทย์จบ · คำตอบที่ได้ใบ้ = `true`)
2. **ไม่บันทึก**: `continue` (ยังไม่จบ) · `ask_working` (ขาดวิธีทำ · ไม่มีหลักฐานว่าทำเอง · demo-room §2 I) · ยอมแพ้ (ไม่มีคำตอบให้ตรวจ · โจทย์จบด้วย `ended_at` อย่างเดียว · BKT ของยอมแพ้เป็นขั้น 8)
3. hook นี้เพิ่มใน `photo_check._verdict_and_explanation` หลังเลือก directive และก่อน `verdict` event · `InMemoryRoomState` / `DemoRoomState` ไม่ทำอะไร (เดโม่เดิมไม่เปลี่ยน)
4. บันทึกไม่ได้ → log แล้วไปต่อ (ผลตรวจอยู่บนจอแล้ว)

### 2.4 สิ่งที่ไม่เปลี่ยน

ทุกข้อของ demo-room §2 G–K (`typed_answer`, ตรวจ, `explain_check/v3` + directive, ขาดวิธีทำ, ยังไม่จบ, ยอมแพ้, ไม่ส่งเฉลยระหว่างใบ้) และ photo-check-in-room §2 (อ่านลายมือ, การ์ดยืนยัน, `no_pending_ocr`) ใช้ตามเดิมผ่าน `DbRoomState` · `done.message_ids` ของ stream เหล่านี้เป็น `[]` (ข้อความถูกบันทึกทีละบรรทัดผ่าน `remember` · หน้าเว็บไม่ได้ใช้ id เพื่อแสดงผล · §10 ข้อ 2)

## 3. Inputs and outputs

| | Type / schema | ตัวอย่าง |
|---|---|---|
| Input | ข้อความพิมพ์ / `image_path` / บรรทัดที่ยืนยัน · session ที่มีโจทย์ค้าง | `{"text": "x^2-49 = (x-7)(x+7)"}` |
| Output (SSE) | เหมือนเดโม่: `verdict` → `token`… → (`token` "ข้อต่อไปนะ" →) `problem` → `done` | ถูก: `verdict {correct}` → คำอธิบาย → `ข้อต่อไปนะ` → `problem` ข้อใหม่ |
| Output (DB) | `attempts` 1 แถวต่อคำตอบที่ตรวจ · `problems.ended_at` / `working_steps` · `messages` (user, tutor, system) · `problems` ข้อใหม่ | |

## 4. Acceptance criteria

fake room repository + fake problem repository (แถวที่ JWT เห็น) + fake provider + SymPy จริง · "DB" = integration บน Supabase ในเครื่อง

- **AC-1 (AM-04, PM-01)** มี token + โจทย์ค้าง (`x^2-49` → `(x-7)(x+7)`) · พิมพ์คำตอบถูกพร้อมวิธีทำ → `typed_answer` ถูกเรียก (นอก local ด้วย) → `verdict correct` → token ของ `explain_check` → `ข้อต่อไปนะ` → `problem` (ข้อใหม่ · แถวใหม่ใน `problems`) → `done` · `attempts` 1 แถว (`verdict correct`, `is_correct true`, `answer_text`, `user_id`, `topic_id`) · โจทย์เดิม `ended_at` ไม่ว่าง
- **AC-2 (AM-07 · local)** ผิดครั้งแรก → `verdict incorrect` → `hint_1` → `problem` เดิม · `attempts` 1 แถว · `ended_at` ว่าง · ผิดครั้งที่ 2 → `hint_2` (นับจาก `attempts`) · ครั้งที่ 3 → `reveal` → ข้อต่อไป · `attempts` 3 แถว
- **AC-3 (AM-07 · ไม่ใช่ local)** ผิดครั้งแรก → `reveal` → ข้อต่อไป (ไม่มี ladder)
- **AC-4** ส่งขั้นที่ยังไม่จบ → `continue` · ไม่มีแถว `attempts` · `working_steps` เพิ่มตามขั้น · ขั้นถัดไป 1 ขั้นผ่านเพราะขั้นสะสม (demo-room AC-42 บน DB)
- **AC-5** ถูกแต่ขาดวิธีทำ → `ask_working` · ไม่มีแถว `attempts` · โจทย์เดิม
- **AC-6** ยอมแพ้ → เฉลย → ข้อต่อไป · ไม่มีแถว `attempts` · โจทย์เดิม `ended_at` ไม่ว่าง
- **AC-7 (TM-10)** ข้อความที่ไม่ใช่คำตอบ → `tutor_reply` ได้โจทย์ค้าง (ไม่มีเฉลย) และบทสนทนาจาก DB · ไม่มี `verdict` · ไม่มีแถว `attempts`
- **AC-8** ไม่มีโจทย์ค้าง → ทางเดิมของ #131 (`typed_answer` ไม่ถูกเรียก)
- **AC-9 (TM-13)** `messages` หลัง AC-2 ครั้งแรก: `user` (ข้อความ), `system` `(ผลตรวจ) verdict incorrect …`, `tutor` (คำอธิบาย), `system` `(โจทย์) …` · ข้อความถัดไปเห็นทั้ง 4 ในบทสนทนา (system เป็นติวเตอร์)
- **AC-10 (TM-06 · local)** รูป → `ocr_preview` ของโจทย์ค้างจาก DB → ยืนยัน → `verdict` → … · `attempts` 1 แถว · `messages` มี `system` `(ส่งรูปวิธีทำ)` และ `(ยืนยันคำตอบ) …`
- **AC-11 (TM-13)** เปิดห้องใหม่หลัง AC-1 → ไม่ได้โจทย์ที่จบแล้ว · หลังผิด 1 ครั้ง (ยังไม่จบ) → ได้โจทย์เดิม (`ended_at` ว่าง แม้มี attempt)
- **AC-12** สร้างข้อต่อไปไม่ได้ → ไม่มี `ข้อต่อไปนะ` และ `problem` · โจทย์เดิมยัง `ended_at` ไม่ว่าง
- **AC-13** บันทึก `attempts` หรือ `messages` ไม่ได้ → stream จบตามปกติ (log)
- **AC-14** ทางที่ไม่มี token (เดโม่เดิม) ไม่เรียก `record_answer` ที่บันทึกอะไร · test เดิมทั้งหมดผ่านโดยไม่แก้
- **AC-tenant (SA-06 · DB)** A ตอบ → แถว `attempts` มี `tenant_id`, `user_id` ของ A · B มองไม่เห็น · B ส่งข้อความเข้า session ของ A → `404`

## 5. Data changes

| Table | Column / index / policy | เพิ่ม / แก้ |
|---|---|---|
| `problems` | `ended_at timestamptz` (null = ยังไม่จบ) · `working_steps integer not null default 0` | **เพิ่ม · migration `0006` · DB เป็นการตัดสินของ Junior (§10 ข้อ 1)** · RLS เดิม |
| `attempts` | ไม่เปลี่ยน · เขียนครั้งแรก | — |
| `messages` | ไม่เปลี่ยน · ใช้ `role = "system"` ที่มีใน check แล้ว | — |

## 6. API / SSE changes

ไม่มี endpoint หรือ event ใหม่ · ทางที่มี token ของ `POST /sessions/{id}/messages` (text, image) และ `POST /sessions/{id}/ocr/confirm` ส่ง event ของเดโม่ (`verdict`, `problem`, `ocr_preview`) ตาม api.md "SSE events" ที่มีอยู่ · api.md (ไฟล์กลาง) เพิ่มคำอธิบายว่าทางที่มี token ทำอะไร (§11)

## 7. AI calls

ไม่มี purpose หรือ prompt ใหม่ · ใช้ `typed_answer/v2`, `check_answer`, `explain_check/v3`, `extract_answer`, `tutor_reply/v2`, `generate_problem/v1`, `open_session/v2` ตามเดิม · `typed_answer` ทำงานนอก local ด้วยในทางที่มี token (เพิ่ม 1 call เล็กต่อข้อความเมื่อมีโจทย์ค้าง · tier small)

## 8. Test plan

| Test | ระดับ | ครอบคลุม AC |
|---|---|---|
| `tests/unit/test_room_answers_db.py` (fake repositories ของ #123 + #131 ที่เพิ่ม attempts/ended_at/working_steps/messages ในไฟล์ใหม่ · ไม่แก้ไฟล์ test เดิม) | unit | AC-1 ถึง AC-13 |
| test เดิมทั้งหมด (`test_demo_room.py`, `test_room_sessions_api.py`, `test_room_problems_api.py`, `test_photo_check_in_room.py`) | unit | AC-14 |
| `tests/integration/test_room_answers_db.py` | integration | AC-tenant, AC-1 บนแถวจริง (ต้องมี `0006`) |
| รันจริงบน Vertex (ขั้น 4 ของ worklog) | มือ | flow ครบ |

**ผลรันจริงบน Vertex (14 พ.ย. · ขั้น 4 ของ worklog · API + repository ในหน่วยความจำ + `APP_ENV=local`):** เปิดห้อง → โจทย์ลิมิตที่มีรากที่ SymPy ยืนยันเฉลย (`probe`) → "ได้ 999" → `incorrect` + hint_1 + โจทย์เดิม → "ได้ 998" → hint_2 + โจทย์เดิม → ยอมแพ้ → เฉลยเต็ม → "ข้อต่อไปนะ" → โจทย์ใหม่ → ตอบถูกพร้อมวิธีทำ → `correct` → ข้อต่อไป · `attempts` 3 แถว (ผิด 2, ถูก 1) · `ended_at` 2 ข้อ · `messages` เป็น `user` / `tutor` / `system` ตาม §2.2 ข้อ 6 · **เจอตอนรัน:** (1) รอบแรก LLM จัด "999" เป็น `no_answer` แต่ SymPy ชี้บรรทัด 1 → `verdict` event ไม่รับ → `internal_error` · แก้ใน merge-rules.md (AC-16, AC-17 · Jam ok) (2) การ์ดโจทย์เดิมที่ขึ้นซ้ำเปลี่ยน `purpose` เป็น `practice` · แก้ให้ใช้ของแถว `problems` (3) **ข้อต่อไปซ้ำกับข้อที่เพิ่งจบ** (ทั้งสองรอบ · `generate_problem` ไม่รู้โจทย์ที่เคยให้) · Jam เลือก: prompt `generate_problem/v2` + input โจทย์ก่อนหน้า + ตัดโจทย์ซ้ำ · PR ถัดไปก่อน demo (§10 ข้อ 4)

## 9. Out of scope

- BKT ลง `topic_progress` และการ์ดที่เปลี่ยนตาม mastery (ขั้น 8) · จบ session (ขั้น 9)
- รูปบน staging (ต้องมี Storage · S5) · ตาราง preview ที่รอยืนยัน
- การ์ดโจทย์/verdict ในประวัติเมื่อรีเฟรช (May · #131 §10 ข้อ 3)

## 10. Open questions

1. **(Junior) migration `0006`:** `problems.ended_at` + `problems.working_steps` · ทางอื่น: "จบ" คิดจาก `attempts` (ถูก หรือผิดครบ) แต่ยอมแพ้ไม่มี attempt และกฎ ladder ต่างกันตาม env · ข้อเสนอ: `0006` · ขึ้นแค่ในเครื่องจน Junior `db push`
2. **`done.message_ids` เป็น `[]` ใน stream ตรวจคำตอบ:** หน้าเว็บไม่ใช้ id แสดงผล · ถ้า May ต้องใช้ (เช่น ลบข้อความชั่วคราว) ค่อยรวม id ของข้อความ `tutor` ที่บันทึกใน stream นั้น
3. **`typed_answer` นอก local:** เพิ่มต้นทุน 1 call (tier small) ต่อข้อความเมื่อมีโจทย์ค้าง · ข้อเสนอ: เปิด เพราะเป็นทางจริงของผลิตภัณฑ์ (intent router เต็มรูปแบบมาแทนภายหลัง)

4. ~~**(Jam ตัดสิน 14 พ.ย. · PR ถัดไป) ข้อต่อไปซ้ำ**~~ **ทำแล้ว PR #133** (`room-problems-db.md` §2.3 v2 · วัดบน Vertex ไม่มีโจทย์ซ้ำ): `generate_problem/v2` รับโจทย์ล่าสุดของหัวข้อเดียวกันใน prep ไม่เกิน `session.avoid_recent_problems` ข้อ และ code ไม่รับโจทย์ที่คณิตใน `$…$` ซ้ำกับข้อเหล่านั้น (`same_problem` · นับเป็นรอบที่ไม่ผ่าน) · โจทย์ที่เก่ากว่านั้น หรือของหัวข้ออื่น ไม่ได้เทียบ

## 11. Spec changes needed

| ไฟล์ | แก้อะไร | ใคร |
|---|---|---|
| `supabase/migrations/0006_problems_ended.sql` + `data-model.md` | §5 | Jam · PR นี้ · Junior `db push` |
| `specs/system/api.md` (ไฟล์กลาง) | ทางที่มี token ของ messages (text/image) และ ocr/confirm: ตรวจคำตอบกับโจทย์ค้างใน DB · บันทึก `attempts` · `done.message_ids` ว่างในทางนี้ | Jam · PR นี้ |
| `room-problems-db.md` §2.3 ข้อ 1, §2.4 | "ค้าง" = `ended_at` ว่าง (แทน "ไม่มี attempt") | Jam · PR นี้ |
| `demo-room.md` §2 G ข้อ 7 | `typed_answer` ทำงานนอก local ในทางที่มี token | Jam · PR นี้ |
