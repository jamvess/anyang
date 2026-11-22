# Feature: stage machine ของหัวข้อ (Probe → Teach → Verify → Practice → Done · Park)

| | |
|---|---|
| Area | tutor |
| Requirements | TM-03 (probe ก่อนสอน · ข้ามการอธิบายเมื่อตอบถูก) · TM-04 (สลับ explain กับ practice ทีละหัวข้อ) · AM-08 (Verify ด้วยโจทย์แบบเดียวกัน) · AM-09 (อธิบายใหม่ด้วยมุมที่ต่าง) · TM-16 (ผ่านตาม skill + ระดับเป้า + mastery) · SM-12 (หัวข้อมี skills) |
| Owner | Jam |
| Reviewer | Jam · Junior ดูย้อนหลัง (คอลัมน์ `topic_progress.stage`, `fail_streak` เป็นของ Junior ตอนต่อเข้าห้อง) |
| Status | approved 2026-11-19 (Jam · §10 ข้อ 1 (ก), ข้อ 2–6 ตามข้อเสนอ) · แก้ 2026-11-22 หลัง self-review (Jam · §10 ข้อ 7) |
| Related system spec | ai-orchestration.md §1.3 (P1 code ตัดสินใจ), §2.2.3 (directive), §2.2.4 (ตาราง stage, เงื่อนไข Done, Park, การสอนตาม error type), §2.2.10, §2.5.4 (เลือก skill + difficulty) · learning-model.md §4 (Done, `d_target`), §7 (Park) · `config/learning.yaml` → `done.*`, `park.*`, `bkt.*` · `app/domain/bkt.py` (`level`, `target_difficulty`) · `app/domain/planner.py` (mode) · `app/domain/hint_ladder.py` (เดโม่ในเครื่อง · §10 ข้อ 1) |

## 1. Context

ห้องติวตอนนี้ให้โจทย์ทีละข้อจากหัวข้อที่เลือก แล้วตรวจ + ใบ้ (hint ladder ของเดโม่) แต่ยังไม่มีขั้นการสอน: ไม่ probe ก่อน ไม่ Verify ด้วยโจทย์ skill เดิม ไม่ไล่ skill และไม่รู้ว่าหัวข้อจบเมื่อไหร่ · ai-orchestration §2.2.4 ออกแบบ stage machine ที่ code ตัดสินล้วน (P1) · feature นี้ทำ **ตัวตัดสินใจแบบ pure function** ใน `app/domain/stage_machine.py` (ไม่มี I/O · ไม่มี LLM) · การต่อเข้าห้องติว (อ่าน/เขียน `topic_progress`, ส่ง directive ให้ prompt) เป็น PR ถัดไปหลังส่งวิดีโอ 23 พ.ย. เหมือน planner (#166)

## 2. Behavior

ทุกค่าอ่านจาก `LearningConfig` · ไม่มีตัวเลขในโค้ด · `level` และ `target_difficulty` ใช้ของ `app/domain/bkt.py`

### 2.1 Input

`next_step(state, event, mode, cfg) -> Step`

- `state: TopicState` · สถานะของหัวข้อ**หลัง**บันทึก attempt ของ event นี้แล้ว (ผู้เรียกบันทึก attempt + BKT ก่อน แล้วค่อยเรียก):
  - `stage` (`probe` · `verify` · `practice` · `done` · `park` · null = ยังไม่เคยเริ่ม)
  - `stars`, `level` (จาก `bkt.level` ด้วย mode เดียวกับที่ส่งมา)
  - `skills: tuple[SkillState, ...]` ตามลำดับของ `topic_skills` · ต่อ skill: `id`, `exam_freq`, `independent_correct` (จำนวน independent correct รวมทุก session), `problems_today` (จำนวนโจทย์ของ skill นี้วันนี้ รวมข้อนี้)
  - `current_skill_id` (skill ของโจทย์ข้อล่าสุด · null ได้), `difficulty` (ของโจทย์ข้อล่าสุด · null ได้), `fail_streak` (`topic_progress.fail_streak` ก่อน event นี้)
- `event`: `Start(user_new: bool)` (เปิดหัวข้อ · `user_new` = ผู้ใช้บอกว่ายังไม่เคยเรียน ซึ่งผู้เรียกตัดสินเอง) หรือ `Answer(correct: bool, error_type: ErrorType | None, independent: bool)` (คำตอบสุดท้ายของโจทย์ · `correct` = `verdict == "correct"` เหมือน BKT · ขั้นที่ถูกแต่ยังไม่จบของ hint ladder ไม่ส่งมา)
- `mode` (จาก planner)

### 2.2 ค่าที่ใช้ร่วม

1. **skill ที่ต้องครอบคลุม** (TM-16, SM-12): skill ที่ `exam_freq > 0` (`done.require_exam_skills_covered`) · ถ้าไม่มี skill ไหนเคยออกสอบ ใช้ทุก skill (`done.require_all_skills_if_no_past_exam`)
2. **ครอบคลุมแล้ว** = `independent_correct ≥ done.min_independent_correct_per_skill`
3. **skill ถัดไป** (Probe, Practice · §2.5.4): skill ที่ต้องครอบคลุมแต่ยังไม่ครอบคลุม เรียง `exam_freq` มากไปน้อย (เท่ากัน → ลำดับใน `skills`) · ถ้าครอบคลุมหมดแล้ว (หัวข้อยังไม่ผ่านเพราะ mastery หรือ `d_max`): skill ที่ต้องครอบคลุมที่ `independent_correct` น้อยสุด (เท่ากัน → `exam_freq` มากไปน้อย → ลำดับ) · §10 ข้อ 5 · หัวข้อที่ไม่มี skill เลย → `skill_id = null` · **skill ของ Verify** = `current_skill_id` (null → skill ถัดไป · §10 ข้อ 7 D)
4. **เพดานความยาก** `cap` = `bkt.target_difficulty(stars, mode)` (null เมื่อหัวข้อถูกตัดใน mode นี้ → ใช้ `done.three_star_final_difficulty`)
5. **ความยาก** (§2.5.4 · ค่าใหม่ใน config §10 ข้อ 3):
   - Probe: `min(stages.probe_difficulty, cap)`
   - Practice ข้อแรก (ไม่มีข้อก่อนหน้า): `min(stages.practice_start_difficulty, cap)`
   - Practice หลังตอบถูก: skill ถัดไปเป็น skill เดิม (`current_skill_id`) หรือเคยทำถูกเองแล้ว (`independent_correct > 0`) → `min(difficulty + 1, cap)` ("ไล่ 2 → 3") · skill ใหม่ที่ยังไม่เคยทำถูกเอง → Practice ข้อแรก (§10 ข้อ 7 C)
   - Verify: `min(max(difficulty − stages.verify_difficulty_drop, 1), cap)` (ห้ามยากขึ้นและไม่เกินเพดาน · 1 = ขั้นต่ำของสเกลใน `problems.difficulty` · §10 ข้อ 7 D) · ไม่มีข้อก่อนหน้า → Practice ข้อแรก

### 2.3 กฎ (ข้อแรกที่ตรงชนะ)

**Start**

ก่อนข้อ 1: `level = passed` → **Done** ไม่มีโจทย์ (mode เปลี่ยนจนหัวข้อผ่านโดยไม่ต้องตอบ · §10 ข้อ 7 B)

1. `stage` null หรือ `park` (§10 ข้อ 6) และ `user_new = false` → **Probe** (TM-03): โจทย์ `purpose = probe`, skill ถัดไป, ความยาก Probe · `fail_streak = 0`
2. `stage` null หรือ `park` และ `user_new = true` → **Teach แบบเริ่มจากศูนย์** แล้ว Practice (§10 ข้อ 4): `teach.kind = introduce`, โจทย์ `purpose = practice` ความยาก Practice ข้อแรก · stage = `practice`
3. `stage = done` แต่ `level ≠ passed` (ผ่านแล้วกลับมาไม่ผ่าน เช่น mode เปลี่ยนระดับเป้า) → Practice เหมือน `practice` ในข้อ 4 (§10 ข้อ 7 B)
4. `stage` อื่น (กลับมาทำหัวข้อค้างใน session ใหม่ · ไม่มีโจทย์ค้าง): ให้โจทย์ของ stage เดิม · `probe` → Probe ใหม่ · `verify` → Verify skill เดิม ความยากเดิม · `practice` → Practice skill ถัดไป ความยากเดิม (`min(difficulty, cap)` · ไม่มี → Practice ข้อแรก)

**Answer**

5. `level = passed` → **Done** (TM-16): ไม่มีโจทย์ · `fail_streak = 0` · ผู้เรียกถาม planner หาหัวข้อถัดไป (ai-orchestration §2.2.4 "Done: ชม แล้วบอกหัวข้อถัดไป")
6. `correct` และ `independent` → `fail_streak = 0` · **Practice** (Probe ถูก = ข้ามการอธิบาย · TM-03 · Verify ถูก = กลับไปฝึก · TM-04): skill ถัดไป, ความยาก Practice หลังตอบถูก
7. `correct` แต่ไม่ `independent` (ทำถูกหลังเห็นวิธีทำ) → **Verify** skill เดิม (AM-08 · ยังไม่นับว่าทำเองได้) · `fail_streak` คงเดิม
8. ไม่ `correct` → `fail_streak + 1` แล้ว:
   1. `fail_streak` ใหม่ ≥ `park.max_fail_streak_per_skill` → **Park** `reason = fail_streak` (ไม่มีโจทย์ · ai-orchestration §2.2.4 "ผิดครั้งที่ 3 ใน skill เดียวกัน")
   2. นอกนั้น → **Teach** แล้ว **Verify** ใน turn เดียว (ตัวอย่าง directive §2.2.3 `do: explain_error, then: give_problem`): `teach.kind` ตาม error type (ตารางข้างล่าง), `teach.angle = fail_streak` ใหม่ (1 = อธิบายครั้งแรก · 2 ขึ้นไป = มุมใหม่ · AM-09), โจทย์ `purpose = verify` skill เดิม ความยาก Verify · stage = `verify`
9. **Park ตามจำนวนโจทย์ต่อวัน** (ตรวจหลังข้อ 1–8 ทุกครั้งที่ผลมีโจทย์ ทั้ง Start และ Answer · §10 ข้อ 7 A): skill ของโจทย์ที่จะให้มี `problems_today ≥ park.max_problems_per_skill_per_day` → **Park** `reason = too_many_today` แทน (Beck & Gong 2013 · ai-orchestration §2.2.4 "เกิน 10 ข้อในวันเดียวโดยยังไม่ผ่าน")

| `error_type` | `teach.kind` (ai-orchestration §2.2.4 "การสอนตาม error type") |
|---|---|
| `calculation`, `sign` | `point_fix` · ชี้จุดเดียว บอกค่าที่ถูก |
| `wrong_method` | `explain_method` · ทำไมวิธีนี้ใช้ไม่ได้ + สาธิตวิธีตามชีท |
| `concept` หรือ null | `explain_concept` (angle 2 ขึ้นไป = มุมใหม่ · AM-09) |
| `prerequisite` | `explain_prerequisite` (ผิดซ้ำจนถึง Park · push หัวข้อพื้นฐานเป็นงาน S6) |
| `no_answer` | `show_first_step` · ทำ step แรกให้ดูแล้วให้ทำต่อ |

### 2.4 Output

`Step(stage, teach, problem, fail_streak, park_reason)`

- `stage`: stage ของหัวข้อหลัง turn นี้ (ผู้เรียกเก็บใน `topic_progress.stage` และ `tutor_sessions.stage`) · Teach ไม่ค้างเป็น stage เพราะสอนแล้วให้ Verify ใน turn เดียว (ยกเว้นข้อ 2 ที่ไป `practice`)
- `teach: Teach(kind, angle, error_type) | None`
- `problem: ProblemSpec(skill_id, difficulty, purpose) | None` · ผู้เรียกส่งให้ `generate_problem` (source ของโจทย์ไม่อยู่ในงานนี้)
- `fail_streak`: ค่าใหม่ให้ผู้เรียกเก็บ
- `park_reason`: `fail_streak` · `too_many_today` · null

## 3. Inputs and outputs

| | Type / schema | ตัวอย่าง |
|---|---|---|
| Input | `TopicState(stage, stars, level, skills, current_skill_id, difficulty, fail_streak)` · `SkillState(id, exam_freq, independent_correct, problems_today)` · `Start(user_new)` หรือ `Answer(correct, error_type, independent)` · `mode` | ลิมิต ★★★ normal · skill A (`exam_freq` 2, ยังไม่ครอบคลุม), B (`exam_freq` 1) · stage `probe` ความยาก 2 · `Answer(correct=False, error_type="sign", independent=True)` · `fail_streak` 0 |
| Output | `Step(stage, teach, problem, fail_streak, park_reason)` | `Step("verify", Teach("point_fix", 1, "sign"), ProblemSpec(A, 2, "verify"), 1, None)` |

## 4. Acceptance criteria

ทุกข้อเป็น unit test ของ pure function · ค่าขอบอ่านจาก `LearningConfig` ของ test

**Probe (TM-03)**

- **AC-1 (TM03)** Given หัวข้อใหม่ (`stage` null) When `Start(user_new=false)` Then stage `probe` · โจทย์ `purpose = probe` · skill ที่ต้องครอบคลุมที่ `exam_freq` มากสุด · ความยาก `stages.probe_difficulty`
- **AC-2 (TM03)** Given หัวข้อใหม่ When `Start(user_new=true)` Then ไม่ probe: `teach.kind = introduce` · โจทย์ `purpose = practice` ความยาก `stages.practice_start_difficulty` · stage `practice`
- **AC-3 (TM03)** Given stage `probe` When ตอบถูก (independent) Then ไม่มี `teach` · stage `practice` · skill ถัดไปเป็น skill ใหม่ที่ยังไม่เคยทำถูก → ความยาก Practice ข้อแรก (§10 ข้อ 7 C)

**Teach → Verify (AM-08, AM-09, TM-04)**

- **AC-4 (AM08)** Given stage `probe` หรือ `practice` skill A ความยาก d When ตอบผิด Then `teach` ตาม error type · stage `verify` · โจทย์ skill A `purpose = verify` ความยาก `max(d − stages.verify_difficulty_drop, 1)` (ไม่ยากขึ้น)
- **AC-5 (AM08)** table-driven: `error_type` ทั้ง 6 ค่า + null → `teach.kind` ตามตาราง §2.3
- **AC-6 (AM09)** Given Verify ผิดอีก (`fail_streak` 1 → 2) Then `teach.angle = 2` (มุมใหม่) · ครั้งแรก `angle = 1`
- **AC-7 (TM04)** Given stage `verify` When ตอบถูก Then stage `practice` · `fail_streak = 0` · skill ถัดไป
- **AC-8 (AM08)** Given ตอบถูกแต่ไม่ independent Then stage `verify` skill เดิม · `fail_streak` ไม่เปลี่ยน

**Practice และ skill (SM-12, TM-16)**

- **AC-9 (SM12)** skill ถัดไป: ยังไม่ครอบคลุม เรียง `exam_freq` (เท่ากัน → ลำดับ) · skill ที่ `exam_freq = 0` ไม่ถูกเลือกเมื่อมี skill ที่เคยออกสอบ · ไม่มี skill ไหนออกสอบ → ทุก skill · หัวข้อไม่มี skill → `skill_id = null`
- **AC-10 (SM12)** ครอบคลุมหมดแล้วแต่ยังไม่ผ่าน → skill ที่ `independent_correct` น้อยสุด
- **AC-11 (TM16) boundary ของการครอบคลุม:** `independent_correct` = `min_independent_correct_per_skill − 1` → ยังไม่ครอบคลุม · = ค่านั้น → ครอบคลุม
- **AC-12 (TM16) เพดานความยาก:** Practice หลังตอบถูกที่ `cap` → ยังเป็น `cap` · ★ ใน normal (`cap` = `done.one_star_final_difficulty`) ไม่เกินค่านั้น
- **AC-13 (TM16)** Given `level = passed` (หลัง attempt) When ตอบถูก Then stage `done` · ไม่มีโจทย์ · `fail_streak = 0`

**Park (ai-orchestration §2.2.4 · learning-model §7)**

- **AC-14 (TM19) boundary ของ fail streak:** ผิดจน `fail_streak` = `park.max_fail_streak_per_skill − 1` → Teach + Verify · = ค่านั้น → stage `park` · `park_reason = fail_streak` · ไม่มีโจทย์
- **AC-15 (TM19) boundary ของโจทย์ต่อวัน:** skill ของโจทย์ถัดไปมี `problems_today` = `park.max_problems_per_skill_per_day − 1` → ได้โจทย์ · = ค่านั้น → `park` · `too_many_today` · ใช้ทั้งหลังตอบถูกและผิด

**Start ของหัวข้อที่เคยทำ**

- **AC-16 (TM04)** `Start` กับ stage `verify` → Verify skill เดิม ความยากเดิม · `practice` → Practice · `done` (ยังผ่านอยู่) → Done ไม่มีโจทย์ · `park` → Probe ใหม่ (§10 ข้อ 6)
- **AC-17 (TM16)** mode เปลี่ยน: `Start` กับ stage `practice` ที่ `level = passed` → Done ไม่มีโจทย์ · stage `done` ที่ `level ≠ passed` → Practice
- **AC-18 (TM19) boundary ของโจทย์ต่อวันตอน Start:** skill ของโจทย์แรกมี `problems_today` = `park.max_problems_per_skill_per_day − 1` → ได้โจทย์ · = ค่านั้น → `park` · `too_many_today` (รวมหัวข้อที่ Park ไว้แล้วเปิดใหม่วันเดียวกัน)
- **AC-19 (TM03)** Practice หลังตอบถูก: skill เดิม → `min(difficulty + 1, cap)` · skill ใหม่ที่ `independent_correct = 0` → `stages.practice_start_difficulty`
- **AC-20 (AM08)** Verify ไม่เกินเพดาน: ★★ ใน tight (`cap` = `done.tight_mode_two_star_difficulty`) ข้อก่อนหน้าความยาก `done.two_star_final_difficulty` ตอบผิด → ความยาก Verify ≤ `cap` · `Start` stage `verify` เหมือนกัน · `current_skill_id` null แต่หัวข้อมี skill → Verify ใช้ skill ถัดไป

**AC-boundary:** AC-11, AC-12, AC-14, AC-15, AC-18 · **AC-tenant:** ไม่อ่านหรือเขียนข้อมูล (pure function · ข้อมูลมาจาก repository ของห้องติวที่แยก tenant อยู่แล้ว)

## 5. Data changes

ไม่มี · คอลัมน์ที่ต้องใช้ตอนต่อเข้าห้องมีใน `0001` แล้ว: `topic_progress.stage`, `fail_streak`, `skill_coverage`, `parked_reason`, `parked_at` · `tutor_sessions.stage` · `problems.skill_id`, `difficulty`, `purpose` · `attempts.independent`

## 6. API / SSE changes

ไม่มี

## 7. AI calls

ไม่มี (code ล้วน · directive ส่งให้ prompt ตอนต่อเข้าห้อง)

## 8. Test plan

| Test | ระดับ | ครอบคลุม AC |
|---|---|---|
| `tests/unit/test_stage_machine.py` (table-driven · `LearningConfig` ของ test) | unit | AC-1 ถึง AC-20 |

## 9. Out of scope

- ต่อเข้าห้องติว: อ่าน/เขียน `topic_progress`, นับ `problems_today`, ส่ง `teach` + `problem` เข้า directive ของ prompt, ตัดสิน `user_new` จากข้อความ (PR ถัดไปหลัง 23 พ.ย.)
- Park ฝั่งกลับเข้า queue (`park.return_after_sessions`) และ push หัวข้อพื้นฐานเมื่อ error ล่าสุดเป็น `prerequisite` (TM-19 · S6) · ทวนตามรอบ (TM-17 · S6)
- source ของโจทย์ (ข้อสอบเก่าที่ความยาก 3 · ห้ามซ้ำ) · interleaving (Could)
- hint ladder ของเดโม่ (§10 ข้อ 1)

## 10. Open questions

ตัดสินแล้ว (Jam 2026-11-19): ข้อ 1 (ก) · ข้อ 2–6 ตามข้อเสนอ · ข้อ 7 (Jam 2026-11-22) ตามข้อเสนอ

1. **hint ladder ของเดโม่กับ Teach:** AM-07 และตาราง Teach (§2.2.4) ห้าม "ให้ hint แล้วให้ลองเอง" แต่เดโม่ในเครื่องมี hint ladder (`demo-room.md` §2 K · ข้อเสนอแก้ AM-07 ยังรอทีม)
   - (ก) **ข้อเสนอ:** stage machine ทำตาม AM-07 ที่เขียนไว้ (ผิด → อธิบายทันที → Verify) · hint ladder คงอยู่เฉพาะเดโม่ในเครื่อง ไม่อยู่ใน stage machine · ถ้าทีมรับข้อเสนอ AM-07 ค่อยใส่ ladder เป็นขั้นย่อยของ Teach ใน PR อื่น
   - (ข) ใส่ ladder ใน Teach เลย (ขัดกับ AM-07 ที่ยัง active)
2. **Park อยู่ในงานนี้แค่ไหน:** ข้อเสนอ: stage machine ตัดสิน**เข้า** Park (ค่าใน `park.*` มีแล้ว และ DoD ของ checklist ต้องรู้ว่าเมื่อไหร่หยุด) · การกลับเข้า queue และ push prerequisite เป็น S6 (TM-19)
3. **ค่าความยากของแต่ละ stage** (§2.5.4 เขียนเป็นตัวเลข แต่ยังไม่มีใน config): เพิ่มส่วนใหม่ใน `config/learning.yaml` (ไฟล์กลาง · บอกกลุ่มก่อน merge):
   ```yaml
   stages:                                # stage machine (ai-orchestration §2.2.4, §2.5.4)
     probe_difficulty: 2                  # [C] §2.5.4 · middle of the 1–3 scale: shows what the user knows without the exam level
     practice_start_difficulty: 2         # [C] §2.5.4 "Practice ไล่ 2 → 3"
     verify_difficulty_drop: 0            # [C] §2.5.4 "ระดับเดิมหรือต่ำลง 1" · 0 = same level (AM-08 "แบบเดียวกัน") · after Alpha: verify pass rate at the same level
   ```
   พร้อมแถวใน `learning-model.md` และ `StagesConfig` ใน `app/settings.py` · ข้อเสนอ `verify_difficulty_drop = 0` (โจทย์ "แบบเดียวกัน" ตาม AM-08)
4. **ผู้ใช้บอกว่ายังไม่เคยเรียน** (§2.2.4 "ให้ข้ามไป Teach"): Teach ปกติเริ่มจากคำตอบที่ผิด แต่กรณีนี้ยังไม่มีคำตอบ · ข้อเสนอ: `teach.kind = introduce` (สอนพื้นฐานของ skill แรกตามชีท) แล้วให้โจทย์ Practice ข้อแรก (`purpose = practice` · ไม่ใช่ verify เพราะยังไม่มีโจทย์ที่ผิดให้เทียบ)
5. **skill ถัดไปเมื่อครอบคลุมหมดแล้วแต่ยังไม่ผ่าน** (mastery ยังไม่ถึงหรือยังไม่เคยทำถูกที่ระดับเป้า · spec ระบบไม่ได้บอก): ข้อเสนอ: skill ที่ `independent_correct` น้อยสุด (ฝึกส่วนที่ทำน้อยสุด) → `exam_freq` → ลำดับ
6. **Start ของหัวข้อที่ Park ไว้:** planner ยังไม่รู้จัก Park (S6) จึงอาจส่งหัวข้อที่ Park มาอีก · ข้อเสนอ: เริ่มใหม่ด้วย Probe (`fail_streak = 0`) จนกว่า S6 จะทำกฎกลับเข้า queue
7. **ช่องโหว่ที่ self-review เจอ** (Jam 2026-11-22 · แก้ใน PR นี้): (A) เพดานโจทย์ต่อวันตรวจแค่ตอนตอบ หัวข้อที่ Park เพราะครบ 10 ข้อแล้วเปิดใหม่วันเดียวกันได้ Probe ของ skill เดิม (B) Start ไม่ดู `level` ทำให้หัวข้อที่ผ่านเพราะ mode เปลี่ยนยังได้โจทย์ และหัวข้อ `done` ที่กลับมาไม่ผ่านไม่ได้โจทย์อีกเลย (C) skill ใหม่ได้ความยาก +1 ต่อจาก skill ก่อน จึงเริ่มที่ระดับข้อสอบทั้งที่ยังไม่เคยทำ (D) Verify ไม่ถูกจำกัดด้วยเพดานเมื่อ mode ลดระดับเป้า และได้ `skill_id = null` เมื่อข้อก่อนหน้าไม่มี skill · แก้: §2.2 ข้อ 3, 5 · §2.3 ก่อนข้อ 1, ข้อ 3, ข้อ 9 · AC-3 · AC-17 ถึง AC-20

## 11. Spec changes needed

- §10 ข้อ 3: `config/learning.yaml` ส่วน `stages:` (ไฟล์กลาง) + `learning-model.md` แถวใหม่ + `app/settings.py` `StagesConfig` · บอกกลุ่มก่อน merge
- ai-orchestration §2.2.4: ไม่ต้องแก้ ถ้า §10 ข้อ 1 เลือก (ก)
- PR ต่อห้องติว: เขียนวิธีนับ `problems_today` ต่อ skill (จาก `attempts` ของวันนี้) และวิธีตัดสิน `user_new` ลง spec ของ PR นั้น
