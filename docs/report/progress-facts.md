# Fact sheet · Progress Report เทอม 1 (ขั้นที่ 2 · ร่าง)

ตรวจเมื่อ 27 พ.ย. 2569 กับ `main` ที่ commit `ca7adac` · ทุกตัวเลขในเล่มต้องมาจากไฟล์นี้ และไฟล์นี้ต้องบอกที่มา

**ป้าย:** ✔ ตรวจกับไฟล์หรือคำสั่งแล้ว · ⚠ จริง แต่ต้องเขียนอย่างระวัง · ❓ ต้องให้ทีมยืนยันหรือเติม

---

## A. ข้อมูลโครงงานและข้อกำหนดของเล่ม

| ข้อ | ค่า | ที่มา | |
|---|---|---|---|
| ชื่อ | อ่านยัง? : ระบบห้องติวเตรียมสอบด้วยปัญญาประดิษฐ์ (AI-Powered Study Room for Exam Preparation) | proposal หน้า 1 | ✔ |
| สมาชิกและบทบาทจริง | นายเวสสภู สว่างวงษ์ (Jam) · AI + การวัดผล · นางสาวจันทรัศม์ แสงเหลา (May) · Frontend + UX · นางสาวมนสิชา คนเที่ยง (Junior) · Backend + DevOps | `docs/team/roles.md`, GitHub handle | ✔ |
| อาจารย์ที่ปรึกษา | ดร.สุเทพ มาดารัศมี | proposal | ✔ |
| ส่งเล่ม / นำเสนอ | ศ. 4 ธ.ค. 2569 / จ. 14 ธ.ค. 2569 (on-site) | สไลด์ของวิชา | ✔ |
| ความยาว | ไม่เกิน 50 หน้า | สไลด์ของวิชา | ✔ |
| โครงเล่ม | Section 1 (Intro, Objectives, Scope, Plan, Gantt, Deliverables) · Section 2 (Backgrounds, Preliminary design) · Section 3 ใหม่ (Current progress, Evaluation + plan เทอม 2) · Section 1–2 แก้ตามคอมเมนต์กรรมการและ scope ปัจจุบัน | สไลด์ของวิชา | ✔ |

## B. คอมเมนต์กรรมการ (ตอบให้ครบในเล่ม)

1. learning path และ progress tracking ต้องมีการออกแบบรองรับ และแสดงได้ว่า algorithm เชื่อถือได้จริง
2. งานดูเหมือนแค่ยิง API ให้ AI ตอบ · ต้องแสดงว่าทีมออกแบบ เขียน pipeline ออกแบบ DB และทดสอบอะไรเอง และงานซับซ้อนพอสำหรับ senior project 3 คน

## C. Scope ที่เปลี่ยนจาก proposal

| เรื่อง | proposal | ตอนนี้ | ที่มา | |
|---|---|---|---|---|
| วิชานำร่อง | LNG, Algebra ม.ปลาย, Calculus, CSC 241 Database, Intro to Physics | **MTH** (ข้อมูลจริงที่ใช้วัดผลคือ MTH10101) · **coding 1** (รหัสวิชา ____) · **วิชาท่องจำ 1 วิชา (____ รอทีมตกลง)** | `evals/topics/mth10101/` | ❓ |
| รูปแบบการเรียน | 3 โหมด: ถามตอบ, แบบทดสอบ, ฝึกข้อสอบเก่า | ห้องแชทเดียว ไม่มีปุ่มเลือกโหมด · tutor เลือกหัวข้อและให้โจทย์เอง · Probe → Teach → Verify · ใบ้ทีละระดับก่อนเฉลย | requirements TM-01, TM-03, TM-04, AM-07 · `specs/features/tutor/stage-machine.md` | ✔ |
| ขอบเขตก่อนติว | ไม่มี | ระบบสกัดหัวข้อ + ดาวความสำคัญจากชีทและข้อสอบเก่า → ผู้ใช้ตรวจและยืนยันก่อนเริ่ม | SM-01, SM-03, SM-09 | ✔ |
| persona | ไม่มี | AI Tutor + AI Buddy เลือก preset หรือบรรยายเอง | UM-03 ถึง UM-05 | ✔ |
| requirement ทั้งหมด | ไม่มีตัวเลข | 91 ข้อ: Must 74 (active 57, new 10, changed 7) · Should 14 (deferred 3, obsolete 1) · Could 2 (deferred) | `specs/requirements/requirements.md` v1.3 | ✔ |
| Must ที่ทำเสร็จแล้ว | — | ตารางใน checklist ประเมินไว้ 13 พ.ย. ซึ่งเก่าแล้ว ต้องนับใหม่ก่อนใส่เล่ม | `docs/team/sprint-checklists.md` | ❓ |

## D. ส่วนที่ทีมออกแบบและเขียนเอง (ตอบคอมเมนต์ข้อ 2)

หลักการ: **code ตัดสินใจ, LLM เป็นคนพูด** · LLM ไม่เขียน DB เอง · ทุก AI call ผ่าน gateway เดียว · ตัดสินถูก/ผิดของคณิตด้วย SymPy · ตัวเลขของ learning model อยู่ใน config ที่เดียวพร้อมที่มา (`CLAUDE.md` "Architecture rules", `docs/report/ai-evaluation.md` §1)

| ส่วน | สิ่งที่ทำ | สถานะในระบบ | ที่มา | |
|---|---|---|---|---|
| AI gateway | `ai.call` / `ai.stream`: โหลด prompt ตาม version · เลือก model ตาม tier · ตรวจ schema + retry · backoff เมื่อโดน 429 · จับคำตอบที่ถูกตัด · แยกข้อมูลผู้ใช้ด้วย data block (กัน prompt injection) · log ทุก call ลง `ai_calls` · fake provider ให้ test ไม่เสียเงิน | ใช้งานจริง | `apps/api/app/ai/gateway.py` · `specs/features/ai/` 7 ไฟล์ | ✔ |
| Ingestion pipeline | จำแนกไฟล์ → อ่านหน้าด้วย vision → แยกข้อสอบเก่าเป็นข้อ → สกัดหัวข้อรายไฟล์ → รวมหัวข้อข้ามไฟล์ → map ข้อสอบเข้าหัวข้อ → เก็บ chunk + embedding | ใช้งานจริงใน `apps/api` | `services/ingestion.py` · `specs/features/scope/ingestion.md` | ✔ |
| ดาวความสำคัญ | คิดจากสัดส่วนข้อสอบเก่าที่หัวข้อนั้นออก (code ไม่ใช่ LLM) | ใช้งานจริง | `domain/stars.py` · `scope/compute-importance.md` | ✔ |
| ตรวจคำตอบ | SymPy ตรวจทีละบรรทัด → LLM จำแนกประเภทความผิด → merge rules รวมผล | ใช้งานจริง | `domain/checker.py`, `math/` · `check/` 6 ไฟล์ | ✔ |
| อ่านลายมือ | vision → LaTeX รายบรรทัด → ผู้ใช้ยืนยันก่อนตรวจทุกครั้ง | ใช้งานจริง | `check/ocr-confirm-card.md`, `check/photo-check-in-room.md` | ✔ |
| ใบ้ทีละระดับ | hint ladder ก่อนเฉลย | ใช้งานจริง | `domain/hint_ladder.py` | ✔ |
| BKT mastery | อัปเดต mastery หลังทุก attempt ลง DB | ใช้งานจริง (`room_db_state.py` เรียก `record_attempt`) | `domain/bkt.py` · `planner/bkt-mastery.md` | ✔ |
| Planner, stage machine | เลือกหัวข้อพร้อมเหตุผล · เดิน Probe → Teach → Verify | **มีโมดูล + test แล้ว ยังไม่ต่อเข้าห้องติว** (งาน S5 และเทอม 2) | `domain/planner.py`, `domain/stage_machine.py` | ⚠ |
| กันเฉลยหลุด | ตรวจว่าคำพูดของ tutor เผยคำตอบก่อนเวลาไหม | **มีโมดูล + test แล้ว (#176) ยังไม่ต่อเข้าห้อง** | `domain/answer_leak.py` | ⚠ |
| persona จากคำบรรยาย | แปลงคำบรรยายเป็น parameter + ประโยคตัวอย่าง | API ใช้งานจริง (#178) หน้าเว็บยังไม่ต่อ | `ai/persona-extract.md` | ⚠ |
| Streaming | SSE stream คำตอบของ tutor | ใช้งานจริง | `tutor/chat-streaming.md` | ✔ |
| ฐานข้อมูล | 28 ตาราง · 9 migration · ทุกตารางมี `tenant_id` + RLS · มี isolation test | ใช้งานจริง | `supabase/migrations/`, `specs/system/data-model.md` | ✔ |
| CI/CD | GitHub Actions 4 job (api, api-integration, web, deploy) · merge แล้ว staging อัปเดตเองใน ~4 นาที | ใช้งานจริง | P6-lite | ✔ |

**RAG ⚠ ต้องเขียนให้ตรง:** ระบบเก็บ chunk + embedding แล้ว (`gemini-embedding-2` 768 มิติ, P3b recall@4 = 19/20) แต่ตอนนี้การสร้างโจทย์ในห้องดึงเนื้อหาจาก**หน้าที่มาของหัวข้อ** (`db/room_problems.py` `source_chunks` เลือก chunk ตามหน้าที่ทับกับหัวข้อ) ยังไม่ใช้ vector search · การถามตอบจากเอกสารตาม proposal §1.2.1 ยังไม่มีในห้อง → เขียนว่า "grounding ด้วยหน้าที่มาของหัวข้อ · vector search เตรียม schema และ embedding ไว้แล้ว ใช้ในเทอม 2 (SM-10, SM-11)"

## E. Learning model (ตอบคอมเมนต์ข้อ 1)

| เรื่อง | วิธี | ที่มา | |
|---|---|---|---|
| Mastery | Bayesian Knowledge Tracing ต่อหัวข้อ อัปเดตเฉพาะ attempt ที่ทำเอง (independent) · เพดาน mastery ตามระดับยากสุดที่ทำถูกเอง | `learning-model.md` §1, §4 | ✔ |
| ผ่าน (Done) | ต้องเคยทำถูกเองที่ระดับเป้า และ mastery หลังเพดานถึงเกณฑ์ | §4 · TM-16 | ✔ |
| ทบทวน | spaced review ตามรอบ | §3 · TM-17 | ✔ |
| ความพร้อม % | จาก mastery หลังเพดาน · หัวข้อที่ยังไม่เคยทำนับ 0 | §5 · PM-03 | ✔ |
| ติดวน | Park และ wheel-spinning | §7 | ✔ |
| ที่มาของตัวเลข | ทุกค่าอยู่ใน `config/learning.yaml` ติดป้าย [A] งานวิจัย · [B] ค่ามาตรฐาน · [calc] คำนวณ · [C] ชั่วคราว ต้อง calibrate | §ต้นไฟล์, §9 | ✔ |
| งานวิจัยรองรับ | 7 ด้าน: knowledge tracing, mastery learning, readiness, learning path, ฝึก + feedback, spaced review, พิสูจน์ผล | `docs/research/learning-path.md` | ✔ |
| ความน่าเชื่อถือ | unit test ที่ค่าขอบของทุกเกณฑ์ (ค่า − ε, ค่า, ค่า + ε) · **ค่า [C] ยังไม่ได้ calibrate กับข้อมูลจริง** · แผน calibrate ใน §9 | `learning-model.md` §9 | ⚠ ห้ามเขียนว่า "พิสูจน์แล้ว" |
| คุยกับอาจารย์ | agenda 3 เรื่อง: BKT ระดับหัวข้อหรือ skill · BKT หรือ logistic · readiness กันมั่นใจเกิน | `docs/research/agenda-learning-model.md` | ❓ ผลการคุย |

⚠ **อ้างอิงไม่ตรงกัน:** proposal อ้าง Corbett & Anderson **1994** และ Cepeda et al. **2006** · `learning-model.md` อ้าง Corbett & Anderson **1995** และ Cepeda et al. **2008** · ต้องเลือกให้ตรงกันทั้งเล่ม (Cepeda 2006 กับ 2008 เป็นคนละ paper)

## F. ผลการวัด (PoC และ eval)

| PoC | คำถาม | ผล | ที่มา | |
|---|---|---|---|---|
| P1 | อ่านลายมือคณิตเป็น LaTeX | line accuracy 119/125 = **95.2%** (เป้า ≥ 80%) PASS · confidence แยกบรรทัดอ่านผิดไม่ได้ FAIL → ให้ผู้ใช้ยืนยันทุกครั้ง · 1/8 รูปที่ตั้งใจผิด AI แก้ให้ถูกเอง · 3.0 s/รูป | `specs/poc/reports/P1.md` | ✔ |
| P2 | SymPy + LLM ตรวจคำตอบ | verdict 50/50 · error type 27/28 = 96.4% · บรรทัดแรกที่ผิด 24/24 · SymPy ตัดสินเอง 45/50 ข้อ median 0.14 s | `P2.md` | ✔ |
| P3a | สกัดหัวข้อ + ดาว (MTH10101) | ★★★ ตรง 10/12 = **83%** PASS · หัวข้อตรง 20/27 = **74%** FAIL (เป้า 80%) · ≤ 1.45 นาที/ไฟล์ | `P3.md` §7 | ✔ |
| P3b | embedding ภาษาไทย | `gemini-embedding-2` 768 มิติ recall@4 19/20 | `P3.md` | ✔ |
| P4-lite | stream เร็วพอไหม | TTFT p95 1.20 s ในเครื่อง (`thinking: minimal`) · ยังไม่ได้วัดบน staging · ต้นทุน 0.039 บาท/ข้อความ ≈ 1.73 บาท/session | `P4-lite.md` | ⚠ |
| P6-lite | deploy อัตโนมัติ + แยก tenant | 8/8 PR deploy เอง 3.4–4.6 นาที · isolation test ไม่เคยล้ม · secret ใน git 0 | `P6-lite.md` | ✔ |
| persona eval | แปลงคำบรรยาย | field 49/49 · refused 4/4 · injection 4/4 · ใช้สรรพนามตามตั้ง 24/24 | PR #178 | ✔ |

**Golden set:** ลายมือ 30 รูป 125 บรรทัด จาก 5 คน · คำตอบ 50 ข้อ · หัวข้อ MTH10101 ชีท 4 ไฟล์ 179 หน้า + ข้อสอบ 43 ข้อย่อย + คำถามค้น 20 ข้อ · persona 24 เคส (`evals/`, `ai-evaluation.md` §2.2)

⚠ **bias ของ label ที่ต้องเขียนไว้:** label หัวข้อ P3 มี Jam (คนทำ PoC) ร่วม · label P2 ร่างโดย AI แล้ว May ตรวจ (`ai-evaluation.md` §2.2)

## G. ความคืบหน้าเชิงตัวเลข

| ข้อ | ค่า | ที่มา | |
|---|---|---|---|
| เริ่ม repo | 12 ต.ค. 2569 | `git log` | ✔ |
| Sprint | S1–S6 ราย 2 สัปดาห์ + Buffer (5 ต.ค. ถึง 31 ธ.ค.) | `sprint-checklists.md` | ✔ |
| PR ที่ merge | 167 (Jam 91 · May 47 · Junior 29) | `gh pr list` | ⚠ จำนวน PR ไม่เท่ากับปริมาณงาน ควรแสดงตามส่วนงาน |
| commit | 1,288 | `git log` | ✔ |
| โค้ด | API Python 11,930 บรรทัด · test API 19,761 · เว็บ TS/TSX 4,165 (ไม่นับ test และไฟล์ generate) · test เว็บ 6,216 · SQL 651 | นับด้วย `Get-Content` | ✔ |
| test | API 2,229 ผ่าน (22 พ.ย.) · เว็บ 467 ผ่าน · CI ล่าสุดบน `main` เขียว (22 พ.ย.) | ผลรัน + `gh run list` | ✔ |
| API | 37 endpoint ใน 6 router | `apps/api/app/routers/` | ✔ |
| หน้าเว็บ | 9 หน้า | `apps/web/app/**/page.tsx` | ✔ |
| feature spec | 47 ไฟล์ · spec ทั้งหมด 7,752 บรรทัด | `specs/` | ✔ |
| prompt | 17 purpose มี version | `prompts/` | ✔ |
| checklist | เสร็จ 83 · ค้าง 38 | `sprint-checklists.md` | ⚠ แต่ละข้อขนาดไม่เท่ากัน |
| demo end to end | วิดีโอ 8 ฉาก ตามที่อาจารย์ขอ 13 พ.ย. | `docs/design/demo-video.md` | ❓ ส่งอาจารย์แล้วหรือยัง |
| ทดสอบกับผู้ใช้ (Alpha) | **ยังไม่ได้ทำ** | Jam 27 พ.ย. | ✔ ต้องเขียนในส่วนปัญหาและแผน |

## H. สิ่งที่ proposal สัญญาไว้สำหรับเทอม 1 (§1.5.1) เทียบกับที่ทำจริง

| # | สัญญาไว้ | ผล |
|---|---|---|
| 1 | proposal ผ่านการอนุมัติ | ✔ |
| 2 | เอกสารออกแบบ (architecture, DB schema, E2E flow) | ✔ และมากกว่าที่สัญญา (system spec 7 ไฟล์, feature spec 47) |
| 3 | อัปโหลดเอกสาร + ถามตอบจากเอกสาร | อัปโหลด ✔ · ถามตอบจากเอกสาร ✘ เพราะ design เปลี่ยนเป็น tutor เป็นคนนำ |
| 4 | โหมดแบบทดสอบสร้างคำถามอัตโนมัติ | เปลี่ยนเป็นสร้างโจทย์ในห้องที่เฉลยผ่าน SymPy แล้ว (AM-11) ✔ |
| 5 | แสดงสมการ | ✔ (TM-08) |
| 6 | ผลทดสอบผู้ใช้กลุ่มแรก | ✘ ยังไม่ได้ทำ |

**ทำก่อนแผน (proposal วางไว้เทอม 2):** ตรวจคำตอบลายมือ (P1, P2) · BKT ลง DB · deploy staging อัตโนมัติ

**ผู้รับผิดชอบเปลี่ยนจาก Gantt เดิม:** proposal ให้มนสิชาทำ RAG และโหมดเรียน และให้เวสสภูทำ DB/architecture · จริง: เวสสภู = AI, มนสิชา = backend/DevOps, จันทรัศม์ = frontend/UX (`roles.md`)

## I. ปัญหาและข้อจำกัดที่พบ (สำหรับ self-evaluation)

| ปัญหา | สาเหตุ | ทำอะไรไปแล้ว | ที่มา |
|---|---|---|---|
| confidence ของ vision แยกบรรทัดที่อ่านผิดไม่ได้ | model มั่นใจ 0.85–0.98 แม้อ่านผิด | ให้ผู้ใช้ยืนยันผลอ่านทุกครั้ง | P1 |
| AI แก้คำตอบผิดให้ถูกเอง 1/8 | model "ช่วย" แก้ | ทำให้ checker ตรวจผิดได้ · ยืนยันโดยผู้ใช้ | P1 |
| หัวข้อตรงแค่ 74% | ชีทภาษาไทย แบ่งหัวข้อไม่ตรงคน | ปรับ prompt v2 · ผู้ใช้แก้ scope ได้ก่อนติว | P3 |
| free tier จำกัด 20 request/วัน | โควตา Gemini | ย้ายไป Vertex AI | P2, P3 |
| 429 ระหว่างซ้อม demo | rate limit ของ provider | backoff ใน gateway (#159) | checklist |
| ไฟล์ ingestion ค้าง | งานเบื้องหลังล้ม | endpoint retry | checklist |
| ค่า [C] ยังไม่ calibrate | ยังไม่มีข้อมูลผู้ใช้จริง | แผน calibrate ใน pilot | `learning-model.md` §9 |
| ข้อมูลวัดผลมีวิชาเดียว | เก็บได้เฉพาะ MTH10101 | ต้องวัดวิชาที่ 2 | P3 §6 |
| ยังไม่ทดสอบกับผู้ใช้ | ทุ่มเวลาให้ demo end to end ที่อาจารย์ขอ | ย้ายไปต้นเทอม 2 | ❓ ทีมยืนยันเหตุผล |

## J. รอทีมเติมหรือยืนยัน ❓

1. ชื่อและรหัสวิชา coding 1 · วิชาท่องจำ (ถ้ามี)
2. วิดีโอ demo ส่งอาจารย์แล้วหรือยัง และอาจารย์ให้ feedback อะไร
3. ผลการคุยเรื่อง learning model กับอาจารย์ (agenda 3 ข้อ)
4. นับ Must ที่เสร็จจริงใหม่ (แต่ละคนนับส่วนของตัวเอง)
5. เหตุผลที่ยังไม่ทดสอบกับผู้ใช้ ตามที่ทีมจะเขียน
