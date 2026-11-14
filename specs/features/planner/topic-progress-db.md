# Feature: BKT ลง `topic_progress` · การ์ดเปลี่ยนตาม mastery (demo ขั้น 8)

| | |
|---|---|
| Area | planner |
| Requirements | PM-02, PM-03, PM-06, TM-15, SA-06 |
| Owner | Jam |
| Reviewer | Jam · Junior ดูย้อนหลัง (migration `0007`, repository) |
| Status | draft 2026-11-14 (PR #135) |
| Related system spec | `bkt-mastery.md` (BKT, ระดับ, ความพร้อม · `domain/bkt.py`) · `demo-room.md` §2 D, §2 K ข้อ 8 (BKT ในเดโม่ · นับครั้งเดียวต่อโจทย์) · `room-answers-db.md` §2.2 ข้อ 4 (`record_check` = โจทย์จบ) · `room-problems-db.md` §2.2 ข้อ 2 (การ์ดจาก `topic_progress`), §10 ข้อ 2 (`d_max`) · learning-model §1, §4, §5 · data-model.md รูป 3 · `docs/team/sprint-checklists.md` ⭐ demo ขั้น 8 |

## 1. Context

ห้องที่มี token บันทึก `attempts` แล้ว (#132) และการ์ดตอนเปิดห้องอ่าน `topic_progress` อยู่แล้ว (#131) แต่ไม่มีโค้ดไหนเขียน `topic_progress` · ตอบกี่ข้อการ์ดก็ยังเป็น "ยังไม่เริ่ม" และความพร้อม 0% · เดโม่ในเครื่องคิด BKT ได้แล้วแต่เก็บใน memory (`demo-room.md` §2 D) · feature นี้ใช้ BKT เดียวกัน (`domain/bkt.py`) แล้วเขียนลง `topic_progress` ของผู้ใช้ ตอนที่ code ตัดสินว่าโจทย์จบ · demo ขั้น 8 ในตาราง demo: "เปิดห้องใหม่เห็นระดับและความพร้อมเปลี่ยน"

## 2. Behavior

### 2.1 เมื่อไหร่ที่ mastery เปลี่ยน

1. `DbRoomState.record_check(pending, is_correct, independent)` ถูกเรียกครั้งเดียวต่อโจทย์ ตอนที่ code ตัดสินว่าโจทย์จบ (`room-answers-db.md` §2.2 ข้อ 4): ถูก (`praise_and_show`), เฉลย (`reveal` หลังผิดครบ หรือไม่มี ladder), ยอมแพ้ · ค่า `is_correct`, `independent` มาจาก `_record_attempt` ของ `photo_check.py` ตามกฎเดิม (`demo-room.md` §2 K ข้อ 8): ยอมแพ้และเฉลย = ผิด · ถูกหลังใบ้ครั้งสุดท้าย = ไม่ independent · ไม่มี ladder = ตามผลตรวจ independent
2. **ไม่เปลี่ยน:** ใบ้ (`hint_1`, `hint_2`), `continue`, `ask_working` (โจทย์ยังไม่จบ · ไม่เรียก `record_check`) · พรีวิวรูปที่ค้างของโจทย์ที่จบไปแล้ว (`record_check` ไม่ทำอะไร · `room-answers-db.md` §2.2 ข้อ 4)
3. **นับครั้งเดียว:** BKT ทำเฉพาะเมื่อโจทย์นั้นยังเป็นโจทย์ค้าง (`ended_at` ว่าง) ตอนที่ request นี้เริ่มตรวจ · โจทย์ที่ request อื่นปิดไปแล้วไม่นับซ้ำ

### 2.2 คำนวณ (pure · `domain/bkt.py` · code ตัดสิน CLAUDE.md ข้อ 1)

1. ก่อน = แถว `topic_progress` ของผู้ใช้กับ `topic_id` ของโจทย์ → `TopicProgress(mastery, attempts_n, d_max)` · ไม่มีแถว → `TopicProgress(bkt.p_init, 0, 0)`
2. หลัง = `record_attempt(ก่อน, is_correct, difficulty ของโจทย์, independent, cfg)` · `bkt.count_only_independent` = true และไม่ independent → ไม่เปลี่ยน และ**ไม่เขียน**
3. `level` = `level(หลัง, target_difficulty(ดาวของหัวข้อ, "normal"), skills_covered=True, cfg)` · `skills_covered` เป็น true เสมอเหมือนเดโม่และการ์ดของ #131 (ยังไม่นับ skill coverage · §9)
4. `correct_n` = เดิม + 1 เมื่อนับและถูก

### 2.3 บันทึก (repository · JWT ของผู้ใช้ · RLS `owner_rows`)

1. upsert แถว `topic_progress` ตาม primary key (`user_id`, `topic_id`): `tenant_id`, `user_id` จาก token · `exam_prep_id` ของ session · `topic_id` · `mastery` · `level` · `attempts_n` · `correct_n` · `d_max` (คอลัมน์ใหม่ §5) · `last_seen_at` = ตอนนี้ · คอลัมน์อื่น (`stage`, `skill_coverage`, `error_counts`, `fail_streak`, review, park) ไม่แตะ
2. อ่านหรือเขียนไม่ได้ (DB ล่ม) → log แล้วไปต่อ (ผลตรวจและคำอธิบายอยู่บนจอแล้ว · แบบ `room-answers-db.md` §2.3 ข้อ 4)
3. แยกตาม exam prep (PM-06): หัวข้อเป็นของ prep เดียว (`topics.exam_prep_id`) จึงไม่ปนข้าม prep

### 2.4 การ์ดตอนเปิดห้อง (TM-15, PM-03)

`room-problems-db.md` §2.2 ข้อ 2 ตามเดิม แต่ `ProgressFacts.d_max` อ่านจากคอลัมน์ใหม่ (เดิม None → 0) · ระดับ, `passed`, ความพร้อม (`readiness` ของ `mastery_eff`) จึงขยับตาม `topic_progress` · การเลือกหัวข้อ (`choose_topic`) ใช้ mastery และระดับใหม่ด้วย · การ์ดมาตอนเปิดห้องเท่านั้น ไม่ส่งกลาง session (`demo-room.md` §2 J ข้อ 1 · ทางสำรองของ demo ขั้น 8)

## 3. Inputs and outputs

| | Type / schema | ตัวอย่าง |
|---|---|---|
| Input | โจทย์ที่จบ (`PendingProblem`: `topic_id`, `difficulty`) · `is_correct`, `independent` · แถว `topic_progress` เดิม (ถ้ามี) · ดาวของหัวข้อ | ลิมิต ★★★ · โจทย์ระดับ 3 · ตอบถูกเอง |
| Output (DB) | `topic_progress` 1 แถวต่อผู้ใช้ต่อหัวข้อ | `mastery 0.68…`, `attempts_n 1`, `correct_n 1`, `d_max 3`, `level developing` |
| Output (SSE) | ไม่มี event ใหม่ · `progress_card` ตอนเปิดห้องใหม่เปลี่ยนตามแถว | ลิมิต `developing`, `readiness` > 0 |

## 4. Acceptance criteria

fake room repository + fake problem repository (เพิ่ม `topic_progress`) + fake provider + SymPy จริง · ค่าที่คาดหวังคิดด้วย `domain/bkt.py` กับ `config/learning.yaml` (ไม่เขียนตัวเลขลง test) · "DB" = integration บน Supabase ในเครื่อง

- **AC-1 (PM-02)** ไม่มีแถว · ตอบถูกพร้อมวิธีทำ (ไม่ใช่ local · ไม่มี ladder) → แถวใหม่: `mastery` = `update_mastery(p_init, True)`, `attempts_n` 1, `correct_n` 1, `d_max` = `difficulty` ของโจทย์, `level` ตาม §2.2 ข้อ 3, `tenant_id`/`user_id` จาก token, `exam_prep_id` ของ session, `topic_id` ของโจทย์
- **AC-2 (PM-02)** ไม่มีแถว · ตอบผิด (ไม่ใช่ local → เฉลยทันที) → `mastery` = `update_mastery(p_init, False)`, `attempts_n` 1, `correct_n` 0, `d_max` 0
- **AC-3 (PM-02)** ยอมแพ้ → นับเป็นผิดแบบ AC-2
- **AC-4 (PM-02)** มีแถวเดิม (`mastery` m, `attempts_n` 3, `correct_n` 2, `d_max` 2) · ตอบถูกโจทย์ระดับ 3 → `mastery` = `update_mastery(m, True)`, `attempts_n` 4, `correct_n` 3, `d_max` 3
- **AC-5 (PM-02 · local)** ผิด → hint_1 → ผิด → hint_2 → ถูก (หลังใบ้ครั้งสุดท้าย · ไม่ independent) → ไม่มีแถว `topic_progress` (`count_only_independent`) · ระหว่างใบ้ก็ไม่มีแถว
- **AC-6 (PM-02)** `continue` และ `ask_working` → ไม่มีแถว
- **AC-7 (TM-15, PM-03)** แถว `topic_progress` ของลิมิต (★★★): `mastery` สูงกว่า `mastery_threshold`, `d_max` = ระดับเป้าของ ★★★ → เปิดห้อง → การ์ดลิมิต `passed`, `passed` 1, `readiness` > 0 · ถ้า `d_max` ต่ำกว่าเป้า → ไม่ `passed` (เพดาน `mastery_eff`)
- **AC-8** บันทึก `topic_progress` ไม่ได้ (DB ล่ม) → stream จบปกติ · ยังมี `verdict` และข้อต่อไป
- **AC-tenant (SA-06 · DB)** A ตอบถูก → แถว `topic_progress` มี `tenant_id`, `user_id` ของ A · B มองไม่เห็นแถวนั้น · A เปิดห้องใหม่ → การ์ดไม่ใช่ `not_started` แล้ว

## 5. Data changes

| Table | Column / index / policy | เพิ่ม / แก้ |
|---|---|---|
| `topic_progress` | `d_max smallint not null default 0 check (d_max between 0 and 3)` (ระดับยากสูงสุดที่ตอบถูกเอง · learning-model §4) | **เพิ่ม · migration `0007`** · RLS เดิม (`owner_rows`) · ปิด `room-problems-db.md` §10 ข้อ 2 |

## 6. API / SSE changes

ไม่มี · `progress_card` ตอนเปิดห้องมีรูปเดิม แค่ค่ามาจากแถวที่เปลี่ยนแล้ว · `GET /exam-preps/{id}/progress` ยังเป็น stub (§9)

## 7. AI calls

ไม่มี

## 8. Test plan

| Test | ระดับ | ครอบคลุม AC |
|---|---|---|
| `tests/unit/test_topic_progress_db.py` (ไฟล์ใหม่ · fake ของ #132 + `topic_progress` · ไม่แก้ไฟล์ test เดิม) | unit | AC-1 ถึง AC-8 |
| test เดิมทั้งหมด (`test_room_answers_db.py`, `test_room_problems_api.py`, `test_demo_room.py`, `test_bkt.py`) | unit | ไม่เปลี่ยนพฤติกรรมเดิม |
| `tests/integration/test_topic_progress_db.py` | integration | AC-tenant (ต้องมี `0007`) |
| รันจริงบน Vertex (ขั้น 4 ของ worklog) | มือ | เปิดห้อง → ตอบถูก 2 ข้อ → เปิดใหม่ การ์ดขยับ |

## 9. Out of scope

- จบ session + สรุป (demo ขั้น 9) · การ์ดกลาง session (TM-11 · S5)
- `GET /exam-preps/{id}/progress` จริง และหน้า home (PM-04 · S5)
- skill coverage (`skill_coverage` · `topic_skills` · SM-12), `error_counts`, `fail_streak`, spaced review, Park (bkt-mastery §9)
- mode ของ planner (ใช้ `normal` ตาม #131)

## 10. Open questions

1. **(Junior) migration `0007`:** `topic_progress.d_max` · ทางอื่น: คิด `d_max` จาก `attempts` + `problems.difficulty` ทุกครั้ง (ไม่ต้อง migration แต่ query หนักขึ้นทุกครั้งที่เปิดห้อง) · ข้อเสนอ: `0007` · ขึ้นแค่ในเครื่องจน Junior `db push` (`anyang-dev` ตาม D2 · PR #134)
2. **`level` ที่บันทึก:** คิดด้วย `skills_covered = true` (เหมือนเดโม่) · เมื่อมี skill coverage (S5) ระดับ `passed` จะเข้มขึ้น · การ์ดคิดระดับใหม่จาก mastery ทุกครั้งอยู่แล้ว คอลัมน์ `level` จึงเป็นค่าล่าสุดสำหรับหน้าอื่น

## 11. Spec changes needed

| ไฟล์ | แก้อะไร | ใคร |
|---|---|---|
| `supabase/migrations/0007_topic_progress_d_max.sql` + `data-model.md` | §5 | Jam · PR นี้ · Junior `db push` |
| `room-answers-db.md` §2.2 ข้อ 4 | `record_check` ทำ BKT ลง `topic_progress` (เดิม "ขั้น 8") | Jam · PR นี้ |
| `room-problems-db.md` §10 ข้อ 2 | ปิด: `d_max` มีคอลัมน์แล้ว | Jam · PR นี้ |
