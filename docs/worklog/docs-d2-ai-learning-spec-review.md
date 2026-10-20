# ตรวจ ai-orchestration.md และ learning-model.md ให้ครบ (D2)

| | |
|---|---|
| Owner | Jam |
| Branch | `docs/d2-ai-learning-spec-review` |
| Checklist item | ตรวจ `specs/system/ai-orchestration.md` และ `learning-model.md` ใน repo ให้ครบ (D2) |
| Status | in progress · 2026-10-20 |

## Plan

- [x] 1. 🤖 ตรวจแบบไล่เทียบอัตโนมัติ: (ก) key ของ `config/learning.yaml` ที่ spec อ้าง มีจริงไหม และ key ที่ไม่มี spec อ้างเลย (ข) AI purpose ใน §3.1 ตรงกับ `config/ai.yaml` และโฟลเดอร์ใน `prompts/` ไหม (ค) requirement ID ที่ spec อ้าง มีใน `requirements.md` ไหม และ requirement AI-/TM-/AM- ที่ยังไม่มี spec ส่วนไหนรองรับ (ง) ตาราง §3.2 ตรงกับ `data-model.md` และ `supabase/migrations/0001_init.sql` ไหม (จ) SSE events §3.3 ตรงกับ `api.md` ไหม (ฉ) ตัวเลขใน spec ที่ไม่ได้มาจาก `learning.yaml` (magic number)
- [x] 2. 🤖 อ่านทั้งสองไฟล์ทีละ section หา: ข้อความที่ขัดกันเอง, ลำดับเลข section ที่สลับ (2.3 มาก่อน 2.2, 2.1 อยู่หลัง 2.5), ข้อความที่อ้างภาพใน .docx (9 จุด) ซึ่งไม่มีใน repo, สิ่งที่ PoC P1/P3 เจอแล้วแต่ spec ยังไม่เขียน
- [x] 3. 🤖 รวบรวมเป็นตาราง findings ใน PR description: จุด · ปัญหา · ข้อเสนอ · ไฟล์ของใคร
- [x] 4. 🙋 Jam ตัดสินทีละข้อ: แก้เลย / ไม่แก้ / เลื่อนไปทำหลังผล PoC (ข้อ S4 "อัปเดต threshold ตามผล P1 P2 P3") · ตอบเป็นเลขข้อ เช่น "1 แก้, 2 เลื่อน"
- [ ] 5. 🤖 แก้ตามที่ Jam ตัดสินใน `ai-orchestration.md` และ `learning-model.md` (ไฟล์ของ Jam) · ถ้าต้องแก้ไฟล์ของคนอื่นหรือไฟล์กลาง (`requirements.md`, `api.md`, `config/ai.yaml`, `data-model.md`) จะถามก่อนทุกครั้ง
- [ ] 6. 🤖 ติ๊ก checklist ใน `docs/team/sprint-checklists.md` แล้ว `/work-done`

## Definition of done

- ทุก finding มีคำตัดสิน (แก้ / ไม่แก้ / เลื่อน พร้อมเหตุผล)
- ข้อที่ตัดสินว่าแก้ ถูกแก้แล้วใน PR นี้ · ข้อที่เลื่อนเขียนไว้ว่าจะทำตอนไหน
- การอ้างอิงข้ามไฟล์ (config key, purpose, requirement ID, table, SSE event) ตรงกันหมด หรือมีเหตุผลที่ยังไม่ตรง
- checklist ข้อนี้ติ๊กแล้ว

## Decisions

- 2026-10-20 · เลือกทำข้อนี้ระหว่างรอโควตา free tier (P1/P3 รันได้หลัง 14:00 น.) · งานนี้ไม่ต้องใช้โควตา
- 2026-10-20 · (Jam เลือกตามคำแนะนำ) findings: แก้ F1 F2 F3 F4 F6 F8 F9 F10 F11 F13 F14 F16 ใน PR นี้ · เลื่อน F5 (mermaid ใน S4, ยังไม่ใส่ path ของ .docx), F12 (ตอนได้ report P1), F15 (ตอนทำ ingest จริง) · ขั้น 5 แบ่งเป็น 5a แก้ข้อเล็ก และ 5b ร่างตาราง requirement → section (F6)

## Findings (ร่าง · รวมเป็นตารางใน PR ตอนขั้น 3)

ขั้น 1 เทียบกับ `ai-orchestration.md` ฉบับใน `poc/P3` (ใหม่กว่า `main`) · script อยู่ใน scratchpad ของ session 2026-10-20 (`d2_check.py`)

ตรงกันแล้ว (ไม่ต้องแก้): purpose 23 ตัวใน §3.1 = `config/ai.yaml` · SSE event 9 ตัวใน §3.3 มีใน `api.md` ครบ · ทุก key ใน `learning.yaml` มีอธิบายใน `learning-model.md` (เขียนเป็นค่า ไม่ได้เขียนชื่อ key)

- F1 · §2.1.3 และ pseudocode §2.1.5 เขียนตัวเลขตรงๆ (quota 1/2/3, หารครึ่ง, `turns_since_buddy < 4`, `fail_streak ≥ 2`) โดยไม่อ้างชื่อ key `buddy.*` · ค่าตรงกับ config แต่ pseudocode นี้คือ "feature spec สำหรับ SDD" คนที่เขียนโค้ดตามจะ hard-code · §2.5.7 ก็เขียน 0.8 / 1.2 / ≤ 3 วัน แบบเดียวกัน
- F2 · `OI-04` (embedding) ถูกอ้าง 2 จุด (§2.10, §3.6) แต่ไม่มีรายการ OI ใน repo
- F3 · §3.2 มีตาราง `golden_answers` แต่ไม่มีใน migration และ `data-model.md` · golden set จริงเก็บเป็นไฟล์ใน `evals/`
- F4 · migration มีตาราง `profiles` แต่ §3.2 ไม่มี
- F5 · มี 9 จุดที่เขียนว่า "ดูภาพในไฟล์ AI Orchestration Design .docx" แต่ไม่มีภาพใน repo
- F6 · spec อ้าง requirement ID น้อย: AI-01..AI-08 อ้างแค่ AI-05 ทั้งที่ §2.9–2.11 ทำตาม AI-01..04, 06..08 · TM-, AM-, SM-, PM- ที่ active และไม่ถูกอ้างเลยมี 27 ข้อ · ทำให้ไล่ trace จาก requirement ไป spec ไม่ได้
- F7 · requirement ที่ status = changed และ spec อ้างถึง: TM-05, TM-07, TM-11, AM-02, SA-02 · **ขั้น 2: ตรงกันหมดแล้ว** (2.1.3–2.1.7, 2.2.5, 2.2.2, 3.4) ไม่ต้องแก้

ขั้น 2 (อ่านทีละ section · ตรวจตัวอย่างตัวเลขด้วย script แล้ว: BKT 0.30→0.71→0.93→0.986, ผิดทันที 0.19 · ตาราง spaced review ทั้ง 4 แถว ถูกหมด):

- ~~ลำดับ section สลับ~~ ไม่ใช่ปัญหา: §1.1 บรรทัด 22 บอกว่าตั้งใจเรียงตามการไหลของข้อมูล และใช้รหัส flow ตามที่อาจารย์กำหนด
- F8 · §2.2.4 ตาราง intent: `off_topic` / `emotion` อ้าง "(2.1.8)" แต่ข้อยกเว้นนอกเรื่องอยู่ที่ §2.1.7
- F9 · §3.1 T1 `route_intent` เขียนว่า "intent (8 ประเภท)" แต่ §2.2.4 มี 9 (answer, question_on_topic, question_off_scope, command, dispute, teach_back, off_topic, emotion, distress)
- F10 · §2.10 ตาราง tier ขาด `vision_extract_pages` (vision), `persona_preview` และ `latex_to_speech` (small) ซึ่งมีใน §3.1 และ `ai.yaml`
- F11 · ขนาด golden set ของ checker: §2.4.8 เขียน "ประมาณ 100 คำตอบ" แต่ `specs/poc/README.md` P2 และ checklist S3 เขียน 50
- F12 · §3.6 แถว P1 เขียน "50 รูป, เทียบ Gemini / Claude / Mathpix" แต่ทำจริง 30 รูป และใช้แค่ Gemini free tier 2 รุ่น (Jam ตัดสิน 19 ต.ค.)
- F13 · spaced review (`learning-model.md` §3, ai-orch §2.5.5): `round()` ของ Python ปัดครึ่งไปเลขคู่ (`round(2.5) = 2`) แต่ตัวอย่างใน spec ใช้ปัดครึ่งขึ้น (2.5→3) · และไม่ได้บอกว่า `days_left` นับ ณ วันไหน (ตัวอย่างถูกเมื่อนับ ณ วันที่ตั้งรอบถัดไป ถ้านับ ณ วันที่ผ่าน แถว 30 วันจะได้ 1, 4, 10)
- F14 · ชื่อ column: §2.2.6 `tutor_sessions.scope_version` แต่ migration ใช้ `scope_version_id` · §2.5.7 มี `topic_progress.parked_at` แต่ตาราง §2.2.6 ไม่มี (migration มี)
- F15 · §2.3.3 เกณฑ์ไฟล์สแกน "ตัวอักษรไทย < 30%" จาก PoC P3 ยังไม่มี key ใน config · อยู่ในส่วนที่ PR #15 แก้
- F16 · ตัวเลขที่ไม่มี key ใน config: running summary "ทุก 8 turns" (§2.2.7, §2.6 · ใช้ค่าเดียวกับ `context_recent_turns` หรือแยก?) และ "Park กลับมาเมื่อผ่านไปอย่างน้อย 1 session" (§2.5.3)

## Next step

ขั้น 4 🙋: รอ Jam ตัดสิน F1–F16 ตามตารางใน PR #31 (ข้อเสนอของ Claude: แก้ทุกข้อ ยกเว้น F5, F12, F15 เลื่อน) · F5 ต้องการ path ของไฟล์ .docx ใน Drive

## Waiting on

Jam ตัดสิน findings ใน PR #31

## Notes for next time

- `poc/P1/` ขึ้นเป็น untracked บน branch นี้ (คือ `out/` และ `results/` ของ P1) · ห้าม commit
