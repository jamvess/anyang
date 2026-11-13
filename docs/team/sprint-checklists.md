# Checklist ราย sprint ของแต่ละคน · เทอม 1

อัปเดต 14 ต.ค. 2569 · อ้างอิงแผนเทอม 1 ฉบับลด scope · **13 พ.ย. แผนใหม่ (Jam · อาจารย์ขอ):** demo end to end จ. 23 พ.ย. แล้วทำ requirement ระดับ Must ทั้งหมด (74 ข้อ) ภายในสิ้นเทอม 31 ธ.ค. · เพิ่ม S5, S6 · Buffer ย้ายไปท้ายเทอม

**วิธีใช้:** ไฟล์นี้บน `main` คือสถานะจริงของทีม ติ๊กข้อของตัวเอง**ใน PR เดียวกับงานที่ทำเสร็จ** พอ merge ทุกคนจะเห็นหลัง `git pull` (`/work-done` ติ๊กให้อัตโนมัติ · ดู `daily-workflow.md`)

| Sprint | วันที่ | เป้าหมาย | Demo |
|---|---|---|---|
| S1 | 5–16 ต.ค. (หยุด 13 ต.ค.) | เตรียมพื้น: repo, CI, specs, เก็บข้อมูลจริง | ศ. 16 ต.ค. |
| S2 | 19–30 ต.ค. (หยุด 23 ต.ค.) | พิสูจน์ความเสี่ยงใหญ่: อ่านลายมือ + สกัดหัวข้อ + deploy อัตโนมัติ | ศ. 30 ต.ค. |
| S3 | 2–13 พ.ย. | ตรวจคำตอบ + chat AI ที่ stream ได้ | ศ. 13 พ.ย. |
| S4 | 16–27 พ.ย. | **demo end to end ในเครื่อง** (วิดีโอ จ. 23 พ.ย.) + P8-lite + demo รวม | จ. 23 พ.ย. (วิดีโอ) · ศ. 27 พ.ย. |
| S5 | 30 พ.ย.–11 ธ.ค. | การติวตามแผน: planner + stage machine + skill + Verify · scope แก้ผ่านแชท · Google login + persona · journey บน staging | ศ. 11 ธ.ค. |
| S6 | 14–25 ธ.ค. | Must ที่เหลือ: buddy, ทบทวน, Park, TTS, ความปลอดภัย, ลบบัญชี · ปิดบั๊ก | ศ. 25 ธ.ค. |
| Buffer | 28–31 ธ.ค. | รายงาน + นำเสนอ (เดิม 30 พ.ย.–4 ธ.ค.) | |

> S1 เริ่มไปแล้ว 1 สัปดาห์ ถ้างาน S1 ยังไม่เริ่ม ให้ทำข้อที่มี ⭐ ก่อน เพราะเป็นงานที่คนอื่นรออยู่

---

## ⭐ Priority: demo end to end · จ. 23 พ.ย. 2569

อาจารย์ขอ (13 พ.ย. · Jam): ผู้ใช้คนเดียวเดินได้ครบ **ตั้งแต่ login จนจบ session แล้วกลับมาเห็นต่อ** · **รันในเครื่องแล้วอัดเป็นวิดีโอ** (ไม่ต้องบน staging) · ทำข้อในส่วนนี้ก่อนข้ออื่นทุกข้อ · สถานะตรวจกับโค้ดบน `main` 13 พ.ย. (`specs/system/architecture.md` v1.3)

**วันสำคัญ:** พฤ. 19 พ.ย. ทุกขั้นต่อกันได้ในเครื่องเดียว · ศ. 20 พ.ย. ซ้อมเดินครบ + แก้บั๊ก · ส. 21 – อา. 22 พ.ย. อัดวิดีโอ (May) · จ. 23 พ.ย. ส่งอาจารย์

**เครื่องที่รัน:** Supabase ในเครื่อง (`npx supabase start` · มี Auth + Storage + DB ครบ · migration ขึ้นด้วย `npx supabase db reset` ไม่ต้อง `db push`) + API `APP_ENV=local AI_PROVIDER=live AUTH_REQUIRED=true` + เว็บ `pnpm dev` · Gemini จริงบน Vertex

### Journey 9 ขั้น

| # | ขั้น | ผ่านเมื่อ | มีแล้ว | ที่ขาด (เจ้าของ) | ถ้าไม่ทัน |
|---|---|---|---|---|---|
| 1 | Login (UM-01) | สมัคร / เข้าด้วย email + password แล้วหน้าเว็บส่ง token ทุก request · API ได้ `tenant_id` จาก token | API ตรวจ JWT (`api-auth.md`) · trigger สร้าง tenant + profile (`0001`) · `custom_access_token_hook` เปิดแล้วใน `supabase/config.toml` | หน้า login + เก็บ session + ส่ง `Authorization` (**May**) · env ของ API ให้ชี้ Supabase ในเครื่อง (`SUPABASE_URL`, `SUPABASE_ANON_KEY` ของ `npx supabase status`) แล้วยืนยันว่า token มี `tenant_id` (**Junior**) | บัญชีที่สร้างไว้ก่อน แล้ว login ในวิดีโอ |
| 2 | สร้างการเตรียมสอบ (CM-01, CM-02) | กรอกชื่อวิชา + วันสอบ → เห็นในรายการพร้อมวันที่เหลือ | `POST` / `GET /exam-preps` บน DB (#121) | หน้ารายการ + ฟอร์มสร้าง แทนหน้า template ของ Next (**May**) | ฟอร์มเดียวไม่มีรายการ |
| 3 | อัปโหลดชีท + ข้อสอบเก่า (CM-03, CM-07) | เลือกหลายไฟล์ → ขึ้น Storage → เห็นสถานะรายไฟล์ | สัญญา API ของ materials (api.md v1.10 · ยังเป็นข้อเสนอ) · stub | `/exam-preps/{id}/materials` จริง + signed upload URL + bucket และ policy (migration ใหม่) (**Junior**) · หน้าอัปโหลด (**May**) | ไฟล์เดียว · ไม่มีการแก้ประเภทไฟล์ |
| 4 | ระบบอ่านไฟล์ → หัวข้อ + ดาว (SM-01, SM-03, SM-04, CM-06) | หลังยืนยันไฟล์ ระบบสกัดหัวข้อ ดาว และหน้าที่มา ลง `topics`, `topic_sources` | pipeline ใน `poc/P3/` (★★★ ตรง 83%) · `domain/stars.py` (#113) | ย้าย pipeline เข้า `apps/api` เป็นงานเบื้องหลัง + เรียก `compute_importance` + `GET /exam-preps/{id}/ingestion` จริง (**Jam** · DB write ร่วมกับ **Junior**) | รัน ingestion จริงก่อนอัด แล้วตัดช่วงรอในวิดีโอ |
| 5 | ตรวจขอบเขตแล้วยืนยัน (SM-09) | หน้า scope แสดงหัวข้อจริง → ยืนยัน → บันทึก `scope_versions` + `active_scope_version_id` | หน้า scope (`ScopeReview.tsx`) · API stub 3 ตัว | `GET /scope` อ่าน DB + `POST /scope/confirm` เขียน DB (**Junior**) · หน้าเว็บต่อ API จริง (**May**) · แก้ scope ผ่านแชท (SM-06) หลัง demo | ยืนยันได้อย่างเดียว ไม่แก้ |
| 6 | เข้าห้องติว · tutor ทักก่อน · ให้โจทย์จากหัวข้อของผู้ใช้ (TM-01, TM-15, AM-11) | session ผูก scope ที่ยืนยัน · การ์ดความคืบหน้าจาก DB · โจทย์ของหัวข้อที่เลือก มีเฉลยที่ SymPy ตรวจแล้ว | ห้องบน DB (#123) · คำทัก `open_session` · เดโม่ในเครื่อง (โจทย์ตายตัว 5 ข้อ) | ทางที่มี token ใช้ของเดโม่ (คำทัก, โจทย์, hint ladder) แทนการตอบแชทอย่างเดียว (**Jam**) · เลือกหัวข้อด้วยกฎง่าย (ดาวสูง mastery ต่ำ) ยังไม่ใช่ planner เต็ม (**Jam**) · ที่มาของโจทย์: ดูคำถาม D3 | คลังโจทย์ที่เขียนไว้ต่อหัวข้อ |
| 7 | ตอบ (พิมพ์ / รูป / canvas) → ตรวจ → ใบ้ (TM-06 ส่วนพิมพ์และรูป, AM-01–07) | ทั้งพิมพ์และรูป/canvas ได้ผลตรวจจาก SymPy ในทางที่มี token · hint ladder ตาม `demo-room.md` §2 K (เฉพาะ `APP_ENV=local` · AM-07 ยังเป็นข้อเดิมจนกว่าทีมตัดสิน) | ครบในเดโม่ในเครื่อง (#115, #117, #127) · ไม่มี token เท่านั้น · รูปในเครื่องอ่านจาก `.local/uploads` (`LocalImageStore`) จึงไม่ต้องใช้ Storage | ต่อ `typed_answer` + ตรวจ + hint ladder เข้าทางที่มี token (**Jam**) · `ImageStore` บน Storage ไม่ต้องใช้ใน demo (S5 บน staging · **Junior**) | ใช้ข้อความพิมพ์ + รูปที่เตรียมไว้ |
| 8 | ความคืบหน้าบันทึกและเห็น (PM-01, PM-02, PM-04) | ตอบแล้วบันทึก `problems`, `attempts`, `topic_progress` · เปิดห้องใหม่เห็นระดับและความพร้อมเปลี่ยน | BKT (`domain/bkt.py`) · การ์ดคิดจาก state ในเดโม่ | repository ของ 3 ตาราง (**Junior**) · เรียก BKT แล้วเขียนผล + การ์ดจาก DB (**Jam**) | การ์ดตอนเปิดห้องเท่านั้น |
| 9 | จบ session · กลับมาเห็นต่อ (TM-13, PM-05) | ผู้ใช้กดจบ (ระบบเสนอให้จบเอง TM-12 อยู่ใน S5) → สรุป session → กลับมาเห็นประวัติและโจทย์ค้าง | ประวัติแชทกลับมาเห็นได้ (#123) | `POST /sessions/{id}/end` จริง (บันทึก `ended_at` + สรุป) (**Junior**) · สรุปจาก AI (`session_summary`) (**Jam**) | สรุปแบบ template ไม่เรียก AI |

### ต้องตัดสินก่อนเริ่ม (ภายใน จ. 16 พ.ย.)

- **D1 · Junior + May:** login ใน demo เป็น **email + password** บน Supabase ในเครื่อง (UM-01) ไหม · Google (UM-02) ต้องตั้ง OAuth client ซึ่งรันในเครื่องยุ่งกว่า · ข้อเสนอ: email ใน demo · Google ทำใน S5 (ยังเป็น Must)
- **D2 · Junior:** demo ใช้ Supabase ในเครื่อง (Docker) แทน `anyang-dev` ไหม · ข้อเสนอ: ในเครื่อง เพราะมี Storage, ขึ้น migration ได้เอง และไม่กระทบ DB ของทีม · หลังอัดวิดีโอค่อยทำบน staging
- **D3 · Jam:** โจทย์ในห้องมาจากไหน · (ก) `generate_problem` สร้างจากหัวข้อ + ตรวจเฉลยด้วย SymPy (AM-11 · ตรงกับ design) · (ข) คลังโจทย์เขียนไว้ต่อหัวข้อ · **ตัดสินแล้ว 13 พ.ย. (Jam): (ก) และใช้ (ข) เป็นทางสำรอง**
- **D4 · May:** ลำดับในวิดีโอและความยาว (`docs/design/demo-flow.md` ของ May · ช่วง live เดิมเป็นห้องติวอย่างเดียว)

### งานของแต่ละคนสำหรับ demo (เรียงตามที่คนอื่นรอ)

- **Junior:** D1, D2 → hook + env ในเครื่อง (ขั้น 1) → materials + Storage (ขั้น 3) → scope อ่าน/ยืนยันบน DB (ขั้น 5) → repository `problems` / `attempts` / `topic_progress` (ขั้น 8) → `ImageStore` บน Storage (ขั้น 7) → จบ session (ขั้น 9)
- **May:** D1, D4 → หน้า login (ขั้น 1) → หน้ารายการ + สร้างการเตรียมสอบ (ขั้น 2) → หน้าอัปโหลด (ขั้น 3) → หน้า scope ต่อ API จริง (ขั้น 5) → อัดวิดีโอ
- **Jam:** D3 → ingestion เข้า `apps/api` (ขั้น 4 · ใหญ่สุด เริ่มก่อน) → ห้องติวในทางที่มี token: คำทัก + โจทย์ + ตรวจ + hint ladder (ขั้น 6–7) → BKT ลง DB (ขั้น 8) → สรุป session (ขั้น 9)

---

## แผน Must ทั้งหมดถึงสิ้นเทอม (74 ข้อ · `specs/requirements/requirements.md`)

สถานะประเมินจากโค้ดบน `main` 13 พ.ย. (`architecture.md` v1.3) · ✅ มีแล้ว · 🟡 บางส่วน (เช่น มีแค่ในเดโม่ในเครื่อง หรือ API เป็น stub) · ❌ ยังไม่มี · เจ้าของตาม `roles.md` (backend/DB → Junior · หน้าจอ → May · AI/prompt/learning model → Jam) · เจ้าของตรวจสถานะของตัวเองอีกรอบตอน `/work-start`

| กลุ่ม | ✅ มีแล้ว | S4 (demo) | S5 | S6 |
|---|---|---|---|---|
| บัญชี + persona (UM) | — | UM-01 email login | UM-02 Google · UM-03, UM-04 เลือก preset · UM-05 custom persona · UM-08 ชื่อเล่น/ระดับ · UM-09 แก้ทีหลัง | UM-10 ลบบัญชี |
| เตรียมสอบ + ไฟล์ (CM) | CM-01, CM-02 (API) | CM-01, CM-02 (หน้าเว็บ) · CM-03 หลายไฟล์ · CM-06 classify (AI) · CM-07 สถานะรายไฟล์ | CM-04 note รายไฟล์ · CM-05 เพิ่มไฟล์ทีหลัง · CM-06 หน้ายืนยัน/แก้ประเภทไฟล์ + confidence · CM-10 ลบไฟล์ | |
| ขอบเขต (SM) | — | SM-01 สกัดหัวข้อ · SM-03 ดาว · SM-04 หน้าที่มา · SM-09 บันทึกการยืนยัน | SM-02 ลำดับ prerequisite · SM-06 แก้ผ่านแชท · SM-07 รายการอัปเดตทันที · SM-08 change log · SM-12 skill ต่อหัวข้อ | SM-06 แก้ scope ด้วยเสียง · SM-10 คำถามนอก scope · SM-11 ไม่สอนวิธีที่ไม่มีในชีท (grounding) |
| การติว (TM) | TM-08 สมการ · TM-10 ถามกลับให้แคบลง (`tutor_reply/v2` · ทั้งทางที่มีและไม่มี token) · TM-13 กลับมาต่อ (DB) · TM-14 (ข้อห้าม ไม่ต้องสร้าง) | TM-01 เลือกหัวข้อ (กฎง่าย) · TM-06 พิมพ์ + รูป/canvas เมื่อ login · TM-15 การ์ดจาก DB · TM-20 | TM-01 + TM-02 planner เต็มพร้อมเหตุผล · TM-03 probe · TM-04 stage machine · TM-11 ขอดู progress · TM-12 เสนอจบ session · TM-16 ผ่านตาม skill · TM-18 mode | TM-05 buddy · TM-06 ตอบด้วยเสียง (mic + STT) · TM-09 TTS · TM-17 ทบทวนตามรอบ · TM-19 Park |
| ตรวจคำตอบ (AM) | AM-01, AM-02, AM-04, AM-05, AM-06 (P1, P2) · AM-07 (hint ladder ในเดโม่เป็นข้อเสนอแก้ AM-07 · รอทีม) | AM-11 เฉลยที่ SymPy ตรวจแล้ว (`generate_problem`) | AM-08 Verify ด้วยโจทย์แบบเดียวกัน · AM-09 ยังไม่เข้าใจหลังอธิบาย · AM-13 answer-leak check | |
| ความคืบหน้า (PM) | PM-03 สูตร (code) | PM-01 บันทึก attempt · PM-02 mastery ลง DB · PM-03 + การ์ดในห้องจาก DB · PM-05 สรุป session · PM-06 แยกตาม prep | PM-04 readiness + หัวข้อที่ยังไม่แม่นบนหน้า home | |
| AI platform (AI) | AI-01, AI-03, AI-04, AI-05, AI-07 | AI-08 เก็บ text ของ chunk (ingestion) | | AI-02 provider ที่ 2 (Claude) ให้สลับได้จริง |
| SaaS + ความปลอดภัย (SA) | SA-01, SA-02 (schema) · SA-03 (`ai_calls`) · SA-06 (RLS + isolation test ทุกตารางใหม่) | | | SA-09 สัญญาณความเครียดรุนแรง |

**หลักแบ่ง sprint:** S4 = ทุกอย่างที่ journey ของ demo ต้องใช้ · S5 = การติวตาม design จริง (planner, stage, skill, Verify) และส่วนบัญชี/ขอบเขตที่ผู้ใช้แก้ได้ · S6 = ส่วนที่เหลือที่ไม่มีใครรอ · ทุก sprint ใช้ flow spec → test → implement เดิม

---

## Junior · Backend + DevOps

### S1 · 5–16 ต.ค.

- [x] ⭐ สร้าง repo, วาง starter files · branch protection เปิดแล้ว 20 ต.ค. (ruleset `main` id 25374094 · ต้อง approve 1 คน + CI `api`, `api-integration`, `web` ผ่าน · ห้าม force push และลบ branch · ไม่มี bypass) · repo เป็น public
  - 31 ต.ค. ทีมตกลงเลิกบังคับ approve (อยู่คนละ time zone · การรอ review ทำให้งานติด) · ruleset เปลี่ยนเป็น approve 0 คน ยังต้องเปิด PR + CI 3 ตัวผ่าน · แทนด้วย self-review `/code-review` ใน `/work-done` + บอกกลุ่มก่อน merge งานเสี่ยง (`CLAUDE.md` "How we work" 5)
- [x] ⭐ ให้ Claude Code scaffold `apps/api` และตรวจผล
- [x] ⭐ `npx supabase init` + `db push` `0001_init.sql` ขึ้น Supabase cloud `anyang-dev` + เปิด custom access token hook
- [x] GitHub Actions รันครบ 3 job และเขียวบน `main`
- [x] สร้าง GCP project, เปิด API, Artifact Registry, Secret Manager (`infra/README.md`)
  - 28 ต.ค. (PR #20): Jam สร้าง Free Trial `anyang-513006` (ถือ billing, budget alert $50) · Junior เป็น Owner · เปิด API 5 ตัว + Artifact Registry `anyang` · Secret Manager เปิดแล้วแต่ยังไม่สร้าง secret เพราะ `api-staging` ยังไม่ใช้ · ⚠️ ห้ามกด Activate/Upgrade · Gemini ใช้ผ่าน Vertex เท่านั้น
- [x] สร้าง Supabase project `anyang-staging` · ref `sfapuygntxuelsxsgkay` Singapore (21 ต.ค., PR #28)
  - 21 ต.ค. Jam ตั้ง Vercel env ทั้ง **Production** และ **Preview** (`NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`) ให้ชี้ `anyang-staging` (`sfapuygntxuelsxsgkay`) แบบ Config แล้ว redeploy production · มีผลเมื่อมีหน้าที่ import `lib/supabase.ts` (ตอนนี้ยังไม่มี production จึงไม่เคยพังจริง)
- [ ] ให้สิทธิ์ทีม: GitHub collaborator + Supabase org (เจ้าของ repo ทำ, `setup.md` A0), GCP (Jam: Vertex AI User)
  - 13 พ.ย. แผนใหม่: หลัง demo
  - 28 ต.ค. ส่วน GCP ไม่ต้องทำ: Jam สร้าง project เองจึงเป็น Owner อยู่แล้ว
- [x] แก้ `.github/CODEOWNERS` เป็น username จริง · + เพิ่ม `/.github/` ให้ Junior ตาม `roles.md` (19 ต.ค.)
- [x] ตั้งเครื่องตัวเองตาม `setup.md` Part A · ผ่านเช็คลิสต์ A6 ครบ 5 ข้อ (19 ต.ค.)
- [x] ตรวจ `specs/system/architecture.md` ให้ตรงกับที่ตั้งจริง (D2)
  - ทำโดย Jam (1 พ.ย.) ช่วง solo
  - 1 พ.ย. (PR #101): `architecture.md` v1.2 ตรงกับ `infra/README.md`, `config/ai.yaml`, workflow และ report PoC · Claude/Mathpix fallback, STT/TTS, Storage, Sentry, PWA และ prod เขียนว่าเป็นแผน · เพิ่มตาราง "สร้างแล้วหรือยัง"
- ~~ร่วม review `specs/requirements/requirements.md` (D1)~~ → ไม่ต้องทำแล้ว (Jam ตัดสิน 1 พ.ย.) · review D1 จบไปแล้วใน `requirements.md` v1.2–v1.3 (May ติ๊กข้อของตัวเองแล้ว) · ถ้า Junior มีข้อแก้ ให้เปิด PR แก้ requirement ตรงๆ
- ~~รูปลายมือ 10 รูป (D8)~~ → ไม่ต้องทำแล้ว (Jam ตัดสิน 1 พ.ย.) · แผนเปลี่ยนเป็นคนละ 6 ใบ (PR #11) และได้ครบ 30 รูปจาก 5 คนแล้ว (ข้อ D8 ของ Jam ใน S1)

**Done เมื่อ:** ทุกคน clone แล้วรันได้ตาม `setup.md` A6 และ CI เขียวบน `main`

### S2 · 19–30 ต.ค.

- [x] Cloud Build trigger: merge → deploy `api-staging` อัตโนมัติ (P6-lite)
  - ทำแล้ว 28 ต.ค. (PR #83): trigger `api-staging-deploy` (`infra/trigger-api-staging.yaml`) + `cloudbuild.yaml` ใช้ `AI_PROVIDER=fake` และ `env/api-staging.yaml` ไม่มี secret · SA `cloudbuild-deployer` (`infra/README.md` "Deploy อัตโนมัติ") · ติ๊กโดย Jam (1 พ.ย.) ช่วง solo · ผลวัดเวลาอยู่ใน report P6-lite
  - 28 ต.ค. ทางสำรองพร้อมแล้ว (PR #20): `infra/deploy-staging.ps1` deploy มือ · `api-staging` ขึ้นแล้วที่ https://api-staging-659706857266.asia-southeast1.run.app (`AI_PROVIDER=fake`, CORS ครบ) · env อยู่ใน `infra/env/api-staging.yaml` ใช้ไฟล์เดียวกันตอนทำ trigger · เหลือ trigger + แก้ `cloudbuild.yaml` (ยังตั้ง `AI_PROVIDER=live` และใช้ secret `anthropic-api-key`)
  - ⏰ Demo S2: เย็นพฤหัส 29 ต.ค. `gcloud run services update api-staging --region=asia-southeast1 --min-instances=1` กัน cold start · หลัง demo ศ. 30 ต.ค. ตั้งกลับเป็น `--min-instances=0` ทันที (instance ที่เปิดค้างกิน trial credit) · คำสั่งอยู่ใน `infra/README.md` "Demo-day"
  - env ของ api-staging อยู่ใน infra/env/api-staging.yaml (--env-vars-file) · บน Windows ห้ามส่งค่าที่มี ^ ผ่าน flag ของ gcloud (cmd.exe กิน ^) ให้ใช้ไฟล์แทน
- [x] `test_SA06_tenant_isolation` รันใน CI (P6-lite) · เสร็จก่อนกำหนดใน S1
- [x] ตรวจว่าไม่มี secret ใน git history · เสร็จก่อนกำหนดใน S1 (15 ต.ค.)
- [x] ปรับ `schema.sql` ตามที่เจอระหว่าง P3 + วาด ERD (D3)
  - 20 ต.ค. วาด ERD ใหม่แล้ว 3 รูป ครบ 27 ตาราง (+ `auth.users` วาดไว้ให้ดูความสัมพันธ์) และ FK ทั้ง 45 ตัว (PR #30) · เหลือแก้ schema ตามผล P3 (จดไว้ 5 ข้อใน `data-model.md`)
  - 21 ต.ค. migration `0002` เพิ่ม `messages.attachment_name` (api.md v1.3) + ERD รูป 3 (PR #43) · ตรวจ 5 ข้อของ P3 แล้ว ยังยืนยันไม่ได้สักข้อเพราะ A6/A7 ยังไม่เคยรันผ่าน (สถานะอยู่ใน `data-model.md`) · เหลือแก้ schema หลังมี report P3a
  - ทำโดย Jam (1 พ.ย.) ช่วง solo · ต่อจาก Junior ขั้น 3–5
  - 1 พ.ย. (PR #67): migration `0003_topic_sources.sql` ตาราง `topic_sources` (ช่วงหน้าของหัวข้อ · check `page_from >= 1 and page_to >= page_from` · Junior ยืนยันแล้ว 9 พ.ย.) + `past_exam_questions.map_note` · ERD รูป 2 + `data-model.md` v1.3 · ⚠️ Junior ยืนยัน check ก่อน แล้วค่อย `db push` ขึ้น `anyang-dev` และ `anyang-staging` (ถ้าไม่เอา check ให้แก้ด้วย migration `0004` ใน PR ใหม่)
  - 9 พ.ย. (PR #116): Junior ยืนยัน check ตามเดิม ไม่ต้องมี `0004` · `db push` `0003` ขึ้น `anyang-dev` และ `anyang-staging`
- ~~ช่วย Jam ทำ ingest pipeline ของ P3: อ่าน PDF (PyMuPDF), ตัด chunk, เก็บลง DB~~ → ไม่ต้องทำแล้ว (Jam ตัดสิน 1 พ.ย.) · P3 ปิดแล้ว (report `P3.md` · #37, #94) · Jam เขียน ingest ของ PoC เองใน `poc/P3/ingest.py` · ingest จริงของแอป (เก็บลง DB) เป็นงานใหม่ ยังไม่มีใน checklist
- [x] เขียน report P6-lite ด้วย `/poc-report P6-lite`
  - ทำโดย Jam (1 พ.ย.) ช่วง solo
  - 1 พ.ย. (PR #96 · `specs/poc/reports/P6-lite.md`): **ผ่านครบ 3 เกณฑ์** · merge แล้ว staging อัปเดตเอง 8/8 ภายใน 3.40–4.58 นาที (เป้า 10) · `api-integration` (isolation) รันทุก push เข้า `main` 84/89 ผ่าน อีก 5 ล้มเพราะ CI ดึง image/CLI ไม่ได้ ไม่ใช่ test · secret 0 (scanning + push protection + grep 709 commit) · วัดซ้ำได้ด้วย `poc/P6-lite/` · Junior ให้ Claude แนะนำ, Jam ยืนยัน: ใช้ Cloud Build ต่อ + pin `supabase/setup-cli` เป็น `2.122.0` ใน `ci.yml`

**Done เมื่อ:** merge PR แล้ว staging อัปเดตเองภายใน 10 นาที และ isolation test ผ่าน

### S3 · 2–13 พ.ย.

- ~~SymPy service `app/math/`~~ → ย้ายให้ Jam 21 ต.ค. (ทีมตกลง · ใกล้กับ P2) · ดูข้อใน S3 ของ Jam
- [x] AI gateway แบบ lite `app/ai/`: `ai.call()`, provider Gemini + fake, อ่าน `config/ai.yaml`, log `ai_calls`
  - 31 ต.ค. Jam เพิ่ม provider `vertex` (PR #87 · Junior ok) · ยังเหลือ log `ai_calls` ลงตาราง
  - ทำโดย Jam (31 ต.ค.) ช่วง solo
  - 31 ต.ค. (PR #95 · `specs/features/ai/ai-calls-log.md`): `AICallLog` ใน `build_default_gateway()` เขียน log JSON ทุก call (logger `app.ai.calls` → Cloud Logging) · call ที่มี tenant (`ai_call_context`) insert ลง `ai_calls` เบื้องหลังด้วย service role ไม่ให้ call รอ DB · ยังไม่มี request ไหนตั้ง tenant จนกว่าจะตรวจ JWT (ข้อ ⚠️ ด้านล่าง) จึงยังมีแค่ log · `cost_usd`, `cached_tokens` เป็น null · รอ Junior: (1) `app/db/` ใช้ supabase-py ไปก่อน เปลี่ยนเป็น psycopg ได้ (2) insert ที่ค้างตอน instance ปิดหายได้ (`AICallLog.flush()` พร้อมให้ lifespan ใช้)
  - ⚠️ 28 ต.ค. ห้ามเปิด AI_PROVIDER=live บน api-staging จนกว่าจะเช็ค Supabase JWT ทุก endpoint · URL เป็น public (--allow-unauthenticated) คนนอกเรียกแล้วกิน credit ได้
- [x] Endpoint SSE `POST /sessions/{id}/messages` ที่ stream จาก gateway (P4-lite)
  - ทำโดย Jam (31 ต.ค.) ช่วง solo
  - 31 ต.ค. (PR #93 · `specs/features/tutor/tutor-reply-stream.md`): ข้อความ text → `ai.stream("tutor_reply")` (ของใหม่ใน gateway · retry เฉพาะก่อนชิ้นแรก) → `token` → `done` · ล้มก่อนชิ้นแรกส่ง "ระบบช้า ลองส่งอีกทีนะ" · ล้มกลางทางส่ง `error` · รูปยังเป็น stub · prompt `tutor_reply/v1` · `ai.yaml` 1.5 `thinking: low`, `max_tokens` 2000 · smoke บน Vertex ในเครื่อง TTFT 3.7 วินาที (เป้า 2 วินาที · ให้ report P4-lite ตัดสิน)
  - รอ Junior: (1) P4-lite ยังไม่ตรวจ JWT และไม่บันทึก `messages` ใช่ไหม (spec §10 ข้อ 1) (2) `error.code` `message_too_long`, `ai_unavailable` (ข้อ 3 · ยังไม่แก้ `api.md`) · staging ยังเป็น fake (ตอบด้วยข้อความ tutor ของ stub ไม่มี buddy)
- [x] เขียน router หัวฟังก์ชันของทุก API ใน `specs/system/api.md` ให้หน้า `/docs` ครบ (D5)
  - 20 ต.ค. api.md v1.2 ห้องติว (PR #35) + stub 4 endpoint ของห้องติวที่คืน fixture ของ May พร้อม `X-Stub: true` (PR #38) · `/docs` แสดง schema ของ `Room`, `Message`, event SSE และ `ErrorResponse` · เหลือ endpoint กลุ่มอื่นใน api.md
  - ทำโดย Jam (1 พ.ย.) ช่วง solo · ทำได้บางส่วน
  - 1 พ.ย. (PR #100): api.md v1.6 หน้าตรวจขอบเขต (เป็นข้อเสนอ รอ Junior ตัดสิน 5 ข้อใน "รอตัดสิน (v1.6 · Junior)") + stub 3 endpoint ที่คืน fixture ของ May พร้อม `X-Stub: true`: `GET /exam-preps/{id}/scope`, `GET /topics/{id}/sources`, `POST /exam-preps/{id}/scope/confirm` · May รัน `pnpm gen:api` แล้วใช้ type `Scope`, `TopicSources` แทน type ที่เขียนเองได้ · เหลือ upload/materials, ingestion, `scope/chat`, `scope/changes`, persona, บัญชี และอีก 6 endpoint ของห้องติว
  - 1 พ.ย. (PR #102 · Jam ช่วง solo): api.md v1.7 `POST /sessions/{id}/uploads`, `/transcribe`, `/ocr/confirm` + payload ของ `ocr_preview` / `verdict` (ข้อเสนอ รอ Junior 5 ข้อ) · stub ทั้ง 3 + ข้อความรูปใน stub ส่ง `ocr_preview` · `api-schema.ts` generate ใหม่ · ยังเหลือ: `/uploads` จริงที่ต่อ Storage, `/end`, `GET /sessions/{id}/messages`, `/progress`, `/tts`, upload/materials, ingestion, `scope/chat`, `scope/changes`, persona, บัญชี
  - 2 พ.ย. (PR #104 · Jam ช่วง solo): api.md v1.9 `POST /sessions/{id}/end` (SSE `session_end`), `GET /sessions/{id}/messages`, `GET /exam-preps/{id}/progress` (schema `ProgressCardEvent`), `GET /messages/{id}/tts` (ข้อเสนอ รอ Junior 5 ข้อ) + stub ทั้ง 4 · ห้องติวมี stub ครบทุก endpoint แล้ว · ยังเหลือ: exam prep + materials, ingestion, `scope/chat`, `scope/changes`, persona, บัญชี
  - 2 พ.ย. (PR #105 · Jam ช่วง solo): api.md v1.10 `POST`/`GET /exam-preps`, `POST /exam-preps/{id}/materials`, `POST /materials/{id}/uploaded`, `GET /exam-preps/{id}/materials`, `POST /exam-preps/{id}/materials/confirm` (ข้อเสนอ รอ Junior 6 ข้อ) + stub ทั้ง 6 · `api-schema.ts` generate ใหม่ · ยังเหลือ: `GET /exam-preps/{id}/ingestion`, `scope/chat`, `scope/changes`, persona, บัญชี
  - 4 พ.ย. (PR #106 · Jam ช่วง solo): api.md v1.11 `GET /exam-preps/{id}/ingestion`, `POST /exam-preps/{id}/scope/chat` (SSE `scope_patch`), `GET /exam-preps/{id}/scope/changes`, `POST /materials/{id}/retry`, `DELETE /materials/{id}` (ข้อเสนอ รอ Junior 8 ข้อ) + stub ทั้ง 5 · แก้กฎ `stage` ของ v1.10 · `scope/chat` นับ rate limit เดียวกับห้องติว · `api-schema.ts` generate ใหม่ · flow 2.3 มี stub ครบแล้ว · ยังเหลือ: persona (`/personas/*`, `/me/*-profile`, `/me/profile`), บัญชี (`DELETE /me`, `DELETE /exam-preps/{id}`) · ฝั่งเสียงของ SM-06 ยังไม่มี endpoint (รอตัดสิน v1.11 ข้อ 5)
  - 4 พ.ย. (PR #107 · Jam ช่วง solo): **`/docs` ครบทุก endpoint ใน `api.md` แล้ว** (`test_api_md_endpoints.py` เทียบให้ทุกครั้ง) · api.md v1.12 persona, โปรไฟล์, `DELETE /me`, `DELETE /exam-preps/{id}` (ข้อเสนอ รอ Junior 8 ข้อ) + stub ทั้ง 10 · `guards.max_persona_text_chars` ใน `config/ai.yaml` 1.9 · `api-schema.ts` generate ใหม่ · **ติ๊กตามข้อความของข้อนี้ ไม่ได้แปลว่า contract ตกลงแล้ว:** ทุก endpoint ที่ Jam เสนอยังรอ Junior ตัดสินใน "รอตัดสิน" v1.6, v1.7, v1.9, v1.10, v1.11, v1.12 และทั้งหมดยังเป็น stub
- [ ] วัด TTFT และต้นทุนบน staging ร่วมกับ May (P4-lite)
  - 13 พ.ย. แผนใหม่: หลัง demo (demo รันในเครื่อง · วัดตอน journey บน staging ใน S5)
  - ทำโดย Jam (1 พ.ย.) ช่วง solo · ทำได้บางส่วน
  - 1 พ.ย. (PR #99 · `specs/poc/reports/P4-lite.md`): วัดกับ Gemini จริงบน Vertex จากเครื่อง Jam (staging ยังเปิด live ไม่ได้) · `thinking: low` p95 3.87 s → `minimal` p95 1.20 s · 0.039 บาท/ข้อความ (`poc/P4-lite/cost.py` จาก log `ai_calls`) · `ai.yaml` 1.8 · เหลือ: วัดซ้ำบน staging `ttft.py --label staging-gemini` เมื่อหน้าเว็บส่ง token + `AUTH_REQUIRED=true` + env Supabase ของ api-staging
  - 1 พ.ย. (PR #103 · Jam ช่วง solo): rate limit ข้อความในห้องติว (`guards.rate_limit_messages_per_minute` · 429 `rate_limited`) + circuit breaker ต่อ provider ใน gateway (`gateway.circuit_breaker`) · `specs/features/ai/gateway-guards.md` · ก่อนเปิด live บน staging ยังเหลือ: `api-staging` ตรวจ token (`SUPABASE_URL`, `SUPABASE_ANON_KEY`, `AUTH_REQUIRED: "true"` · Junior), runtime SA (Junior), หน้า login (May)

**Done เมื่อ:** หน้า `/docs` แสดงครบทุก API และหน้าแชทของ May คุยกับ Gemini ผ่าน staging ได้

### S4 · 16–27 พ.ย.

- [ ] ⭐ demo D1 + D2: ตัดสิน login ใน demo และ Supabase ในเครื่อง (ภายใน จ. 16 พ.ย.)
- [ ] ⭐ demo ขั้น 1: env ของ API ชี้ Supabase ในเครื่อง (hook เปิดใน `supabase/config.toml` แล้ว) · ยืนยัน `tenant_id` ใน token · `AUTH_REQUIRED=true` วนได้กับหน้า login ของ May (UM-01)
- [ ] ⭐ demo ขั้น 3: `POST /exam-preps/{id}/materials` + `POST /materials/{id}/uploaded` + `POST /exam-preps/{id}/materials/confirm` จริง · signed upload URL · bucket + storage policy (migration ใหม่ + isolation test) (CM-03, CM-07)
- [ ] ⭐ demo ขั้น 5: `GET /exam-preps/{id}/scope` อ่าน DB · `POST /scope/confirm` เขียน `scope_versions` + `active_scope_version_id` (SM-09)
- [ ] ⭐ demo ขั้น 8: repository ของ `problems`, `attempts`, `topic_progress` (PM-01, PM-02, PM-06)
- [ ] ⭐ demo ขั้น 9: `POST /sessions/{id}/end` จริง (`ended_at` + สรุป) (TM-13, PM-05)
- [ ] P8-lite ร่วมกับทีม (review test ของ `compute_importance`)
  - 13 พ.ย. แผนใหม่: หลัง demo (ทำใน S4 หลัง 23 พ.ย.)
  - 8 พ.ย. test พร้อมให้ review ย้อนหลัง (PR #113 · `apps/api/tests/unit/test_stars.py`) · จดเวลาที่ใช้ใน `poc/P8-lite/metrics.md` §4 · test ที่ผิดจดใน §3
- [ ] อัปเดต architecture และ data model ตามผล PoC (D2, D3)
  - 13 พ.ย. แผนใหม่: หลัง demo (รอ P8-lite)
  - 1 พ.ย. (PR #101 · Jam ช่วง solo): `architecture.md` v1.2 ใส่ผล P1, P2, P3b, P4-lite แล้ว (model ของแต่ละ tier, embedding 768 มิติ, SymPy worker pool) · data model ได้ `0003` จาก P3 (PR #67) · เหลือ: อัปเดตอีกรอบหลัง P8-lite และ P2 ต่อเข้าห้องแชท
  - ทำโดย Jam (12 พ.ย.) ช่วง solo
  - 12 พ.ย. (PR #128): `architecture.md` v1.3 ตาราง "สร้างแล้วหรือยัง" ตรวจกับโค้ดบน main (P2 ต่อเข้าห้องแล้ว, ห้องติวบน DB #123, exam prep API #121, `domain/` stars + bkt + hint_ladder, canvas, เดโม่ในเครื่อง, login / staging ยังรอ #120) · `data-model.md` v1.4 แถว `0004` และเรื่องที่รอทีม (`attempts` เก็บจำนวน hint ถ้ารับข้อเสนอ AM-07) · ไม่มี migration ใหม่ · **ยังไม่ติ๊ก** (self-review): ข้อนี้ให้อัปเดตอีกรอบหลัง P8-lite ซึ่งยังไม่จบ · เหลือ: ดูผล P8-lite ว่าเปลี่ยน `compute_importance` หรือ input ของดาวไหม แล้วติ๊ก · Junior ดูย้อนหลังได้
- [ ] (ถ้ามีเวลา) ต่อ P1 + P2 เข้าหน้าแชท: ส่งรูปแล้วได้ verdict
  - 13 พ.ย. แผนใหม่: หลัง demo · demo ในเครื่องอ่านรูปจาก `.local/uploads` อยู่แล้ว · `ImageStore` บน Storage อยู่ใน S5 (journey บน staging)
  - ทำโดย Jam (8 พ.ย.) ช่วง solo · ทำได้บางส่วน
  - 8 พ.ย. (PR #114 · `specs/features/check/photo-check-in-room.md`): ส่งรูป → `extract_answer` → `ocr_preview` · ยืนยัน → checker ของ P2 → `verdict` → purpose ใหม่ `explain_check` อธิบายทันที (AM-07) · smoke บน Vertex ในเครื่อง 3 รูปจาก `evals/` verdict ตรง label 3/3 · ผ่าน interface `ImageStore` + `RoomState` (เก็บใน memory) · **บน staging ยังเป็น stub** จนกว่าจะมี Storage · เหลือ (Junior): `/uploads` จริง + bucket/policy + `ImageStore` ที่อ่าน Supabase Storage, บันทึก `messages` / `problems` / `attempts`, ตัดสินข้อเสนอใน spec §10 ข้อ 3–8 · api.md: 404/422 ของ `image_path` (spec §11)
- [ ] เตรียม staging สำหรับ demo รวม
  - 13 พ.ย. แผนใหม่: หลัง demo · demo 23 พ.ย. รันในเครื่อง · #120 และ journey บน staging ย้ายไป S5
  - 11 พ.ย. เป้าเปลี่ยนเป็น advisor update จันทร์ 16 พ.ย. (journey เดียวบน staging: login → exam prep → upload → topics → ห้องติว AI จริง → resume) · ลำดับ: 1) login + #120 2) exam prep API 3) บันทึก messages + resume 4) upload + Storage 5) ingestion (Jam)
  - 11 พ.ย. (PR #121 · `specs/features/exam-prep/create-exam-prep.md`): `POST`/`GET /exam-preps` บันทึกและอ่าน `exam_preps` จริงผ่าน JWT ของผู้ใช้ (RLS) · ไม่มี token + `AUTH_REQUIRED=false` ยังได้ stub (`X-Stub`) · api.md v1.14 · `503 db_unavailable` · เหลือ: #120 (รอหน้า login ของ May), ลำดับ 3–5
  - 12 พ.ย. (PR #123 · `specs/features/tutor/room-sessions-db.md`): ลำดับ 3 เสร็จ · ห้องติวที่มี token บันทึก `tutor_sessions` + `messages` จริง (RLS) และกลับมาเห็นประวัติได้ (TM-13) · เปิดห้องทักด้วย template ใน `config/messages.yaml` ไม่เรียก AI · ยังไม่มี `progress_card` / `problem` จนกว่าจะมี scope ที่ยืนยันแล้ว · api.md v1.15 · `0004` ขึ้น anyang-dev และ anyang-staging แล้ว · unit test ออก network ไม่ได้แล้ว (`tests/unit/conftest.py`) · แก้ 3 test ของ Jam ตาม AC-auth-real / AC-23 (Jam ยังไม่ ok) · เหลือ: #120 (รอหน้า login ของ May), ลำดับ 4–5

### S5 · 30 พ.ย.–11 ธ.ค.

- [ ] journey ของ demo บน staging: merge #120 · Storage + migration ขึ้น `anyang-staging` · `ImageStore` ที่อ่านรูปจาก Storage (demo ในเครื่องใช้ `.local/uploads`) · วัด TTFT บน staging (P4-lite)
- [ ] API ของบัญชี + persona บน DB: Google OAuth (UM-02) · preset และ custom persona (UM-03, UM-04, UM-05) · โปรไฟล์ (UM-08, UM-09)
- [ ] ไฟล์: note รายไฟล์, เพิ่มไฟล์ทีหลัง, ลบไฟล์ (CM-04, CM-05, CM-10)
- [ ] ขอบเขต: บันทึก `scope_changes` + change log (SM-06, SM-07, SM-08) · `topic_skills` (SM-12)
- [ ] DB ของ planner: `planner_decisions` + เก็บ stage ของ session (TM-04, TM-18)

### S6 · 14–25 ธ.ค.

- [ ] ลบบัญชีและข้อมูลทั้งหมด (UM-10)
- [ ] แก้บั๊กจาก demo S5

### Buffer · 28–31 ธ.ค. (เดิม 30 พ.ย.–4 ธ.ค.)

- [ ] ส่วน backend, DevOps, SaaS ในรายงานเทอม 1
- [ ] แก้บั๊กจาก demo S4
  - 13 พ.ย. แผนใหม่: ทำใน S4 หลังวิดีโอ 23 พ.ย. และหลัง demo รวม 27 พ.ย. (ไม่ต้องรอ Buffer)

---

## May · Frontend + UX

### S1 · 5–16 ต.ค.

- [x] ⭐ ตั้งเครื่องตัวเองตาม `setup.md` Part A (ได้คอมแล้ว 14 ต.ค.)
- [x] ⭐ ให้ Claude Code scaffold `apps/web` และตรวจผล (+ `pnpm build` ใน CI)
- [x] แก้ wireframe S05 (คำแนะนำการเขียน persona), S08 (ช่องนาทีต่อวัน), S15 (progress card) (D6)
- [x] เชื่อม Vercel กับ repo (root `apps/web`)
- [x] ร่วม review `specs/requirements/requirements.md` (D1)
- [x] รูปลายมือ 10 รูป (D8)
  - ส่ง 6 รูปให้ Jam แล้ว 19 ต.ค. ตามแผนใหม่ (คนละ 6 ใบ · ดู PR #11)

**Done เมื่อ:** wireframe 3 หน้าแก้เสร็จ และ `pnpm dev` ขึ้นหน้าแรกได้

### S2 · 19–30 ต.ค.

- [x] พิมพ์เฉลย LaTeX รายบรรทัดของรูปลายมือทุกรูป ลง `evals/handwriting/labels.jsonl` (ให้ P1)
- [x] Label หัวข้อ ดาว และ map ข้อสอบรายข้อของวิชา pilot ร่วมกับ Jam ลง `evals/topics/` (ให้ P3)
- [x] ตรวจ wireframe ทั้ง 27 หน้าว่าไม่มีส่วนที่ขัดกับ design ใหม่ (D6)
- [x] เริ่มหน้าแชท: layout, bubble ของ tutor/buddy/user, composer (พิมพ์ + ส่งรูป)
- [x] เขียนคำถาม 20 ข้อ + หน้าที่มีคำตอบ สำหรับวัด embedding (P3b) ลง `evals/topics/mth10101/retrieval_questions.md` (เทมเพลตและกติกาอยู่ใน branch `poc/P3b-embedding`) · คนเขียนต้องไม่ใช่ Jam · ส่งให้ Jam ภายใน จ. 26 ต.ค. · เสร็จ 21 ต.ค. (PR #46 เข้า #39): 20 ข้อ 19 หัวข้อ

**Done เมื่อ:** label ครบและส่งให้ Jam ก่อน ศ. 23 ต.ค. (Jam ต้องใช้รัน PoC) · คำถาม P3b ส่งภายใน จ. 26 ต.ค.

### S3 · 2–13 พ.ย.

- [ ] หน้าแชท P4-lite: อ่าน SSE ผ่าน `lib/sse.ts`, แสดงข้อความที่ไหลออกมา, render KaTeX, ส่งรูป
  - 13 พ.ย. แผนใหม่: ⭐ demo ขั้น 6–7 (หน้าห้องติวที่ใช้ใน demo · ส่วนใหญ่เสร็จแล้ว)
  - 20 ต.ค. stream จาก fake transport เสร็จ (PR #32 · `chat-streaming.md`) · เหลือ HTTP transport + upload รูปจริง เมื่อ `POST /sessions/{id}/messages` ของ Junior มา
  - 21 ต.ค. HTTP transport ต่อ API stub เสร็จ (PR #42 · `room-http.md`): เปิดห้อง/กลับเข้า session, ส่งข้อความ stream จาก API, ชื่อไฟล์รูปจาก `attachment_name` · ลองจริงในเครื่องผ่าน · เหลือ upload รูปจริง (รอ `/uploads` + api.md รอตัดสินข้อ 1) และทดสอบบน staging กับ AI จริง
  - 5 พ.ย. (PR #108 · `room-photo-send.md`): ทำโดย Jam ช่วง solo · ส่งรูปพร้อมข้อความกำกับ → การ์ดยืนยันลายมือ → ผลตรวจ ครบเส้นทางกับ stub · ลองในเบราว์เซอร์ผ่าน · ยังเป็น stub: ผลตรวจตายตัว ไม่ได้อ่านลายมือจริง และ `PUT` เข้า Storage ยังไม่เคยวิ่งจริง (เว็บข้ามเมื่อเห็น `X-Stub`) · เหลือ: `/uploads` จริง (Junior) และทดสอบบน staging กับ AI จริง · ปุ่มไมค์ยังปิด (`voiceEnabled`) · May ดู OQ 3–5 ใน spec ย้อนหลังได้
- [x] Generate type จาก `/openapi.json` (`pnpm gen:api`)
  - 21 ต.ค. (PR #41) · generate จาก stub ห้องติว api.md v1.2 · รัน `pnpm gen:api` ใหม่เมื่อ Junior เพิ่ม endpoint หรือทำตาม v1.3
- [x] Use case UC สมัคร และ UC upload → scope (D7)
- [x] เขียน report P4-lite ร่วมกับ Junior
  - ทำโดย Jam (1 พ.ย.) ช่วง solo · May + Junior ดูย้อนหลังได้ (report ของทั้งคู่)
  - 1 พ.ย. (PR #99): `specs/poc/reports/P4-lite.md` **ผ่านบางส่วน**: ต้นทุนและการสลับ provider ผ่าน · TTFT ในเครื่องผ่าน รอวัดบน staging · ใช้ผล AI จำลองของ May (#85) + Gemini จริงของ Jam · ยังต้องวัดซ้ำบน staging (ดูข้อ "วัด TTFT และต้นทุน" ของ Junior)
  - 31 ต.ค. วัด TTFT พื้นฐานบน `api-staging` ด้วย AI จำลองแล้ว (PR #85 · `poc/P4-lite/`): p95 0.15 s (ทั้ง stub และผ่าน gateway หลัง #93) · cold start 6.06 s · ในเบราว์เซอร์ข้อความแรกมี CORS preflight +0.17 s · เหลือ: วัดกับ Gemini จริงเมื่อ staging เปิด live, ต้นทุนต่อข้อความ, สลับ provider ด้วย config, `/poc-report P4-lite`

**Done เมื่อ:** คุยกับ AI บน staging แล้วเห็นตัวอักษรไหลออกมาและสมการ render ถูก

### S4 · 16–27 พ.ย.

- [x] P8-lite ร่วมกับทีม (review test)
  - 8 พ.ย. test พร้อมให้ review ย้อนหลัง (PR #113 · `apps/api/tests/unit/test_stars.py`) · จดเวลาที่ใช้ใน `poc/P8-lite/metrics.md` §4 · test ที่ผิดจดใน §3
  - 11 พ.ย. (PR #118) May review ย้อนหลังแล้ว (1 นาที · อ่านตาราง AC → test ที่ Claude สรุป ไม่ได้อ่านโค้ด test เอง): 27 AC มี test ครบ · ช่องโหว่ 2 (§10 ข้อ 9, 10 ไม่มี test) · comment ทำให้เข้าใจผิด 1 (AC-13) · เสนอ Jam แก้ใน PR ใหม่ · จดใน `metrics.md` §3, §4
- [x] Use case UC ติว และ UC ส่งคำตอบ ให้ครบ 4 UC (D7)
  - ทำก่อนกำหนด 21 ต.ค. (PR #36) · มีข้อเสนอแก้ AM-02, ai-orchestration และ api.md v1.3 รอ Junior + Jam review
- [ ] ⭐ demo ขั้น 1: หน้า login (email + password ตาม D1) · เก็บ session · ส่ง `Authorization` ทุก request (UM-01)
- [ ] ⭐ demo ขั้น 2: หน้ารายการการเตรียมสอบ + ฟอร์มสร้าง แทนหน้า template ของ Next (CM-01, CM-02)
- [ ] ⭐ demo ขั้น 3: หน้าอัปโหลดหลายไฟล์ + สถานะรายไฟล์ (CM-03, CM-07)
- [ ] ⭐ demo ขั้น 5: หน้า scope ต่อ API จริง + ยืนยัน (SM-09)
- [ ] เตรียมลำดับหน้าจอสำหรับ demo รวม
  - 13 พ.ย. แผนใหม่: ⭐ demo D4 + อัดวิดีโอ 21–22 พ.ย. (#125 เตรียมของช่วง live ใช้ต่อได้)
  - 21 ต.ค. ร่างแล้ว `docs/design/demo-flow.md` (PR #61): 15 นาที 7 ช่วง · ห้องติว live + wireframe คู่ผล PoC · คนพูดแบ่งตามงาน · ทางสำรอง + checklist ก่อน demo · เหลือเติมตัวเลข P2, P4-lite, P8-lite หลัง S3–S4 และให้ทีมตกลงลำดับ
  - 11 พ.ย. (PR #119) ร่างรอบ 2: live ย้ายมาห้องเดโม่ในเครื่อง May (staging เป็นโบนัส) · รวมช่วง 3+4 เป็น live 5:30 · ตัวเลข P1–P4-lite, P6-lite, P8-lite เติมแล้ว (P8-lite ยังไม่มี report · TTFT staging ยังไม่วัด) · **เหลือ: ทีมตกลงลำดับ** (ถามในกลุ่มแล้ว) · Jam ให้ role Vertex AI User แก่ May ก่อนซ้อม · May เตรียมรูปลายมือข้อ 2 ที่เขียนเอง

### S5 · 30 พ.ย.–11 ธ.ค.

- [ ] หน้า onboarding: Google login, เลือก tutor + buddy (preset และ custom), ชื่อเล่น/ระดับ, แก้ทีหลัง (UM-02, UM-03, UM-04, UM-05, UM-08, UM-09)
- [ ] หน้าไฟล์: ยืนยัน/แก้ประเภทที่ AI เดาพร้อม confidence, note รายไฟล์, เพิ่มไฟล์ทีหลัง, ลบไฟล์ (CM-06, CM-04, CM-05, CM-10)
- [ ] หน้า home: readiness + หัวข้อที่ยังไม่แม่นของแต่ละการเตรียมสอบ (PM-04)
- [ ] หน้า scope: แก้ผ่านแชทแล้วรายการอัปเดตทันที + change log (SM-06, SM-07, SM-08)
- [ ] ห้องติว: ขอดู progress กลางทาง, ข้อเสนอจบ session (TM-11, TM-12)

### S6 · 14–25 ธ.ค.

- [ ] ห้องติว: ข้อความของ buddy, ปุ่ม TTS, ปุ่ม mic ตอบด้วยเสียง (TM-05, TM-06, TM-09, TM-20) · mic ในหน้า scope (SM-06)
- [ ] หน้าลบบัญชี (UM-10)

### Buffer · 28–31 ธ.ค. (เดิม 30 พ.ย.–4 ธ.ค.)

- [ ] สไลด์นำเสนอ + ส่วน UI/UX ในรายงาน
- [ ] ซ้อม live demo

---

## Jam · AI + การวัดผล

### S1 · 5–16 ต.ค.

- [x] ⭐ ติดตั้งเครื่องมือและ Claude Code
- [x] ⭐ เลือกวิชาคณิต 1 วิชาสำหรับ P3 และหาชีท + ข้อสอบเก่า 2 ชุด · MTH10101, ดู `evals/topics/mth10101/sources.md`
- [x] ตรวจ `specs/system/ai-orchestration.md` และ `learning-model.md` ใน repo ให้ครบ (D2) · findings F1–F17 ใน PR #31 (F7 ไม่ต้องแก้) · แก้ 13 · เลื่อน 4 (F5 ภาพ → S4, F12 แถว P1 → หลัง report P1, F15 key ไฟล์สแกน → ingest S3, TM-10 → feature spec ห้องติว S3) · เพิ่ม §3.7 requirement → section
- [x] ตรวจ `config/learning.yaml` ว่าทุกค่ามีป้ายที่มา · ติดป้ายครบทุกค่า + เพิ่มแถวใน `learning-model.md` (ค่าไม่เปลี่ยน)
- [x] เขียนคู่มือ label golden set (verdict, error type, บรรทัดแรกที่ผิด) ใน `evals/README.md` · + คู่มือลายมือ P1 และคู่มือหัวข้อ P3 ใน `evals/topics/README.md`
- [x] ร่าง prompt `extract_answer/v1` (มีร่างแล้ว) และ `extract_topics_local/v1` · smoke test กับ sheet-02, sheet-03 ใน AI Studio ผ่าน
- [x] รวบรวมรูปลายมือจากทุกคนให้ได้ ≥ 30 รูป + ขอความยินยอมเพื่อน (D8) · 30 รูปจาก 5 คน ยินยอมครบ · ทุกรูปเขียนบน tablet ยังไม่มีรูปกระดาษ (ดู `evals/handwriting/README.md`)
- [x] เตรียมรายการงานวิจัยเรื่อง learning path และ progress tracking สำหรับคุยกับทีม (`learning-model.md` §10) · 23 รายการใน 7 ด้านที่ MVP ใช้ (`docs/research/learning-path.md`) · agenda 3 เรื่องรอคุย (`docs/research/agenda-learning-model.md`): BKT ระดับ skill, BKT vs logistic, ความพร้อม %

**Done เมื่อ:** มีรูป ≥ 30 รูปและไฟล์วิชา pilot ครบ

### S2 · 19–30 ต.ค.

- [x] P1: รันรูปทั้งหมดกับ Gemini, Claude, Mathpix · ให้คะแนนด้วย SymPy · วาด precision–recall ของ confidence · 30 รูปด้วย `gemini-3.5-flash-lite` อย่างเดียว (ไม่ใช้ Claude/Mathpix เพราะต้องเสียเงิน) · line accuracy 95.2% PASS · threshold ของ confidence FAIL · PR curve เป็นตารางใน `score.json` ยังไม่ได้วาดกราฟ · report: `specs/poc/reports/P1.md`
- [x] P3: ingest → A5 → A6 → A7 → `compute_importance` · เทียบกับ label · ลอง embedding 2–3 ตัวกับคำถาม 20 ข้อ
  - P3b เสร็จ 21 ต.ค. (PR #39): `gemini-embedding-2` ที่ 768 มิติ recall@4 95% (bge-m3 45%) · `Gateway.embed` + `embedding.dimensions: 768` · เหลือ P3a (PR #37)
  - P3a รันแล้ว 21 ต.ค. (PR #37) · **ไม่ผ่านเป้า:** flash-lite หัวข้อตรง 1/27 · flash ได้ถึง A5 (56%) แต่ A6 ไม่ได้คำตอบที่ผ่าน schema บน free tier (0/20) · สูตรดาว + map ของทีม ★★★ 83% ผ่าน · ใช้ fallback ปรับ prompt A5/A6 และวัดใหม่บน Vertex (รอ GCP #20)
- [x] Report P1 และ P3 ด้วย `/poc-report`
  - P1 เสร็จแล้ว (`specs/poc/reports/P1.md`) · P3 เสร็จ 21 ต.ค. (`specs/poc/reports/P3.md`, PR #37)
- [x] อัปเดต `config/learning.yaml` (`ocr.confirm_below_confidence`, `stars.*`) และ `config/ai.yaml` (model ที่เลือก) ผ่าน PR
  - ส่วน ocr เสร็จแล้ว (PR #45): `ocr.always_confirm: true` แทน threshold · AM-02 ยืนยันทุกครั้ง (ทีมตกลง)
  - 21 ต.ค. (PR #60): `stars.*` ค่าเดิม ติดป้ายผล P3 · `ai.yaml` v1.2: vision = flash-lite (P1), mid = flash (P3), main = flash ชั่วคราว (A6 รอวัดบน Vertex), embed = gemini-embedding-2 · small ยัง TODO · `embedding.dimensions: 768` อยู่ใน PR #39

**Done เมื่อ:** ตัดสินแล้วว่าใช้ provider ไหนอ่านลายมือ และใช้ embedding ตัวไหน

### S3 · 2–13 พ.ย.

- [x] Label golden set คำตอบ 50 ข้อ (D8)
  - ทีมตกลง 21 ต.ค. (PR #51): คน label คือ May หรือ Junior ไม่ใช่ Jam เพราะ Jam ทำ P2 (`evals/README.md` "กฎ") · Jam เตรียมใบงาน `evals/answers/worksheet.md` แล้ว (รูป 30 ข้อ + ช่องคำตอบพิมพ์ 20 ข้อ) · เหลือ: เขียนคำตอบพิมพ์ 20 ข้อตามโควตาใน `evals/README.md` "ใบงาน" และ label ครบ 50 ข้อ
  - 21 ต.ค. เสร็จ 50/50 (PR #52) · ทีม (May + Jam) ตกลงให้ AI ร่าง label และคำตอบพิมพ์ ans_031–050 (writer `w06`) · หมายเหตุอยู่หัว `worksheet.md` · ตอนอ่านผล P2 ต้องคำนึงว่า label อาจเอนไปทางเดียวกับ checker ที่เป็น LLM · แก้ `handwriting/labels.jsonl` hw_018 ตามรูป (Jam อนุญาต)
- [x] SymPy service `app/math/`: parse LaTeX, เทียบทีละบรรทัด, expression / factored / equation, subprocess + timeout จาก config · ย้ายให้ Jam 21 ต.ค. (ทีมตกลง · ใกล้กับ P2) · รูปแบบผลตกลงไว้ใน `specs/features/check/merge-rules.md` §3 · Junior review เพราะอยู่ใน `apps/api/`
  - 28 ต.ค. (PR #75 · ทำก่อนกำหนด): spec `specs/features/check/sympy-service.md` + `app/math/sympy_service.py` · worker ที่เปิดค้างไว้ (`checker.sympy_workers`) + timeout จาก config · golden set 50 ข้อ: SymPy ตัดสินได้ 45 ข้อ ตรงกับ label 45/45 · อีก 5 ข้อ (implicit dy/dx 3, จบไม่ครบ 1, solveset แก้ไม่ได้ 1) ส่งให้ LLM
- [x] P2: merge rules + LLM classifier (`prompts/check_answer/v1`) ใช้ SymPy service
  - 21 ต.ค. merge rules เสร็จ (PR #68): spec `specs/features/check/merge-rules.md` + `app/domain/checker.py` · รูปแบบผลของ SymPy service ตกลงกับ Junior แล้ว · เหลือ prompt `check_answer/v1` และต่อกับ SymPy service
  - 28 ต.ค. SymPy service เสร็จ (PR #75) · เหลือ prompt `check_answer/v1` (ต้องทำเรื่อง `first_wrong_line` ของข้อ wrong_method ที่ SymPy มองว่าทุกบรรทัดถูก เช่น ans_037, ans_038) และ checker service ที่ต่อ SymPy + LLM + merge
  - 31 ต.ค. eval ของ PR #80 บน free tier ได้ 23/50 แล้วติด quota รายวัน · จะรันใหม่ครบ 50 ข้อบน Vertex หลัง PR #87
  - 31 ต.ค. เสร็จ (PR #80): spec `specs/features/check/check-answer-classifier.md` + prompt `check_answer/v1` + `app/services/checker.py` + `evals/run_checker.py` · รันบน Vertex 50 ข้อ: **verdict 100%, error_type 96.4% (27/28), first_wrong_line 100% (24/24) ผ่านเป้าทั้ง 3** · SymPy ตัดสิน verdict 45 ข้อ LLM 5 · พลาดข้อเดียว ans_039 (`wrong_method` → `prerequisite`) · `ai.yaml` 1.3 `thinking: low` · ผลอยู่ที่ `evals/answers/results/v1.json` · เหลือ Report P2 (PR #82)
- [x] Script `evals/run_eval.py` ออกคะแนน verdict, error type, บรรทัดผิด · เสร็จก่อนกำหนด (21 ต.ค. · PR #47) · ให้คะแนนจากไฟล์ prediction (`--predictions`) · นิยาม metric ใน `evals/README.md` "การให้คะแนน" · ต่อกับ checker จริงตอนทำ P2 · การรันใน CI เมื่อ prompt เปลี่ยน (§2.11) รอ Junior
- [x] Provider `vertex` ใน gateway ใช้เครดิต Free Trial ของ `anyang-513006` (เพิ่ม 31 ต.ค. · `infra/README.md` "งาน AI gateway ใน S3") · PR #87 · spec `specs/features/ai/gemini-vertex.md` · ADC ไม่มี key file · smoke บน Vertex ผ่าน (`gemini-3.5-flash`, `global`, 4.8 วินาที) · เหตุผล: free tier ของ AI Studio ได้ 20 request/วัน/model รัน P2 ได้แค่ 23/50 · Junior ok ให้แก้ `apps/api/app/ai/`
- [x] Report P2
  - 31 ต.ค. (PR #82): `specs/poc/reports/P2.md` · **ผ่าน** (Jam ตัดสิน): 6 error types, prompt v1, Vertex · ไม่ต้อง fallback 4 แบบ · บรรทัดผลใน `specs/poc/README.md` · งานต่อก่อนเข้าห้องแชท: hint sign flip ใน job เดียวกับ SymPy, กติกา §2.5 ของ `CheckAnswerResult`
- [x] ⭐ API ตรวจ Supabase JWT ทุก endpoint: อ่าน `Authorization: Bearer <jwt>` (api.md "Auth") → ได้ `tenant_id`, `user_id` → ตั้ง `ai_call_context` และส่ง JWT ต่อให้ Supabase ให้ RLS ทำงาน · ไม่มีหรือผิด → 401
  - เพิ่ม 1 พ.ย. (Jam รับเอง · งาน backend จึงชวน Junior ดูย้อนหลัง) · ⭐ เพราะขวาง 3 อย่าง: แถวใน `ai_calls` (`ai-calls-log.md`), การบันทึก `messages` (`tutor-reply-stream.md` §9) และการเปิด `AI_PROVIDER=live` บน api-staging (⚠️ ใน `infra/README.md` · ต้องเปลี่ยน runtime SA ด้วย)
  - 1 พ.ย. เสร็จ (PR #98 · `specs/features/platform/api-auth.md`): `app/auth.py` ตรวจด้วย `get_claims` ของ Supabase Auth (ES256 กับ JWKS ที่ cache ไว้ · HS256 ของ Supabase ในเครื่องถาม Auth server) · `tenant_id` จาก claim ของ hook + `user_id` จาก `sub` · 401 `missing_token` / `invalid_token` · router ห้องติวทั้งหมดผ่าน `get_auth` (test ไล่ทุก endpoint) · แชทที่มี token ได้แถวใน `ai_calls` · `get_user_db` ส่ง JWT ของ user ให้ RLS · env ใหม่ `AUTH_REQUIRED` (staging และ `.env.example` = `false`) · `api.md` v1.5
  - เหลือก่อนบังคับบน staging: หน้าเว็บ login + ส่ง token (May) · `api-staging` ใส่ `SUPABASE_URL` / `SUPABASE_ANON_KEY` แล้วตั้ง `AUTH_REQUIRED: "true"` (Junior · `anyang-staging` ต่อไม่ได้ 1 พ.ย.)

**Done เมื่อ:** มีตัวเลข 3 ตัวของ P2 เทียบกับเป้า

### S4 · 16–27 พ.ย.

- [x] ⭐ demo ขั้น 4: ingestion ใน `apps/api` (งานเบื้องหลัง: classify → อ่านไฟล์ → chunk + embed → สกัดหัวข้อ → `compute_importance`) ลง `materials`, `chunks`, `topics`, `topic_sources` · `GET /exam-preps/{id}/ingestion` จริง (SM-01, SM-03, SM-04, CM-06, AI-08) · เริ่มก่อนข้ออื่น
  - 13 พ.ย. (PR #130 · `specs/features/scope/ingestion.md`): pipeline ของ P3 อยู่ใน `apps/api` แล้ว · classify (prompt ใหม่ `classify_material/v1`) · อ่าน/ตัดรายข้อ/chunk/embed ทีละไฟล์ · A5 → A6 → A7 → `compute_importance` ต่อ prep · `GET /ingestion` อ่าน DB · migration `0005` (`ingestion_jobs.exam_prep_id`) ขึ้นแค่ในเครื่อง **Junior: ดูแล้ว `db push`** · รันจริงบน Vertex กับ MTH10101: หัวข้อ 20/27, ★★★ 9/12 (P3 10/12 · Jam รับผล · ลองส่ง kind `exercise` หลัง demo), map 70%, ≤ 1.44 นาทีต่อไฟล์ · Vertex embed ทีละข้อความ (`embedding.batch_size: 1`) · **ต่อเข้า demo:** endpoint materials ของ Junior (ขั้น 3) เรียก `classify_material` และ `get_ingestion_runner().start(prep_id)` หลังยืนยันไฟล์ · bucket ชื่อ `materials`
- [x] ⭐ demo ขั้น 6: ห้องติวในทางที่มี token: คำทัก `open_session` + การ์ดจาก DB + เลือกหัวข้อด้วยกฎง่าย + `generate_problem` ที่ SymPy ตรวจเฉลยแล้ว (คลังโจทย์เป็นทางสำรอง · D3) (TM-01, TM-15, AM-11)
  - 13 พ.ย. (PR #131 · `specs/features/tutor/room-problems-db.md`): เปิดห้องที่มี token + prep ที่มีหัวข้อ → การ์ดจาก DB → `open_session/v2` บอกหัวข้อและเหตุผล → โจทย์จาก `generate_problem/v1` ที่ SymPy ยืนยันเฉลยแล้ว ลง `problems` (โจทย์ค้างใช้ซ้ำ) · `tutor_reply` รู้โจทย์ค้าง · รันจริงกับ 34 หัวข้อ MTH10101: ยืนยันผ่าน 71% ภายใน 3 รอบ (หัวข้อหลักของ demo ผ่านรอบแรก · Jam รับผล) · คลังโจทย์สำรองและให้ SymPy อ่านอนุพันธ์อันดับสูงเป็นงานหลัง demo · **การ์ดโจทย์หายเมื่อรีเฟรชหน้า (May · spec §10 ข้อ 3)** · ตรวจคำตอบในทางนี้คือขั้น 7
- [ ] ⭐ demo ขั้น 7: `typed_answer` + ตรวจ + รูป/canvas ในทางที่มี token (TM-06 ส่วนพิมพ์และรูป, AM-01–07) · hint ladder เฉพาะ `APP_ENV=local` ตาม `demo-room.md` §2 K (AM-07 ยังเป็นข้อเดิมจนกว่าทีมตัดสิน)
- [ ] ⭐ demo ขั้น 8–9: BKT ลง `attempts` / `topic_progress` + การ์ดจาก DB (PM-01–04) · สรุป session ด้วย `session_summary` (PM-05)
- [ ] เดโม่ห้องติวที่ใช้ได้จริงในเครื่อง ให้อาจารย์ดูก่อนทำต่อ (อาจารย์ขอ 9 พ.ย. · เพิ่มเอง)
  - 13 พ.ย. แผนใหม่: ⭐ demo ขั้น 6–7 · ของในเดโม่นี้ (คำทัก, ตรวจ, hint ladder, BKT) ต้องย้ายเข้าทางที่มี token (ข้อใหม่ข้างล่าง) · ที่เหลือเดิม (canvas ในเบราว์เซอร์, วิดีโอ) รวมเข้า demo end to end · iPad หลัง demo
  - 9 พ.ย. (PR #115 · `specs/features/tutor/demo-room.md` + `specs/features/planner/bkt-mastery.md`): `APP_ENV=local` วนได้จริงกับ Vertex · อัปโหลดรูปในเครื่อง · โจทย์ 5 ข้อ · BKT จริง (`app/domain/bkt.py`) ในการ์ดตอนเข้าห้อง · tutor ทักก่อน (`open_session`) · รู้โจทย์และจำบทสนทนา (`tutor_reply/v2`) · พิมพ์คำตอบแล้วตรวจ (`typed_answer`) · แสดงวิธีทำทีละขั้นทุกครั้ง (`explain_check/v2`) · ส่งแค่คำตอบยังไม่ผ่าน (`checker.min_working_lines`) · วิธีเปิดอยู่ใน spec §12 · staging ยังเป็น stub
  - 9 พ.ย. (PR #117 · `specs/features/tutor/answer-canvas.md`): canvas เขียนคำตอบอยู่ท้ายแชทเมื่อมีโจทย์ค้าง (เมาส์ / Apple Pencil / นิ้ว · ใส่รูป · ส่งเป็น PNG ทางเดิมของรูป) · ลองบนคอมแล้ว · iPad ยังไม่ได้ลอง · นับวิธีทำเป็นขั้น และให้โจทย์เดิมซ้ำเมื่อขาดวิธีทำ · ตัด `**` ในแชท · May ตัดสินดีไซน์แล้ว 12 พ.ย. (PR #122 · spec §10): ตำแหน่ง ขนาด เครื่องมือคงเดิม · เพิ่มภาพย่อใน bubble และ "ถ่ายใหม่" พาไป canvas ทำแล้ว 12 พ.ย. (PR #124)
  - 12 พ.ย. (PR #127 · `demo-room.md` §2 K): hint ladder ในเดโม่ในเครื่อง · ส่งขั้นที่ถูกแต่ยังไม่จบได้ "ทำต่อ" (ไม่มี ✓/✗) · ผิดครั้งที่ 1 ชี้บรรทัด ครั้งที่ 2 บอกสูตร + ทำให้ดู 1 ขั้น ครั้งที่ 3 เฉลย (`tutoring.max_hints_before_solution: 2` [C]) · พิมพ์ "ไม่ได้จริงๆ" เฉลยทันที · BKT นับครั้งเดียวต่อโจทย์ ถูกหลัง hint สุดท้ายไม่นับ · ระหว่างใบ้ tutor ไม่ได้เห็นเฉลย (AM-13) · `explain_check/v3`, `typed_answer/v2` · smoke บน Vertex 6 ขั้นผ่าน (Claude · ไม่ผ่านเบราว์เซอร์) · staging ยังเฉลยทันที · **ข้อเสนอแก้ AM-07 รอทีมตอบ**
  - เหลือ: ลอง ladder บน canvas ในเบราว์เซอร์ · อัดวิดีโอสำรอง · ลองบน iPad
- [ ] P8-lite ร่วมกับทีม (เป็นเจ้าของ spec `compute_importance`)
  - 13 พ.ย. แผนใหม่: หลัง demo (ทำใน S4 หลัง 23 พ.ย.)
  - 31 ต.ค. ส่วน spec เสร็จก่อนกำหนด (PR #89): `specs/features/scope/compute-importance.md` approved หลังเทียบกับผล P3 · AC 13 → 27 · test plan 19 ชื่อ · ใบเก็บ metrics `poc/P8-lite/metrics.md` · เหลือทำด้วยกันใน S4: `/spec-to-tests` → review test → `/implement-feature` → merge
  - 8 พ.ย. (PR #113 · Jam ช่วง solo): `/spec-to-tests` → Jam review test → `/implement-feature` → merge · `app/domain/stars.py` + 32 test (`test_stars.py`, AC-19 ใน `test_settings.py`) · agent เขียน 100% · red → green 3 รอบ · บั๊กก่อน merge จดใน `poc/P8-lite/metrics.md` §3 · เหลือ: Junior review test ย้อนหลังแล้วจดเวลาใน metrics §4 (May เสร็จ 11 พ.ย. · PR #118), กรอก §6, `/poc-report P8-lite`
- [x] อัปเดต threshold ใน AI flow specs และ `learning-model.md` ตามผล P1 P2 P3 (D2)
  - 28 ต.ค. (PR #73 · ไม่ได้มาจากผล PoC แต่มาจากการทบทวน design): `learning-model.md` v1.2 เพิ่มระดับเป้าตามดาวและเพดาน mastery (`mastery_eff`) · `learning.yaml` 1.2 · `ai-orchestration.md` v1.2 · TM-16, PM-03 ใน `requirements.md` v1.3 · เหลือปรับค่าตามผล P1 P2 P3
  - 31 ต.ค. เสร็จ (PR #91): งานนี้ไม่เปลี่ยนค่าไหน (ค่าเดียวที่ PoC เปลี่ยนคือ `ocr.always_confirm` จาก P1 ทำไปแล้วใน PR #45) · แก้ป้ายที่มาใน `learning.yaml` 1.4, `ai.yaml` 1.4, `learning-model.md` v1.3 §8–9 · `ai-orchestration.md` v1.4 ใส่ model ที่วัดแล้วของ tier mid, main (ชั่วคราว), vision, embed ใน §2.10 (small ยัง TODO เพราะยังไม่ได้วัด) และผล PoC (§3.6) · PDF สแกนใช้ A2b ทั้งไฟล์ (§2.3.7) · ที่วัดไม่ได้ระบุว่าจะวัดเมื่อไหร่: P3a บน Vertex ใน S4 (ข้อถัดไป) · สัญญาณแยกบรรทัดที่ OCR อ่านผิด เทอม 2 · `numeric_rel_tolerance` และ `max_generate_retries` วัดตอนมี feature
- [x] วัด P3a ใหม่บน Vertex: prompt A5/A6 ที่ปรับแล้ว (fallback ของ P3) · ตัดสิน model ของ tier `main` · เช็ค token out ของ `merge_topics` (คำตอบบน free tier ไม่ผ่าน schema ทั้งคู่) · วัด A2b `vision_extract_pages` บน flash-lite (P3 รันบน flash) · เติมผลใน `P3.md`, `ai-orchestration.md` §2.10 และ §3.6, `docs/report/ai-evaluation.md` §3
  - เพิ่ม 31 ต.ค. (PR #91): ทำก่อน demo รวม เพราะ demo ต้องแสดง upload → scope
  - 31 ต.ค. เสร็จ (PR #94 · `specs/poc/reports/P3.md` §7): **ผ่านบางส่วน** (Jam ตัดสิน) · `extract_topics_local/v2` + `merge_topics/v2` บน Vertex: ★★★ ทั้ง pipeline 10/12 = 83% ผ่าน · ≤ 3 นาที/ไฟล์ ผ่าน (A6 รวมทั้งวิชา 87 วินาที · A5 ต่อชีทไม่เกิน 15 วินาที) · หัวข้อตรง 20/27 = 74% (เป้า 80%) · A6 v1 รวมหัวข้อเกิน (51 → 17) และชนเพดาน 16,000 token → `merge_topics` `max_tokens` 32,000 · tier main และ small = `gemini-3.5-flash` · A2b บน flash-lite 14 หน้า 12–27 วินาที · flash-lite ไม่เหมาะกับ A4 (JSON ที่มี LaTeX พัง) · `ai.yaml` 1.7 · วัดรอบละครั้ง วิชาเดียว
- [x] Test strategy 1 หน้าใน `specs/system/` · ทำก่อนกำหนด 21 ต.ค. (PR #55) · `specs/system/test-strategy.md` · §5 มีงานเสนอให้ Junior 2 ข้อ (`evals/` เข้า CI ใน S3, isolation test ทุกตารางใน S4) · Junior ตกลงแล้ว 21 ต.ค.
  - 31 ต.ค. v1.1 (PR #86): อัปเดตจำนวน test ต่อชั้นตาม `main` (`tests/unit/` 346 · web 242 · `evals/` 69 · isolation 3/27 ตาราง เท่ากับ v1.0 · ตัวเลข 6/27 ของร่าง 28 ต.ค. นับแถว seed ผิด) · หลักการไม่เปลี่ยน

### S5 · 30 พ.ย.–11 ธ.ค.

- [ ] planner เต็ม: เลือกหัวข้อ + เหตุผล + mode (TM-01, TM-02, TM-18) · ลำดับ prerequisite (SM-02)
- [ ] stage machine: probe → teach → Verify ด้วยโจทย์แบบเดียวกัน → practice (TM-03, TM-04, AM-08, AM-09) · ผ่านตาม skill (TM-16, SM-12)
- [ ] prompt ของ persona (`persona_extract`, `persona_preview`) และ scope edit ผ่านแชท (UM-05, SM-06)
- [ ] answer-leak check แบบ deterministic ใน gateway (AM-13)
- [ ] ข้อเสนอ hint ladder (AM-07) ตามที่ทีมตัดสิน

### S6 · 14–25 ธ.ค.

- [ ] buddy ตามกฎของ code (TM-05) · ทบทวนตามรอบ (TM-17) · Park (TM-19)
- [ ] grounding: คำถามนอก scope และไม่สอนวิธีที่ไม่มีในชีท (SM-10, SM-11) · STT + TTS (TM-06, TM-09, SM-06)
- [ ] สัญญาณความเครียดรุนแรง (SA-09) · golden set ของ prompt ในห้องติว (explain_check, typed_answer, open_session)
- [ ] provider ที่ 2 ใน gateway (Claude) ให้สลับด้วย config (AI-02)

### Buffer · 28–31 ธ.ค. (เดิม 30 พ.ย.–4 ธ.ค.)

- [x] ส่วน AI, การวัดผล และงานวิจัยรองรับในรายงาน
  - ทำก่อนกำหนด 28–31 ต.ค. (PR #84): `docs/report/ai-evaluation.md` 4 หัวข้อ (สถาปัตยกรรม AI · วิธีวัดผล · ผล PoC P1 P2 P3 · งานวิจัยรองรับ learning model) · เหลือย้ายเข้า template รายงานของภาควิชาตอน Buffer (path ใน repo อาจต้องเป็นภาคผนวกหรือลิงก์) · ถ้ามีผล P8-lite หรือ P3a วัดใหม่บน Vertex ต้องเติม §3
- [ ] สรุปตัวเลขของ P8-lite สำหรับ Self-Assessment

---

## ทั้งทีม

| Sprint | งานร่วม |
|---|---|
| S1 | review `requirements.md` แล้วอัปเดต SRS เป็น v1.1 (D1) · ตกลง Claude Code subscription · คุยเรื่องงานวิจัยรองรับ learning path |
| S2 | ตรวจ label ของกันและกัน (คน label ไม่ใช่คนทำ PoC) |
| S3 | ทดลองใช้หน้าแชทแล้วจด feedback |
| S4 | **P8-lite:** `/spec-to-tests` → review test ด้วยกัน → `/implement-feature` → เก็บ metrics |
| S4 (เพิ่ม 13 พ.ย.) | ⭐ demo end to end: ต่อทุกขั้นในเครื่องเดียว พฤ. 19 พ.ย. · ซ้อม ศ. 20 · อัดวิดีโอ 21–22 · ส่ง จ. 23 พ.ย. |
| S5 | journey บน staging · ลองใช้การติวตามแผนแล้วจด feedback |
| S6 | ไล่ Must ที่เหลือทุกข้อ (ตารางแผน Must) · ปิดบั๊ก |
| Buffer | รายงานเทอม 1 + ซ้อมนำเสนอ (28–31 ธ.ค.) |
