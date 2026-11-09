# Feature: mastery ของหัวข้อด้วย BKT, ระดับ และความพร้อม

| | |
|---|---|
| Area | planner |
| Requirements | PM-02, PM-03, TM-15, TM-16 |
| Owner | Jam |
| Reviewer | Jam · Junior ดูย้อนหลัง (อยู่ใน `apps/api/`) |
| Status | approved 2026-11-09 (Jam · §10 ข้อ 1 (ข), ข้อ 2 ตามข้อเสนอ) |
| Related system spec | learning-model.md §1 (BKT), §4 (ระดับ, `mastery_eff`, Done), §5 (readiness) · `config/learning.yaml` → `bkt`, `levels`, `done`, `readiness` · ai-orchestration §2.2.4 "เงื่อนไข Done", §2.5.2 (mode) |

## 1. Context

ระบบต้องรู้ว่าผู้เรียนเข้าใจหัวข้อแค่ไหนจากผลตรวจคำตอบ (PM-02) เพื่อแสดงระดับและความพร้อม % ในการ์ดความคืบหน้า (TM-15, PM-03) และตัดสินว่าหัวข้อผ่านแล้ว (TM-16) · feature นี้คือ pure function ใน `apps/api/app/domain/bkt.py` ตาม learning-model §1, §4, §5 · ผู้เรียกแรกคือเดโม่ในเครื่อง (`specs/features/tutor/demo-room.md` §2 D) · การบันทึก `topic_progress` และ `attempts` ลง DB อยู่นอก feature นี้ (§9)

## 2. Behavior

ทุกค่าอ่านจาก `LearningConfig` (`bkt.*`, `done.*`, `readiness.*`) · ไม่มีตัวเลขในโค้ด

1. **อัปเดต mastery** `update_mastery(p, correct, cfg) -> float` ตามสูตร learning-model §1:
   - ถูก: `p' = p(1 − slip) / [p(1 − slip) + (1 − p)·guess]`
   - ผิด: `p' = p·slip / [p·slip + (1 − p)(1 − guess)]`
   - แล้ว `p_next = p' + (1 − p')·transit`
   - `correct` คือ `CheckResult.is_correct` (`correct_with_flaw` และ `incomplete` นับเป็นผิด · ai-orchestration §2.4.5)
2. **บันทึก attempt ของหัวข้อ** `record_attempt(progress, correct, difficulty, independent, cfg) -> TopicProgress`
   - `TopicProgress` = `mastery` (ค่า BKT ดิบ · เริ่มที่ `bkt.p_init`), `attempts` (จำนวน attempt ที่นับ), `d_max` (difficulty สูงสุดที่ทำถูกเอง · เริ่ม 0)
   - `independent = false` และ `bkt.count_only_independent = true` → คืนค่าเดิมทุก field (ไม่นับ · learning-model §1 "กฎ independent")
   - นอกนั้น: `mastery` อัปเดตตามข้อ 1 · `attempts + 1` · ถ้าถูก `d_max = max(d_max, difficulty)` · ผิดไม่ลด `d_max`
3. **ระดับเป้า** `target_difficulty(stars, mode, cfg) -> int | None` ตาราง learning-model §4: ★★★ → `done.three_star_final_difficulty` ทุก mode · ★★ → `done.two_star_final_difficulty` ใน normal และ final · `done.tight_mode_two_star_difficulty` ใน tight และ triage · ★ → `done.one_star_final_difficulty` ยกเว้น triage → `None` (ข้าม) · 0 ดาว → `None`
4. **mastery หลังเพดาน** `mastery_eff(mastery, d_max, d_target, cfg)`: `d_max ≥ d_target` → `mastery` · `d_max = d_target − 1` → `min(mastery, (bkt.weak_below + bkt.mastery_threshold) / 2)` · `d_max ≤ d_target − 2` → `min(mastery, bkt.weak_below)` · `d_target = None` → `mastery`
5. **ระดับ** `level(progress, d_target, skills_covered, cfg)`:
   - `attempts = 0` → `not_started`
   - ผ่าน = `skills_covered` และ `mastery_eff ≥ bkt.mastery_threshold` และ `d_target` ไม่ใช่ `None` และ `d_max ≥ d_target` → `passed`
   - `mastery_eff < bkt.weak_below` → `weak`
   - นอกนั้น → `developing`
   - `skills_covered` = ผู้เรียกบอก (ทุก skill ที่ต้องมี independent correct ≥ `done.min_independent_correct_per_skill` · learning-model §4 ข้อ 1) · feature นี้ไม่นับ skill เอง
6. **ความพร้อม** `readiness(topics, cfg) -> float` = `Σ(signal_r × mastery_eff) ÷ Σ signal_r` ของหัวข้อที่ดาว > 0 เมื่อ `readiness.exclude_zero_star` · `Σ signal_r = 0` หรือไม่มีหัวข้อ → `0.0` · หัวข้อที่ `attempts = 0` นับ `mastery_eff = 0` (§10 ข้อ 1 ตัดสินแล้ว)

## 3. Inputs and outputs

| | Type | ตัวอย่าง |
|---|---|---|
| Input | `p: float`, `correct: bool`, `cfg: BktConfig` | `0.30, True` |
| Output | `float` | `0.7098` |
| Input | `TopicProgress(mastery, attempts, d_max)` + `correct`, `difficulty 1–3`, `independent` | `TopicProgress(0.30, 0, 0), True, 3, True` |
| Output | `TopicProgress` | `TopicProgress(0.7098, 1, 3)` |
| Input (readiness) | `list[ReadinessTopic(stars, signal_r, mastery_eff)]` | `[(3, 1.0, 0.71), (2, 0.5, 0.30)]` |
| Output | `float` 0–1 | `(1.0·0.71 + 0.5·0.30) ÷ 1.5 = 0.573` |

## 4. Acceptance criteria

ค่าใน config ปัจจุบัน: `p_init 0.3`, `p_transit 0.15`, `p_guess 0.2`, `p_slip 0.1`, `mastery_threshold 0.95`, `weak_below 0.5` · test อ่านจาก config และคิดค่าที่คาดจากสูตรด้วย config ไม่พิมพ์ตัวเลข ยกเว้นตัวอย่างใน learning-model §1 ที่ใช้เทียบ (ต้องปัดตรงตามตาราง)

**BKT**
- **AC-1 (PM-02)** Given `p_init` When ถูก 1, 2, 3 ข้อติด Then 0.71, 0.93, 0.986 (ปัด 2–3 ตำแหน่งตามตาราง learning-model §1) · ถูกข้อ 3 ≥ `mastery_threshold` แต่ข้อ 2 ยังไม่ถึง
- **AC-2 (PM-02)** Given `p_init` When ผิด 1 ข้อ Then ≈ 0.19
- **AC-3 (PM-02)** mastery อยู่ใน (0, 1) เสมอ และถูกได้ค่ามากกว่าผิดจาก p เดียวกัน (parametrize p = 0.01, 0.5, 0.99)
- **AC-4 (PM-02)** `independent = false` → `TopicProgress` ไม่เปลี่ยน · `count_only_independent = false` ใน config fixture → นับ
- **AC-5 (TM-16)** ถูก difficulty 3 แล้วผิด difficulty 1 → `d_max` ยัง 3 · ผิดอย่างเดียวไม่เพิ่ม `d_max`

**ระดับเป้า เพดาน และระดับ**
- **AC-6 (TM-16)** `target_difficulty` ตามตาราง §2 ข้อ 3 ทุกคู่ดาว × mode (parametrize 4 mode × 4 ดาว) · ค่ามาจาก `done.*`
- **AC-7 (TM-16)** `mastery_eff` ตัวอย่าง learning-model §4 (★★★ normal): ถูก d1 ×3 → 0.5 · ถูก d2 → 0.725 · ถูก d3 → ค่าดิบ
- **AC-8 (TM-15)** `level`: ไม่มี attempt → `not_started` · `mastery_eff` = `weak_below` − ε → `weak`, = `weak_below` → `developing` · `mastery_eff` = `mastery_threshold` − ε → `developing`, = `mastery_threshold` พร้อม `d_max ≥ d_target` และ `skills_covered` → `passed` · ε = 1e-9
- **AC-9 (TM-16)** mastery ≥ `mastery_threshold` แต่ `skills_covered = false` → ไม่ `passed` · `d_target = None` (★ ใน triage) → ไม่ `passed`

**ความพร้อม**
- **AC-10 (PM-03)** ตัวอย่าง §3 → 0.573 (±1e-9 จากสูตร) · หัวข้อ 0 ดาวไม่นับ · ไม่มีหัวข้อหรือ `Σ signal_r = 0` → 0.0
- **AC-10b (PM-03)** หัวข้อที่ยังไม่มี attempt นับ 0 · ทุกหัวข้อยังไม่เริ่ม → 0.0

**ทั่วไป**
- **AC-pure** ไม่อ่าน DB, network, ไฟล์ · รับ `cfg` เข้ามา

## 5. Data changes

ไม่มีใน feature นี้ · ของจริงเก็บใน `topic_progress.mastery` และ `attempts` (`0001_init.sql`) โดยผู้เรียก

## 6. API / SSE changes

ไม่มี

## 7. AI calls

ไม่มี

## 8. Test plan

`apps/api/tests/unit/test_bkt.py` · AC-1 ถึง AC-10 ข้อละ 1 test (parametrize ตามที่เขียน) · ชื่อ `test_PM02_...`, `test_TM16_...`, `test_TM15_...`, `test_PM03_...`

## 9. Out of scope

- บันทึก `attempts`, `topic_progress` (Junior) · นับ skill coverage จาก `topic_skills` · spaced review (§3), Park (§7), planner และ mode (§6) · calibrate ด้วย pyBKT (§9)

## 10. Open questions

1. ~~**หัวข้อที่ยังไม่เริ่มในความพร้อม %**~~ **ตัดสินแล้ว** (Jam 2026-11-09): (ข) นับเป็น 0 · learning-model v1.4 §5 · ทางเลือกเดิม: learning-model §5 ไม่ได้บอก · ทางเลือก: (ก) ใช้ `mastery_eff` ของ `p_init` หลังเพดาน (`d_max = 0` → เพดาน `weak_below` หรือต่ำกว่า · ได้ `min(p_init, weak_below)` = 0.3) (ข) นับเป็น 0 · ข้อเสนอ: (ข) เพราะยังไม่มีหลักฐานว่าทำได้ และความพร้อมเริ่มที่ 0% อ่านง่ายกว่า 30% ทั้งที่ยังไม่ได้ทำสักข้อ
2. ~~**mode เริ่มต้น**~~ **ตัดสินแล้ว** (Jam 2026-11-09): ยังไม่มี planner (§2.5.2) · เดโม่ใช้ `normal` ตลอด

## 11. Spec changes needed

| ไฟล์ | แก้อะไร | เจ้าของ |
|---|---|---|
| `specs/system/learning-model.md` §5 | เขียนกฎของหัวข้อที่ยังไม่เริ่มตาม §10 ข้อ 1 | เสร็จแล้ว (v1.4 · PR #115) |
