# Feature: ห้องติวบน DB · การ์ด + เลือกหัวข้อ + โจทย์ที่ SymPy ยืนยันเฉลยแล้ว

| | |
|---|---|
| Area | tutor |
| Requirements | TM-01 (กฎง่าย), TM-02, TM-03 (โจทย์แรกของหัวข้อเป็น probe), TM-15, AM-11, AM-13, TM-10, SA-06 |
| Owner | Jam |
| Reviewer | Jam · Junior ดูย้อนหลัง (repository ใน `app/db/room.py`) · May ดู §10 ข้อ 3 (การ์ดโจทย์ในประวัติ) |
| Status | draft 2026-11-13 (PR #131) |
| Related system spec | `room-sessions-db.md` (#123 · ห้องบน DB) · `demo-room.md` §2 C, F (ทักก่อน, tutor รู้โจทย์) · `ingestion.md` (หัวข้อมาจากไหน) · ai-orchestration §2.2.2–2.2.4, §2.4.6 · learning-model §4 (ระดับยากเป้า) · api.md v1.16 · `docs/team/sprint-checklists.md` ⭐ demo ขั้น 6 |

## 1. Context

demo end to end (23 พ.ย.) เข้าห้องติวหลัง login · ห้องที่มี token ตอนนี้ (#123) ทักด้วย template แล้วคุยได้อย่างเดียว ไม่มีการ์ด ไม่มีโจทย์ · ของที่มีในเดโม่ในเครื่อง (การ์ด, `open_session`, โจทย์) ทำงานเฉพาะตอนไม่มี token และใช้โจทย์ตายตัว 5 ข้อ · feature นี้ทำให้ห้องที่มี token เปิดด้วยการ์ดจาก DB → tutor ทักพร้อมบอกหัวข้อที่เลือกและเหตุผล → โจทย์ของหัวข้อนั้นที่ `generate_problem` สร้างและ SymPy ยืนยันเฉลยแล้ว (AM-11) เก็บใน `problems` · หัวข้อมาจาก ingestion (#130) · ตรวจคำตอบเป็นขั้น 7 · บันทึก mastery เป็นขั้น 8 (§9)

## 2. Behavior

### 2.1 หัวข้อที่ห้องใช้

1. หัวข้อของ prep = แถว `topics` ของ prep ที่ `status` เป็น `draft` หรือ `confirmed` (ไม่รวม `excluded`) เรียงตาม `order_index` · **ใช้ได้ทั้งก่อนและหลังยืนยัน scope** (การยืนยันเป็นงานของ Junior ขั้น 5 ยังไม่มี · §10 ข้อ 1)
2. ไม่มีหัวข้อเลย (ยังไม่ได้ ingest) → เปิดห้องแบบเดิมทุกอย่าง (`room-sessions-db.md` §2.4 · template · ไม่เรียก AI)

### 2.2 เปิดห้อง `POST /exam-preps/{id}/sessions` เมื่อมีหัวข้อ

ลำดับ SSE: `session` → `progress_card` → `token` ของ tutor (`open_session`) → `problem` → `done {message_ids}`

1. `session` ตามเดิม (insert `tutor_sessions` · #123)
2. **`progress_card` จาก DB (TM-15)** ส่งทันทีหลัง `session` (ก่อนสร้างโจทย์ ผู้ใช้จึงเห็นอะไรเร็ว):
   - `topics` = หัวข้อตาม §2.1 · `stars` = `importance` · `origin` ตามแถว · `review_due = false`
   - ระดับและความพร้อมคิดด้วย `domain/bkt.py` (`level`, `mastery_eff`, `readiness`) แบบเดียวกับ `demo-room.md` §2 D · ข้อมูลของหัวข้อจาก `topic_progress` ของผู้ใช้ · **ไม่มีแถว → `not_started`** (ความพร้อม 0 ตาม bkt-mastery §10 ข้อ 1) · ตอนนี้ยังไม่มีใครเขียน `topic_progress` (ขั้น 8 · §10 ข้อ 2) การ์ดจึงเป็น `not_started` ทุกหัวข้อ
   - `passed` = จำนวนหัวข้อ `passed` · `total` = จำนวนหัวข้อ · `days_left` = `exam_date − วันนี้ (Asia/Bangkok)` (create-exam-prep §2.3) · mode `normal` (ยังไม่มี planner)
3. **เลือกหัวข้อ (TM-01 แบบง่าย · pure function `choose_topic` ใน `app/domain/room.py`)** · ผู้สมัคร = หัวข้อที่ `importance ≥ 1` และระดับไม่ใช่ `passed` · เรียง: ดาวมากก่อน → mastery น้อยก่อน (ไม่มีแถว = `bkt.p_init`) → `order_index` น้อยก่อน · เอาอันแรก · ไม่มีผู้สมัคร (ทุกหัวข้อผ่านแล้ว) → หัวข้อที่ `importance ≥ 1` ที่ mastery น้อยสุด · ไม่มีหัวข้อ `importance ≥ 1` เลย → แบบไม่มีหัวข้อ (§2.1 ข้อ 2)
4. **เหตุผล (TM-02)** · ข้อความสั้นจาก code: `"{ชื่อ} · {ดาว} ดาว · {ระดับ}"` (ระดับเป็นภาษาไทยแบบการ์ด เช่น "ยังไม่เริ่ม") · ส่งให้ `open_session` ใน input `focus` · ไม่ส่งแผนทั้งหมด
5. **โจทย์ (§2.3)** · ได้โจทย์ → บันทึก `problems` แล้วจึงทัก · ไม่ได้ → ทักโดยไม่มีโจทย์ (§2.3 ข้อ 7)
6. **ทัก (TM-15 · ai-orchestration §2.2.2 directive `open_session`)** · `open_session/v2` = v1 + input `focus` (หัวข้อที่เลือกและเหตุผล · default `none` เพื่อให้ทางเดโม่ในเครื่องที่ส่ง 4 input ยังใช้ได้) · facts: `days_left`, `readiness` (%), `topics` (บรรทัดละ `{ชื่อ} · {ดาว} ดาว · {ระดับ}`), `problem` (ข้อความโจทย์ **ไม่มีเฉลย** · AM-13 · ไม่มีโจทย์ → `none`), `focus` · ล้มก่อน token แรก → token เป็นคำทัก template เดิมของ #123 · ล้มหลังมี token → หยุดข้อความนั้น · ทั้งสองกรณียังส่ง `problem` (ถ้ามี) และ `done` (`demo-room.md` §2 F ข้อ 5)
7. คำทักที่ส่งจริงบันทึกเป็นข้อความ `tutor` ตาม #123 แล้วส่ง id ใน `done`

### 2.3 สร้างโจทย์และยืนยันเฉลย (AM-11 · ai-orchestration §2.4.6)

1. **ใช้โจทย์ค้างก่อน:** มีแถว `problems` ของ prep นี้ (session ไหนก็ได้ของ prep) ที่ยังไม่จบ (`ended_at` ว่าง · เดิม "ยังไม่มี `attempts`" · เปลี่ยนใน `room-answers-db.md` §2.2 ข้อ 1 เพราะคำตอบผิดที่ได้ใบ้มี attempt แต่โจทย์ยังไม่จบ) และ `topic_id` เป็นหัวข้อที่เลือก → ใช้แถวล่าสุดนั้น ไม่สร้างใหม่ (เปิดห้องใหม่แล้วโจทย์เดิมยังรออยู่ · TM-13) · `problem_id` เดิม
2. **input ของ `generate_problem/v1`** (ทุกค่าเป็น string ใน data block):
   - `topic` = ชื่อหัวข้อ · `skills` = บรรทัดละ `s{n}: {ชื่อ skill}` ตามลำดับของ `topic_skills` ที่ไม่ `excluded`
   - `source_text` = ข้อความของ `chunks` ที่ช่วงหน้าทับกับ `topic_sources` ของหัวข้อ เรียงตามไฟล์และหน้า เอา `session.grounding_chunks` ก้อนแรก (learning.yaml · ไม่มี chunk → `none`) · โจทย์ต้องใช้วิธีและสัญลักษณ์ตามชีท (SM-11 · ai-orchestration §1.4)
   - `difficulty` = `target_difficulty(ดาว, "normal")` (learning-model §4 · ★★★ / ★★ = 3, ★ = 2) · `None` (หัวข้อถูกข้าม) ไม่เกิดเพราะ `importance ≥ 1`
   - `answer_formats` = `expression`, `factored`, `equation` (ที่ checker ตรวจได้ · `domain/checker.py`)
3. **output `GenerateProblemResult`:** `text` (โจทย์ภาษาไทยพร้อมสมการใน `$…$`) · `text_latex` (บรรทัดเดียวสำหรับการ์ด · ภาษาไทยอยู่ใน `\text{}`) · `expression` (นิพจน์ที่ SymPy คำนวณได้ของสิ่งที่โจทย์ถาม เช่น `\frac{d}{dx}(x^{2}\sin(x))`, `\lim_{x \to 2}\frac{x^2-4}{x-2}`, `x^{3}-x`, `x^{2}-5x+6=0`) · `answer_format` · `reference_answer` (LaTeX) · `solution_steps` (LaTeX ทีละขั้น · อย่างน้อย 1) · `skill` (`s{n}` หรือ null)
4. **ยืนยันด้วย SymPy (code):** ก่อนอื่น `expression` ต้องเป็นตัวโจทย์ ไม่ใช่คำตอบที่ model คิดมาแล้ว (`poses_a_problem` ใน `app/domain/room.py`): ตัดคำสั่ง LaTeX ออกแล้วต้องยังมีตัวแปร และต้องไม่ใช่ข้อความเดียวกับเฉลย · ไม่งั้น SymPy เช็คได้แค่เลขคณิต (เพิ่ม 13 พ.ย. จากรันจริง: `5 + 1` = `6`, `2(2)^{3}-…` = `-15`) · แล้ว `evaluate_lines(answer_format, reference_answer, [expression])` ของ SymPy service ต้อง `parsed`, ไม่ `timed_out` และ `final_equal = true` · `factored` ต้อง `final_in_form` ของเฉลยเป็น true ด้วย (`evaluate_lines("factored", reference, [reference])`) · ไม่ผ่าน (รวม parse ไม่ได้, AI ล้ม, schema ผิดหลัง retry ของ gateway) → สร้างใหม่ · รวมไม่เกิน `1 + checker.max_generate_retries` ครั้ง (learning.yaml)
5. ผ่าน → insert `problems` ด้วย JWT ของผู้ใช้ (RLS): `session_id` (session ใหม่), `topic_id`, `skill_id` (`s{n}` → id · ไม่รู้จัก → null), `source = 'generated'`, `text`, `reference_answer`, `solution_steps` (jsonb list), `answer_format`, `verified = true`, `difficulty` (ที่ขอ), `purpose` = `probe` ถ้าหัวข้อนี้ยังไม่มีแถว `problems` ใน prep เลย (TM-03: โจทย์แรกของหัวข้อวัดความรู้เดิม) ไม่งั้น `practice` · `problems` ไม่มีคอลัมน์ `text_latex` · โจทย์ใหม่ใช้ `text_latex` ของ model ใน event · โจทย์ที่ใช้ซ้ำ (ข้อ 1) แปลงจาก `text` ด้วย code (§10 ข้อ 4)
6. event `problem` = `{problem_id, text_latex, difficulty, purpose}` · ไม่มีเฉลย (api.md · AM-13)
7. **ไม่ได้โจทย์** (ครบรอบแล้วยังไม่ผ่าน หรือ insert ไม่ได้) → ไม่ส่ง `problem` · `open_session` ได้ `problem: none` · หลังคำทักส่ง `token` ข้อความ `config/messages.yaml` → `room.no_problem` (ไฟล์กลาง · เช่น "ตอนนี้เตรียมโจทย์ไม่ทัน ลองเปิดห้องใหม่อีกครั้งนะ") · log ทุกรอบที่ไม่ผ่านพร้อมเหตุผล (ไว้ calibrate `max_generate_retries` · learning.yaml บอกให้วัดตอนมี feature) · ทางสำรองแบบคลังโจทย์ (D3) อยู่ใน §10 ข้อ 5

### 2.4 ข้อความพิมพ์ในห้องที่มี token (demo-room §2 C บน DB · TM-10)

`tutor_reply` ได้ input `problem` = `text` ของโจทย์ค้างของ session (แถว `problems` ล่าสุดของ prep ของ session ที่ `ended_at` ว่าง) **ไม่มีเฉลย** · ไม่มี → `none` ตามเดิม · การตรวจคำตอบที่พิมพ์: `room-answers-db.md`

### 2.5 code ตัดสิน · AI พูด

AI สร้างโจทย์และพูด · code เลือกหัวข้อ, ระดับยาก, ตัดสินว่าเฉลยถูกด้วย SymPy, เลือก `purpose`, เขียน DB (CLAUDE.md ข้อ 1–2, 4)

## 3. Inputs and outputs

| | Type / schema | ตัวอย่าง |
|---|---|---|
| Input | prep ที่มี `topics` (จาก ingestion) · `topic_skills`, `topic_sources`, `chunks` · `topic_progress` ของผู้ใช้ (ถ้ามี) | MTH10101: 34 หัวข้อ · ลิมิต ★★★ |
| Output (SSE) | `session` → `progress_card` → `token`… → `problem` → `done` | `problem: {"problem_id": "…", "text_latex": "\\lim_{x \\to 2} \\frac{x^{2}-4}{x-2}", "difficulty": 3, "purpose": "probe"}` |
| Output (DB) | `problems` 1 แถว (`verified = true`) · `messages` คำทัก | |
| `GenerateProblemResult` | `{text, text_latex, expression, answer_format, reference_answer, solution_steps[], skill}` | `{"text": "หาค่า $\\lim_{x \\to 2} \\frac{x^2-4}{x-2}$", "expression": "\\lim_{x \\to 2}\\frac{x^{2}-4}{x-2}", "answer_format": "expression", "reference_answer": "4", "solution_steps": ["\\frac{(x-2)(x+2)}{x-2}", "= x+2", "= 4"], "skill": "s1"}` |

## 4. Acceptance criteria

fake provider · repository ปลอม (แถวที่ JWT ของผู้ใช้เห็น) · SymPy จริง · ข้อ "DB" เป็น integration บน Supabase ในเครื่อง

**เปิดห้อง**

- **AC-1 (TM-15, AM-11)** Given prep มี 3 หัวข้อ (★★★, ★★, ★ · ไม่มี `topic_progress`) When เปิดห้อง Then SSE `session` → `progress_card` → `token`… → `problem` → `done` · การ์ด: 3 หัวข้อเรียง `order_index` ทุกหัวข้อ `not_started`, `readiness` 0, `passed` 0, `total` 3, `days_left` ตามวันสอบ · `problems` 1 แถว `verified = true`, `source = generated`, `topic_id` = หัวข้อ ★★★, `purpose = probe`, `difficulty` = `target_difficulty(3)` · `problem.problem_id` = id ของแถว · event ไม่มีเฉลย
- **AC-2 (TM-01)** `choose_topic` (table-driven): ★★★ ก่อน ★★ · ดาวเท่ากัน mastery น้อยก่อน · เท่ากันอีก `order_index` น้อยก่อน · `importance` 0 และ `excluded` ไม่ถูกเลือก · `passed` ข้าม · ทุกหัวข้อ passed → mastery น้อยสุด · ไม่มีหัวข้อ `importance ≥ 1` → None
- **AC-3 (TM-02, AM-13)** input ของ `open_session` มี `focus` = `"ลิมิต · 3 ดาว · ยังไม่เริ่ม"`, `problem` = ข้อความโจทย์ · ไม่มี `reference_answer` และ `solution_steps` ของโจทย์ในทุก input ของ `open_session`
- **AC-4 (SM-11)** input ของ `generate_problem` มี `topic`, `skills` (`s1: …` ตามลำดับ · skill ที่ excluded ไม่มี), `difficulty`, `source_text` = ข้อความของ chunk ที่ทับหน้าของหัวข้อ ไม่เกิน `session.grounding_chunks` ก้อน · chunk ของหน้าอื่นไม่อยู่
- **AC-5 (AM-11)** รอบแรกเฉลยผิด (`expression` ไม่เท่า `reference_answer`) · รอบสองถูก → `generate_problem` 2 ครั้ง · `problems` มีแค่ของรอบสอง
- **AC-boundary (AM-11)** ไม่ผ่านทุกรอบ → เรียก `1 + max_generate_retries` ครั้งพอดี (config ทดสอบ: ค่า 0 → 1 ครั้ง · ค่า 2 → 3 ครั้ง) · ไม่มี `problem` · มี token `room.no_problem` หลังคำทัก · ไม่มีแถว `problems` · `open_session` ได้ `problem: none`
- **AC-6 (AM-11)** `factored` ที่เฉลยยังแยกไม่สุด (`x(x^{2}-1)`) → ไม่ผ่าน · `expression` parse ไม่ได้ → ไม่ผ่าน · AI ล้ม → ไม่ผ่าน (นับรอบ)
- **AC-14 (AM-11 · เพิ่ม 13 พ.ย.)** `expression` ที่เป็นคำตอบคิดมาแล้ว (`5 + 1` = `6`, ตัวเลขล้วน, เท่ากับเฉลย, มีแค่คำสั่ง LaTeX ไม่มีตัวแปร) → ไม่ผ่าน นับเป็น 1 รอบ · `\lim_{x…}`, `\frac{d}{dx}(…)`, `x^{3}-x` → ผ่านกฎนี้
- **AC-7** `skill` = `s9` (ไม่มี) หรือ null → `skill_id` null · ยังใช้โจทย์ได้
- **AC-8 (TM-13)** prep มีโจทย์ค้าง (`ended_at` ว่าง) ของหัวข้อที่เลือกจาก session ก่อน → ไม่เรียก `generate_problem` · `problem.problem_id` = แถวเดิม · ไม่มีแถวใหม่
- **AC-9 (TM-03)** หัวข้อที่เคยมีโจทย์ใน prep แล้ว (มี attempt) → โจทย์ใหม่ `purpose = practice`
- **AC-10** prep ไม่มีหัวข้อ → เหมือน #123 ทุกอย่าง (`session` → `token` template → `done` · ไม่เรียก AI · ไม่มี `progress_card` / `problem`)
- **AC-11** `open_session` ล้มก่อน token → token template ของ #123 · ยังมี `progress_card`, `problem`, `done`
- **AC-12** insert `problems` ไม่ได้ (DB ล่ม) → เหมือนไม่ได้โจทย์ (AC-boundary) · ไม่ส่ง `problem` ที่ไม่มีในตาราง

**ข้อความพิมพ์**

- **AC-13 (TM-10, AM-13)** session มีโจทย์ค้าง → `tutor_reply` ได้ `problem` = `text` ของโจทย์ · ไม่มีเฉลย · ไม่มีโจทย์ → `none`

**แยก tenant**

- **AC-tenant (SA-06 · DB)** A เปิดห้อง → แถว `problems` มี `tenant_id` ของ A · B query `problems` ด้วย JWT ของตัวเองได้ 0 แถว · B เปิดห้องของ prep A → `404`

## 5. Data changes

ไม่มี migration · ใช้ `problems` (insert), `topics`, `topic_skills`, `topic_sources`, `chunks`, `topic_progress`, `attempts` (อ่าน) ที่มีแล้ว · RLS เดิม (`tenant_rows` / `owner_rows`)

## 6. API / SSE changes

| Endpoint / event | Request | Response |
|---|---|---|
| `POST /exam-preps/{id}/sessions` (มี token) | ไม่เปลี่ยน | prep มีหัวข้อ → เพิ่ม `progress_card` และ `problem` ในลำดับ §2.2 (api.md v1.15 เขียนว่ายังไม่ส่งจนกว่ามี scope ที่ยืนยัน · แก้เป็น "จนกว่ามีหัวข้อ" · ไฟล์กลาง · §11) · event เดิมทั้งหมด ไม่มี event ใหม่ |
| `POST /sessions/{id}/messages` (text, มี token) | ไม่เปลี่ยน | ไม่เปลี่ยน · `tutor_reply` รู้โจทย์ค้าง (§2.4) |

## 7. AI calls

| Purpose | Tier | Output schema | Prompt file |
|---|---|---|---|
| `generate_problem` (**prompt ใหม่**) | mid | `GenerateProblemResult` | `prompts/generate_problem/v1.md` (input `topic`, `skills`, `source_text`, `difficulty`, `answer_formats`) · `config/ai.yaml` มีแถวแล้ว (`max_tokens: 800`, ไม่ตั้ง `thinking`) · เสนอ `max_tokens` 2000 + `thinking: low` (§11) |
| `open_session` | main | free text | `prompts/open_session/v2.md` (v1 + `focus` · `defaults: {focus: none}`) |
| `tutor_reply` | main | free text | v2 เดิม · ได้ `problem` จาก DB |

## 8. Test plan

| Test | ระดับ | ครอบคลุม AC |
|---|---|---|
| `tests/unit/test_room_problems.py` (domain `choose_topic`, เหตุผล, การ์ด) | unit (pure) | AC-2, AC-3 (ข้อความเหตุผล) |
| `tests/unit/test_room_problems_api.py` (FakeRoomRepo แบบ #123 + fake provider + SymPy จริง) | unit | AC-1, AC-3–AC-13 |
| `tests/integration/test_room_problems_db.py` (Supabase ในเครื่อง · prep + หัวข้อ seed ด้วย service role) | integration | AC-tenant, AC-1 (แถวจริง) |
| รันจริงบน Vertex: สร้างโจทย์ของหัวข้อ MTH10101 นับ % ที่ SymPy ยืนยันในรอบที่ 1, 2, 3 | eval (มือ · ขั้น 4 ของ worklog) | calibrate `max_generate_retries` |

**ผลรันจริงบน Vertex (13 พ.ย. · ขั้น 4 ของ worklog · `generate_problem` กับ 34 หัวข้อของ MTH10101 จาก ingestion · ผลอยู่ใน `poc/P3/results/apps-api-ingestion/generate_problem.json`):** SymPy ยืนยันผ่านในรอบที่ 1 = 62% · ภายใน 2 รอบ = 68% · ภายใน 3 รอบ (`1 + max_generate_retries`) = 24/34 = **71%** · รอบแรกของการวัดพบ 4 หัวข้อที่ `expression` เป็นคำตอบคิดมาแล้ว (`5 + 1` = `6`) จึงเพิ่มกฎ `poses_a_problem` (§2.3 ข้อ 4 · AC-14) และแก้ prompt (ห้ามหาค่า ณ จุดแบบ `\left.…\right|`, ห้าม `y` / หลายตัวแปร / `f'(c)`) · รอบสองไม่มีหัวข้อที่ผ่านแบบนั้นแล้ว · หัวข้อหลักของ demo (ลิมิต, อนุพันธ์ทุกแบบพื้นฐาน, รูปแบบไม่กำหนด, เส้นกำกับ) ผ่านรอบแรกทุกหัวข้อ · ที่ไม่ผ่าน 10 หัวข้อ: SymPy service อ่านไม่ได้ (อนุพันธ์อันดับสูง `\frac{d^{n}}{dx^{n}}`, สมการที่มี `\frac{d^2}{dx^2}(…) = 0`, `\max`) หรือโจทย์ประยุกต์ที่ model แทนตัวเลขก่อน (อัตราสัมพัทธ์, ค่าประมาณ) · `max_generate_retries` คง 2 (รอบ 2–3 เพิ่ม 6% และ 3%) · **Jam รับผลนี้สำหรับ demo 13 พ.ย.**

## 9. Out of scope

- ตรวจคำตอบในทางที่มี token (ขั้น 7) · บันทึก `attempts`, `topic_progress` และ BKT จริง (ขั้น 8) · จบ session (ขั้น 9)
- planner เต็ม (mode, ทบทวน, Park · TM-18, TM-17, TM-19 · S5–S6) · stage machine (TM-04 · S5) · โจทย์จากข้อสอบเก่า (`source = past_exam`)
- โจทย์แบบ `numeric`, `solution_set`, `short_text`, `sql` (checker ยังไม่รองรับ)
- การ์ดโจทย์ในประวัติแชทเมื่อโหลดห้องใหม่ (§10 ข้อ 3)

## 10. Open questions

1. **(Junior) หัวข้อก่อนยืนยัน scope:** ข้อเสนอใช้ `topics` ที่ไม่ `excluded` ทั้ง `draft` และ `confirmed` · ทำให้ demo ไม่ต้องรอขั้น 5 · หลังมีการยืนยัน session ใหม่ผูก `scope_version_id` ตามกฎใน data-model.md อยู่แล้ว · หัวข้อหลังยืนยันเป็น `confirmed` จึงยังอยู่ในเงื่อนไข
2. **(Junior · ขั้น 8) `topic_progress` ไม่มี `d_max`** (ระดับยากสูงสุดที่ทำถูกเอง · `mastery_eff` ของ learning-model §4 ต้องใช้) · feature นี้ไม่ต้องใช้เพราะยังไม่มีแถว · ขั้น 8 ต้องเพิ่มคอลัมน์ (migration) ก่อนเขียนแถวแรก
3. **(May) การ์ดโจทย์ในประวัติ:** `GET /sessions/{id}` คืนแค่ข้อความ · การ์ดโจทย์อยู่ใน SSE เท่านั้น · รีเฟรชหน้าแล้วการ์ดหาย (แต่เปิดห้องใหม่ได้โจทย์เดิม · AC-8) · ข้อเสนอ: บันทึกเป็น `messages` `role = "card"`, `card = {"problem": {problem_id, text_latex, difficulty, purpose}}` แล้วหน้าเว็บแสดงการ์ดโจทย์จาก `card.problem` · ตอนนี้หน้าเว็บอ่าน `card` ของประวัติเป็นการ์ดความคืบหน้า จึงยังไม่บันทึกใน feature นี้
4. **`problems` ไม่มีคอลัมน์ `text_latex`:** โจทย์ที่ใช้ซ้ำ (AC-8) ต้องมี `text_latex` สำหรับการ์ด · ข้อเสนอ: เก็บใน `solution_steps` ไม่ได้ (ปนกับเฉลย) · ให้ใช้ `text` (มี `$…$`) แปลงเป็น `text_latex` ด้วย code: ส่วนนอก `$` ห่อด้วย `\text{}` · ทางอื่นคือ migration เพิ่มคอลัมน์ (Junior) · ข้อเสนอ: แปลงด้วย code ไปก่อน
6. **(หลัง demo) SymPy service อ่านอนุพันธ์อันดับสูงและสมการของอนุพันธ์:** สาเหตุหลักของหัวข้อที่สร้างโจทย์ไม่ผ่าน (§8 ผลรันจริง) · แก้ใน `app/math/sympy_service.py` (`sympy-service.md`)
5. **(Jam · D3 · หลัง demo) คลังโจทย์สำรอง:** ผลรันจริง 71% (< 80%) · ทำสำหรับหัวข้อประยุกต์ที่ model แทนตัวเลขก่อน · ถ้าขั้น 4 พบว่า SymPy ยืนยันผ่านน้อย (เช่น < 80% ภายใน 3 รอบ) ค่อยทำคลังโจทย์ที่เขียนไว้ต่อชนิดหัวข้อ · ตอนนี้ไม่ได้โจทย์ → ข้อความ `room.no_problem`

## 11. Spec changes needed

| ไฟล์ | แก้อะไร | ใคร |
|---|---|---|
| `specs/system/api.md` (ไฟล์กลาง) | `POST /exam-preps/{id}/sessions` มี token: ส่ง `progress_card` + `problem` เมื่อ prep มีหัวข้อ (ไม่ต้องรอยืนยัน scope · §10 ข้อ 1) | Jam · PR นี้ · Junior ดูย้อนหลัง |
| `config/ai.yaml` (ไฟล์กลาง) | `generate_problem`: `max_tokens` 800 → 2000, `thinking: low` [C] (Gemini 3 นับ thinking ใน `max_tokens` · ai-orchestration §2.3.7) · `open_session.prompt: v2` | Jam · PR นี้ |
| `config/messages.yaml` (ไฟล์กลาง) | `room.no_problem` | Jam · PR นี้ · May ดูถ้อยคำ |
| `prompts/generate_problem/v1.md`, `prompts/open_session/v2.md` | ใหม่ | Jam · PR นี้ |
| `room-sessions-db.md` §2.4 ข้อ 4 | ชี้มาที่ spec นี้เมื่อ prep มีหัวข้อ | Jam · PR นี้ |
