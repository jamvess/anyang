# Feature: planner เลือกหัวข้อถัดไป เหตุผล และ mode

| | |
|---|---|
| Area | planner |
| Requirements | TM-01 (ระบบเลือกหัวข้อเองจาก importance, mastery และวันที่เหลือ) · TM-02 (เหตุผลสั้นๆ ไม่บอกแผนทั้งหมด) · TM-18 (mode normal / tight / triage / final จากเวลาที่ต้องใช้เทียบเวลาที่เหลือ · บอกเมื่อ mode เปลี่ยน) · SM-02 (ลำดับตาม prerequisite) |
| Owner | Jam |
| Reviewer | Jam · Junior ดูย้อนหลัง (`planner_decisions` เป็นของ Junior · §11) |
| Status | approved 2026-11-19 (Jam · §10 ข้อ 1 (ก), ข้อ 2–4 ตามข้อเสนอ) · แก้ 2026-11-19 หลัง self-review (Jam · §10 ข้อ 5) |
| Related system spec | ai-orchestration.md §2.5.1–2.5.3, §2.5.7 · learning-model.md §4 (ระดับ, ระดับเป้า), §6 (need, available, ratio) · `config/learning.yaml` → `planner.*`, `bkt.*`, `done.*`, `levels` · `bkt-mastery.md` (`level`, `target_difficulty`, `mastery_eff`) · `app/domain/room.py` `choose_topic` (กฎง่ายของ demo ที่ feature นี้มาแทน) |

## 1. Context

ห้องติวตอนนี้เลือกหัวข้อด้วยกฎง่ายของ demo (`choose_topic`: ดาวมากสุด → mastery ต่ำสุด → `order_index`) และล็อก mode เป็น `normal` (`room_problems.py` `MODE`) · ai-orchestration §2.5 ออกแบบ planner ที่เป็น code ล้วน: เลือก mode จากเวลาที่ต้องใช้เทียบเวลาที่เหลือ แล้วเรียง queue ด้วยกฎตามลำดับที่อธิบายได้ · feature นี้ทำ **ตัวตัดสินใจแบบ pure function** ใน `app/domain/planner.py` (ไม่มี I/O · ไม่มี LLM · CLAUDE.md ข้อ 1) · การต่อเข้าห้องติว (อ่านข้อมูลจาก DB, ส่งเหตุผลเข้าคำทัก, เก็บ mode) เป็น PR ถัดไปหลังส่งวิดีโอ 23 พ.ย. (§10 ข้อ 2)

## 2. Behavior

ทุกค่าอ่านจาก `LearningConfig` · ไม่มีตัวเลขในโค้ด · `level`, `target_difficulty`, `mastery_eff` ใช้ของ `app/domain/bkt.py` ตามเดิม

### 2.1 Input

`plan(topics, facts, previous_mode, cfg) -> PlannerDecision`

- `topics: Sequence[PlanTopic]` · ต่อหัวข้อ: `id`, `name`, `order_index` (ลำดับที่ผู้ใช้ยืนยัน · A6 เรียงตาม prerequisite แล้ว · SM-02), `stars` (0–3 · 0 = ตัดออก), `prereq_ids`, `skills_total` (จำนวนแถว `topic_skills` ของหัวข้อ), `skills_covered` (skill ที่มี independent correct ≥ `done.min_independent_correct_per_skill`), `level` (`not_started` · `weak` · `developing` · `passed`), `mastery_eff`
- `facts: PlanFacts` · `days_left` (วันที่เหลือก่อนสอบ · 0 = สอบวันนี้), `daily_minutes` (`exam_preps.daily_minutes` · null ได้), `minutes_per_problem` (ค่าเฉลี่ยของผู้ใช้จาก `attempts` · null ได้), `current_topic_id` (หัวข้อที่ session ก่อนทำค้างไว้ · null ได้)
- `previous_mode: Mode | None` · mode ที่บอกผู้ใช้ไปครั้งก่อน (null = ยังไม่เคย)

### 2.2 ขั้นที่ 1 · mode (TM-18 · learning-model §6)

1. `minutes_per_problem` null → `planner.default_minutes_per_problem` · `daily_minutes` null → `planner.default_daily_minutes`
2. `problems_per_skill` = จำนวนข้อที่คาดว่าต้องใช้ให้ mastery ถึง `bkt.mastery_threshold` คำนวณจาก `bkt.*` (`planner.problems_per_skill: bkt_simulation` · วิธีคำนวณ §10 ข้อ 1)
3. `need` = Σ ของหัวข้อที่ `stars ≥ 1` และ `level ≠ passed` ของ `max(skills_total − skills_covered, 1) × problems_per_skill × minutes_per_problem` (หัวข้อที่ยังไม่มี skill นับเป็น 1 skill)
4. `available` = `days_left × daily_minutes` · `ratio` = `need ÷ available` · `available = 0` → `ratio` = null ใน output และในข้อ 5 ถือว่าเกินทุกขอบเมื่อ `need > 0` (ไม่มีเวลาเลยแต่ยังมีงาน เช่น `daily_minutes = 0` · §10 ข้อ 5) หรือไม่เกินขอบไหนเมื่อ `need = 0`
5. mode ตามลำดับ (ข้อแรกที่ตรงชนะ):
   1. `days_left ≤ planner.final_mode_days_left` → `final`
   2. `days_left ≤ planner.triage_days_left` หรือ `ratio > planner.triage_ratio` → `triage`
   3. `ratio > planner.tight_ratio` → `tight`
   4. นอกนั้น → `normal`
6. `mode_changed` = `previous_mode` ไม่ null และ ≠ mode ใหม่ (ห้องติวบอกผู้ใช้ครั้งเดียวตอนเปิดห้อง · ai-orchestration §2.5.2 · การเก็บ mode เป็นของ Junior §11)

### 2.3 ขั้นที่ 2 · หัวข้อถัดไป (TM-01, SM-02 · ai-orchestration §2.5.3 ข้อ 2 และ 5)

1. **ผู้สมัคร** = หัวข้อที่ `stars ≥ 1` · แล้วกรองตาม mode:
   - `normal`: ทุกหัวข้อ
   - `tight`: ทุกหัวข้อ แต่ ★ ไปท้าย (เรียงใหม่: ★★ และ ★★★ ตาม `order_index` ก่อน แล้ว ★ ตาม `order_index`)
   - `triage`: ★★★ ทุกหัวข้อ และ ★★ ที่ `level` ∈ {`not_started`, `weak`} (§10 ข้อ 3) · ★ ไม่เข้า
   - `final`: ★★★ เท่านั้น (ไม่เปิดหัวข้อใหม่ · ai-orchestration §2.5.2)
   - **ผู้สมัครเป็นศูนย์** แต่มีหัวข้อ `stars ≥ 1` (mode ตัดทุกหัวข้อ เช่น final ที่ไม่มี ★★★ หรือ triage ที่เหลือแค่ ★ กับ ★★ `developing`) → ใช้ข้อ 2–6 ของ `normal` แทนทั้งหมด (`reason_code` ตาม normal) · §10 ข้อ 5
2. **ทำหัวข้อค้างให้จบก่อน:** `current_topic_id` เป็นผู้สมัคร และ `level ≠ passed` → หัวข้อนั้น · `reason_code = continue_topic`
3. **final:** หัวข้อ ★★★ ที่ `mastery_eff` ต่ำสุด (เท่ากัน → `order_index`) · `reason_code = final_review` · ไม่ข้ามหัวข้อที่ผ่านแล้ว (Final ทวนทุก ★★★)
4. **mode อื่น:** ผู้สมัครตัวแรกตามลำดับของข้อ 1 ที่ `level ≠ passed` · `reason_code` = `triage_focus` ถ้า mode เป็น `triage` · นอกนั้น `next_in_order`
5. **prerequisite ก่อน (SM-02):** หัวข้อที่ได้จากข้อ 4 มี prerequisite (`prereq_ids`) ที่ `stars ≥ 1` และยังไม่ผ่าน → เลือก prerequisite ตัวที่ `order_index` น้อยสุดแทน (ไล่ซ้ำจนเจอหัวข้อที่ prerequisite ผ่านหมดหรือไม่มี) · `reason_code = prerequisite_first` · `reason_topic_id` = หัวข้อที่ได้จากข้อ 4 · ใช้กับทุก mode ยกเว้น `final` และข้อ 2 (หัวข้อค้าง)
6. **ทุกผู้สมัครผ่านแล้ว** (mode อื่นที่ไม่ใช่ final): **ผู้สมัคร**ที่ `mastery_eff` ต่ำสุด (เท่ากัน → `order_index`) · `reason_code = all_passed` (เหมือนกฎของ demo · spaced review มาแทนใน S6) · เลือกจากผู้สมัครเท่านั้น ไม่ใช่ทุกหัวข้อ จึงไม่ได้หัวข้อที่ mode ตัด (§10 ข้อ 5)
7. **ไม่มีหัวข้อที่ `stars ≥ 1` เลย** → `topic_id = null` · `reason_code = no_topic` (ห้องติวเปิดแบบไม่มีโจทย์เหมือนเดิม)

### 2.4 Output

`PlannerDecision`: `mode`, `mode_changed`, `need_minutes`, `available_minutes`, `ratio` (null เมื่อ `available = 0`), `topic_id`, `reason_code` (`continue_topic` · `next_in_order` · `prerequisite_first` · `triage_focus` · `final_review` · `all_passed` · `no_topic`), `reason_topic_id` (หัวข้อที่ทำให้ต้องเรียน prerequisite · null ถ้าไม่ใช่ `prerequisite_first`)

- **เหตุผลที่ผู้ใช้เห็น (TM-02):** planner คืนแค่ `reason_code` + หัวข้อ · ห้องติวแปลงเป็น `focus` ของ `open_session` แล้ว LLM พูดเป็นประโยค (ai-orchestration §2.5.1 · "LLM แปลง reason_code เป็นประโยค") · planner ไม่คืน queue ทั้งหมด จึงไม่มีทางบอกแผนทั้งหมดล่วงหน้า
- `inputs` ทั้งหมดและ output เก็บใน `planner_decisions` (ai-orchestration §2.5.7) เป็นงานของห้องติว + ตารางของ Junior (§11)

## 3. Inputs and outputs

| | Type / schema | ตัวอย่าง |
|---|---|---|
| Input | `PlanTopic(id, name, order_index, stars, prereq_ids, skills_total, skills_covered, level, mastery_eff)` × n · `PlanFacts(days_left, daily_minutes, minutes_per_problem, current_topic_id)` · `previous_mode` | ลิมิต ★★★ `weak` 4 skill 1 ครอบคลุม · `days_left = 20`, `daily_minutes = null` |
| Output | `PlannerDecision(mode, mode_changed, need_minutes, available_minutes, ratio, topic_id, reason_code, reason_topic_id)` | หัวข้อเดียวตามตัวอย่าง input, `problems_per_skill` ≈ 7.8, นาทีต่อข้อ 4 (default), นาทีต่อวัน 45 (default): need = 3 × 7.8 × 4 ≈ 93.6 · available = 20 × 45 = 900 · `("normal", False, 93.6, 900, 0.104, <ลิมิต>, "next_in_order", None)` |

## 4. Acceptance criteria

ทุกข้อเป็น unit test ของ pure function · ค่าขอบทั้งหมดอ่านจาก `LearningConfig` ของ test (ไม่ hard-code) · `problems_per_skill` อ่านจากฟังก์ชันเดียวกับที่ planner ใช้

**mode (TM-18)**

- **AC-1 (TM18)** `need` = Σ ตามข้อ 2.2.3 · หัวข้อ ★0 และหัวข้อ `passed` ไม่นับ · หัวข้อที่ `skills_total = 0` นับ 1 skill · null ของ `minutes_per_problem` และ `daily_minutes` ใช้ค่า default จาก config
- **AC-2 (TM18) boundary ของ ratio** (table-driven · `days_left` มากพอไม่ให้เข้า triage ด้วยวัน): ratio = `tight_ratio − ε` → normal · = `tight_ratio` → normal · `+ ε` → tight · = `triage_ratio` → tight · `+ ε` → triage
- **AC-3 (TM18) boundary ของวัน:** `days_left` = `triage_days_left + 1` (ratio ต่ำ) → normal · = `triage_days_left` → triage · = `final_mode_days_left` → final · 0 → final
- **AC-4 (TM18)** `previous_mode` null → `mode_changed = false` · เท่ากับ mode ใหม่ → false · ต่างกัน → true
- **AC-5 (TM18)** `problems_per_skill` จาก `bkt.*` ปัจจุบัน: ค่าคงที่ทุกครั้งที่เรียก (deterministic) และอยู่ในช่วงที่ learning-model §6 รายงาน (§10 ข้อ 1)

**หัวข้อถัดไป (TM-01, SM-02)**

- **AC-6 (TM01)** normal: 3 หัวข้อ `order_index` 1–3 ไม่มีอันไหนผ่าน → หัวข้อ 1 · `next_in_order` · หัวข้อ 1 ผ่าน → หัวข้อ 2
- **AC-7 (TM01)** หัวข้อค้าง: `current_topic_id` = หัวข้อ 3 (ยังไม่ผ่าน) → หัวข้อ 3 · `continue_topic` · หัวข้อ 3 ผ่านแล้ว → ตามลำดับ · หัวข้อ 3 เป็น ★ ใน triage (ไม่ใช่ผู้สมัคร) → ไม่ทำต่อ
- **AC-8 (TM18)** tight: ★ `order_index` 1, ★★★ `order_index` 2 → ★★★ ก่อน · เหลือ ★ ตัวเดียวที่ยังไม่ผ่าน → ★
- **AC-9 (TM18)** triage: ★ ไม่ถูกเลือก · ★★ `developing` ไม่ถูกเลือก · ★★ `weak` และ `not_started` ถูกเลือก · `reason_code = triage_focus`
- **AC-10 (TM18)** final: เลือก ★★★ ที่ `mastery_eff` ต่ำสุด แม้ผ่านแล้ว · ★★ ไม่ถูกเลือกแม้ยังไม่ผ่าน · `final_review`
- **AC-11 (SM02)** หัวข้อถัดไปตามลำดับมี prerequisite ที่ยังไม่ผ่าน → prerequisite · `prerequisite_first` · `reason_topic_id` = หัวข้อเดิม · ไล่ 2 ชั้น (A → B → C) ได้ C · prerequisite ที่ ★0 ไม่นับ
- **AC-12 (TM01)** ทุกหัวข้อผ่าน (normal) → `mastery_eff` ต่ำสุด · `all_passed` · ไม่มีหัวข้อ ★ ≥ 1 → `topic_id = null` · `no_topic`
- **AC-13 (TM02)** output ไม่มีรายการหัวข้อหรือ queue (มีแค่หัวข้อเดียว + เหตุผล)
- **AC-14 (TM18)** ผู้สมัครเป็นศูนย์: final ที่มีแค่ ★★ กับ ★ (ยังไม่ผ่าน) → หัวข้อแรกตามลำดับ · `next_in_order` (ไม่ใช่ `all_passed`) · triage ที่มีแค่ ★ กับ ★★ `developing` → เหมือนกัน
- **AC-15 (TM18)** triage: ★★★ ผ่านหมด, ★★ `developing` กับ ★ ยังไม่ผ่าน (★ มี `mastery_eff` ต่ำสุด) → ★★★ ที่ `mastery_eff` ต่ำสุด · `all_passed` (ไม่ใช่ ★)
- **AC-16 (TM18)** `daily_minutes = 0`, `days_left` = `triage_days_left + 30`, มีหัวข้อที่ยังไม่ผ่าน → `triage` · `ratio` = null · ไม่มีหัวข้อที่ยังไม่ผ่าน → `normal`

**AC-boundary:** AC-2, AC-3, AC-16 · **AC-tenant:** ไม่อ่านหรือเขียนข้อมูล (pure function · ข้อมูลมาจาก repository ของห้องติวที่แยก tenant อยู่แล้ว)

## 5. Data changes

ไม่มีใน feature นี้ · `planner_decisions` (ai-orchestration §2.5.7) เป็นของ Junior (S5 "DB ของ planner") · ใช้ตอนต่อเข้าห้องติว (§10 ข้อ 2)

## 6. API / SSE changes

ไม่มี · การ์ดความคืบหน้าและคำทักใช้ช่องเดิม

## 7. AI calls

ไม่มี (code ล้วน · ai-orchestration §2.5.1)

## 8. Test plan

| Test | ระดับ | ครอบคลุม AC |
|---|---|---|
| `tests/unit/test_planner_mode.py` (table-driven · `LearningConfig` ของ test) | unit | AC-1 ถึง AC-5, AC-16 |
| `tests/unit/test_planner_queue.py` (table-driven) | unit | AC-6 ถึง AC-15 |

## 9. Out of scope

- ทบทวนตามรอบ (TM-17 · S6 · ai-orchestration §2.5.3 ข้อ 1 และ §2.5.5) · Park และ prerequisite ที่ถูก push จาก Park (TM-19 · S6 · §2.5.3 ข้อ 3–4)
- เลือกโจทย์ (skill, difficulty, ข้อสอบเก่า · §2.5.4) · stage machine (TM-03, TM-04 · S5 ข้อถัดไป)
- แผนวันนี้ (`plan_today` · §2.5.6) · user override ("อยากทำ…", "ข้ามเรื่องนี้" · ต้องมี intent router)
- การต่อเข้าห้องติว (§10 ข้อ 2) และตาราง `planner_decisions` (Junior)
- คำนวณ `minutes_per_problem` ของผู้ใช้จาก `attempts` (รับเป็น input · ห้องติวคำนวณตอนต่อ)

## 10. Open questions

ตัดสินแล้ว (Jam 2026-11-19): ข้อ 1 (ก) · ข้อ 2–4 ตามข้อเสนอ

1. **วิธีคำนวณ `problems_per_skill`** (`planner.problems_per_skill: bkt_simulation` · learning-model §6 รายงานจากการจำลอง 100,000 รอบ: เฉลี่ย 7.8 ข้อ, median 6, p90 15):
   - (ก) **ข้อเสนอ:** จำลองแบบ fix seed ตอนโหลด config (จำลองผู้เรียนตาม `bkt.*`: เริ่มรู้ด้วย `p_init`, เรียนรู้ทีละข้อด้วย `p_transit`, ตอบตาม `p_guess`/`p_slip`, นับข้อจน mastery ≥ `mastery_threshold`) แล้วใช้ **ค่าเฉลี่ย** · ได้ค่าเดิมทุกครั้ง · จำนวนรอบและ seed เป็นค่าคงที่ของการคำนวณ ไม่ใช่ threshold ของ learning model
   - (ข) คำนวณค่าคาดหวังแบบตรง (ไม่สุ่ม) · ซับซ้อนกว่า เพราะ mastery หลังแต่ละข้อขึ้นกับลำดับถูกผิดทั้งหมด
   - (ค) ใช้ median แทนค่าเฉลี่ย (ประเมินเวลาต่ำกว่า · mode ผ่อนกว่า)
2. **ต่อเข้าห้องติวเมื่อไหร่:** ข้อเสนอ: PR นี้ทำแค่ `app/domain/planner.py` + test · ห้องติวยังใช้ `choose_topic` · ต่อใน PR ถัดไปหลังส่งวิดีโอ 23 พ.ย. (ไม่แตะห้องที่ใช้อัดวิดีโอ) และหลังมีที่เก็บ mode ครั้งก่อน (Junior)
3. **triage เลือก ★★ "ที่อ่อน"** (ai-orchestration §2.5.2): ข้อเสนอ `level` ∈ {`not_started`, `weak`} · หัวข้อที่ยังไม่เริ่มมี mastery `p_init` ซึ่งต่ำกว่า `bkt.weak_below` อยู่แล้ว จึงนับว่าอ่อน · ★★ `developing` ไม่ทำใน triage
4. **ลำดับเปลี่ยนจากของ demo:** `choose_topic` เลือก "ดาวมากสุดก่อน" แต่ ai-orchestration §2.5.3 ให้ "ตามลำดับที่ตกลงกัน" (`order_index`) · spec นี้ทำตาม §2.5.3 · ผลคือหัวข้อแรกในห้องอาจเปลี่ยนเมื่อต่อเข้าห้องติว (ไม่กระทบ PR นี้เพราะยังไม่ต่อ)
5. **ช่องโหว่ที่ self-review เจอ** (Jam 2026-11-19 · เลือกแก้ใน PR นี้): (A) final ที่ไม่มี ★★★ ไม่มีกฎรองรับ และได้ `all_passed` ทั้งที่ยังไม่ผ่านอะไร (B) triage ที่ ★★★ ผ่านหมด ข้อ 6 เดิมเลือกจากทุกหัวข้อ จึงได้ ★ ที่ triage ข้าม (C) `daily_minutes = 0` ทำให้ `available = 0` ก่อนวันสอบ ข้อ 4 เดิมถือว่าเป็น final อยู่แล้ว จึงได้ normal ทั้งที่ไม่มีเวลา · แก้: §2.3 ข้อ 1 (ผู้สมัครเป็นศูนย์ → normal) · ข้อ 6 (เลือกจากผู้สมัคร) · §2.2 ข้อ 4 (`available = 0` กับ `need > 0` เกินทุกขอบ) · AC-14 ถึง AC-16

## 11. Spec changes needed

- ไม่แตะไฟล์กลาง · `config/learning.yaml` มีค่าครบแล้ว (`planner.*`)
- ถ้า §10 ข้อ 1 เลือก (ก): learning-model §6 เขียนว่า "จำลอง 100,000 รอบ" อยู่แล้ว · ค่าที่ใช้จะเท่ากับที่รายงาน (±การสุ่ม) · ไม่ต้องแก้
- Junior (S5 "DB ของ planner"): `planner_decisions` + เก็บ mode ครั้งก่อนของ prep (ใช้กับ `previous_mode` · AC-4)
- PR ต่อห้องติว (จาก self-review): (1) `level` และ `mastery_eff` ของ input ขึ้นกับ mode (`target_difficulty`: ★★ ผ่านที่ระดับต่ำกว่าใน tight/triage) · ห้องติวคำนวณด้วย `previous_mode` (null → `normal`) แล้วเขียนเรื่องนี้ลง spec ของ PR นั้น (2) `problems_per_skill` คำนวณครั้งแรกที่เรียกแล้วเก็บไว้ (~0.35 วินาที) · เรียกตอน startup ของ API เพื่อไม่ให้ request แรกของ instance ค้าง
