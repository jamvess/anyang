# Checklist ราย sprint ของแต่ละคน · เทอม 1

อัปเดต 14 ต.ค. 2569 · อ้างอิงแผนเทอม 1 ฉบับลด scope

**วิธีใช้:** ไฟล์นี้บน `main` คือสถานะจริงของทีม ติ๊กข้อของตัวเอง**ใน PR เดียวกับงานที่ทำเสร็จ** พอ merge ทุกคนจะเห็นหลัง `git pull` (`/work-done` ติ๊กให้อัตโนมัติ · ดู `daily-workflow.md`)

| Sprint | วันที่ | เป้าหมาย | Demo |
|---|---|---|---|
| S1 | 5–16 ต.ค. (หยุด 13 ต.ค.) | เตรียมพื้น: repo, CI, specs, เก็บข้อมูลจริง | ศ. 16 ต.ค. |
| S2 | 19–30 ต.ค. (หยุด 23 ต.ค.) | พิสูจน์ความเสี่ยงใหญ่: อ่านลายมือ + สกัดหัวข้อ + deploy อัตโนมัติ | ศ. 30 ต.ค. |
| S3 | 2–13 พ.ย. | ตรวจคำตอบ + chat AI ที่ stream ได้ | ศ. 13 พ.ย. |
| S4 | 16–27 พ.ย. | SDD/TDD + ปิดงาน design + demo รวม | ศ. 27 พ.ย. |
| Buffer | 30 พ.ย.–4 ธ.ค. | รายงาน + นำเสนอ | |

> S1 เริ่มไปแล้ว 1 สัปดาห์ ถ้างาน S1 ยังไม่เริ่ม ให้ทำข้อที่มี ⭐ ก่อน เพราะเป็นงานที่คนอื่นรออยู่

---

## Junior · Backend + DevOps

### S1 · 5–16 ต.ค.

- [x] ⭐ สร้าง repo, วาง starter files · branch protection เปิดแล้ว 20 ต.ค. (ruleset `main` id 25374094 · ต้อง approve 1 คน + CI `api`, `api-integration`, `web` ผ่าน · ห้าม force push และลบ branch · ไม่มี bypass) · repo เป็น public
- [x] ⭐ ให้ Claude Code scaffold `apps/api` และตรวจผล
- [x] ⭐ `npx supabase init` + `db push` `0001_init.sql` ขึ้น Supabase cloud `anyang-dev` + เปิด custom access token hook
- [x] GitHub Actions รันครบ 3 job และเขียวบน `main`
- [ ] สร้าง GCP project, เปิด API, Artifact Registry, Secret Manager (`infra/README.md`)
- [ ] สร้าง Supabase project `anyang-staging`
  - ⚠️ รอ Jam (เจ้าของ Vercel): (ก) เปลี่ยน Vercel **Preview** env (`NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`) ให้ชี้ `anyang-staging` (`sfapuygntxuelsxsgkay`) แล้ว redeploy · (ข) ตรวจ **Production** env ถ้ายังชี้ project Tokyo ที่ลบแล้ว (`xztfzskxusykuqtpomrf`) แปลว่า `anyang-amber.vercel.app` พังอยู่ ต้องแก้ก่อน demo 30 ต.ค. (ดู `infra/README.md` หัวข้อ Frontend · Vercel)
- [ ] ให้สิทธิ์ทีม: GitHub collaborator + Supabase org (เจ้าของ repo ทำ, `setup.md` A0), GCP (Jam: Vertex AI User)
- [x] แก้ `.github/CODEOWNERS` เป็น username จริง · + เพิ่ม `/.github/` ให้ Junior ตาม `roles.md` (19 ต.ค.)
- [x] ตั้งเครื่องตัวเองตาม `setup.md` Part A · ผ่านเช็คลิสต์ A6 ครบ 5 ข้อ (19 ต.ค.)
- [ ] ตรวจ `specs/system/architecture.md` ให้ตรงกับที่ตั้งจริง (D2)
- [ ] ร่วม review `specs/requirements/requirements.md` (D1)
- [ ] รูปลายมือ 10 รูป (D8)

**Done เมื่อ:** ทุกคน clone แล้วรันได้ตาม `setup.md` A6 และ CI เขียวบน `main`

### S2 · 19–30 ต.ค.

- [ ] Cloud Build trigger: merge → deploy `api-staging` อัตโนมัติ (P6-lite)
  - ⚠️ ต้องตั้ง `CORS_ALLOW_ORIGINS` และ `CORS_ALLOW_ORIGIN_REGEX` ใน env ของ `api-staging` (`--set-env-vars` ใน `infra/cloudbuild.yaml`) ไม่งั้น Vercel preview เรียก staging ไม่ได้ (ค่าดู `.env.example` · PR #49) · ใน `cloudbuild.yaml` ต้องเขียน `$` ของ regex เป็น `$$` เพราะ Cloud Build ใช้ `$` แทนค่าตัวแปร · `--set-env-vars` แยกตัวแปรด้วย `,` แต่ `CORS_ALLOW_ORIGINS` ก็คั่นด้วย `,` เหมือนกัน ถ้ามีมากกว่า 1 origin ให้ใช้ตัวคั่นแบบกำหนดเองของ gcloud เช่น `--set-env-vars="^@^CORS_ALLOW_ORIGINS=a,b@CORS_ALLOW_ORIGIN_REGEX=..."` หรือตั้งผ่าน `--env-vars-file`
- [x] `test_SA06_tenant_isolation` รันใน CI (P6-lite) · เสร็จก่อนกำหนดใน S1
- [x] ตรวจว่าไม่มี secret ใน git history · เสร็จก่อนกำหนดใน S1 (15 ต.ค.)
- [ ] ปรับ `schema.sql` ตามที่เจอระหว่าง P3 + วาด ERD (D3)
  - 20 ต.ค. วาด ERD ใหม่แล้ว 3 รูป ครบ 27 ตาราง (+ `auth.users` วาดไว้ให้ดูความสัมพันธ์) และ FK ทั้ง 45 ตัว (PR #30) · เหลือแก้ schema ตามผล P3 (จดไว้ 5 ข้อใน `data-model.md`)
  - 21 ต.ค. migration `0002` เพิ่ม `messages.attachment_name` (api.md v1.3) + ERD รูป 3 (PR #43) · ตรวจ 5 ข้อของ P3 แล้ว ยังยืนยันไม่ได้สักข้อเพราะ A6/A7 ยังไม่เคยรันผ่าน (สถานะอยู่ใน `data-model.md`) · เหลือแก้ schema หลังมี report P3a
- [ ] ช่วย Jam ทำ ingest pipeline ของ P3: อ่าน PDF (PyMuPDF), ตัด chunk, เก็บลง DB
- [ ] เขียน report P6-lite ด้วย `/poc-report P6-lite`

**Done เมื่อ:** merge PR แล้ว staging อัปเดตเองภายใน 10 นาที และ isolation test ผ่าน

### S3 · 2–13 พ.ย.

- [ ] SymPy service `app/math/`: parse LaTeX, เทียบทีละบรรทัด, expression / factored / equation, subprocess + timeout จาก config (ให้ Jam ใช้ใน P2)
- [ ] AI gateway แบบ lite `app/ai/`: `ai.call()`, provider Gemini + fake, อ่าน `config/ai.yaml`, log `ai_calls`
- [ ] Endpoint SSE `POST /sessions/{id}/messages` ที่ stream จาก gateway (P4-lite)
- [ ] เขียน router หัวฟังก์ชันของทุก API ใน `specs/system/api.md` ให้หน้า `/docs` ครบ (D5)
  - 20 ต.ค. api.md v1.2 ห้องติว (PR #35) + stub 4 endpoint ของห้องติวที่คืน fixture ของ May พร้อม `X-Stub: true` (PR #38) · `/docs` แสดง schema ของ `Room`, `Message`, event SSE และ `ErrorResponse` · เหลือ endpoint กลุ่มอื่นใน api.md
- [ ] วัด TTFT และต้นทุนบน staging ร่วมกับ May (P4-lite)

**Done เมื่อ:** หน้า `/docs` แสดงครบทุก API และหน้าแชทของ May คุยกับ Gemini ผ่าน staging ได้

### S4 · 16–27 พ.ย.

- [ ] P8-lite ร่วมกับทีม (review test ของ `compute_importance`)
- [ ] อัปเดต architecture และ data model ตามผล PoC (D2, D3)
- [ ] (ถ้ามีเวลา) ต่อ P1 + P2 เข้าหน้าแชท: ส่งรูปแล้วได้ verdict
- [ ] เตรียม staging สำหรับ demo รวม

### Buffer · 30 พ.ย.–4 ธ.ค.

- [ ] ส่วน backend, DevOps, SaaS ในรายงานเทอม 1
- [ ] แก้บั๊กจาก demo S4

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
- [ ] เขียนคำถาม 20 ข้อ + หน้าที่มีคำตอบ สำหรับวัด embedding (P3b) ลง `evals/topics/mth10101/retrieval_questions.md` (เทมเพลตและกติกาอยู่ใน branch `poc/P3b-embedding`) · คนเขียนต้องไม่ใช่ Jam · ส่งให้ Jam ภายใน จ. 26 ต.ค.

**Done เมื่อ:** label ครบและส่งให้ Jam ก่อน ศ. 23 ต.ค. (Jam ต้องใช้รัน PoC) · คำถาม P3b ส่งภายใน จ. 26 ต.ค.

### S3 · 2–13 พ.ย.

- [ ] หน้าแชท P4-lite: อ่าน SSE ผ่าน `lib/sse.ts`, แสดงข้อความที่ไหลออกมา, render KaTeX, ส่งรูป
  - 20 ต.ค. stream จาก fake transport เสร็จ (PR #32 · `chat-streaming.md`) · เหลือ HTTP transport + upload รูปจริง เมื่อ `POST /sessions/{id}/messages` ของ Junior มา
- [x] Generate type จาก `/openapi.json` (`pnpm gen:api`)
  - 21 ต.ค. (PR #41) · generate จาก stub ห้องติว api.md v1.2 · รัน `pnpm gen:api` ใหม่เมื่อ Junior เพิ่ม endpoint หรือทำตาม v1.3
- [x] Use case UC สมัคร และ UC upload → scope (D7)
- [ ] เขียน report P4-lite ร่วมกับ Junior

**Done เมื่อ:** คุยกับ AI บน staging แล้วเห็นตัวอักษรไหลออกมาและสมการ render ถูก

### S4 · 16–27 พ.ย.

- [ ] P8-lite ร่วมกับทีม (review test)
- [x] Use case UC ติว และ UC ส่งคำตอบ ให้ครบ 4 UC (D7)
  - ทำก่อนกำหนด 21 ต.ค. (PR #36) · มีข้อเสนอแก้ AM-02, ai-orchestration และ api.md v1.3 รอ Junior + Jam review
- [ ] เตรียมลำดับหน้าจอสำหรับ demo รวม

### Buffer · 30 พ.ย.–4 ธ.ค.

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
- [ ] P3: ingest → A5 → A6 → A7 → `compute_importance` · เทียบกับ label · ลอง embedding 2–3 ตัวกับคำถาม 20 ข้อ
- [ ] Report P1 และ P3 ด้วย `/poc-report`
  - P1 เสร็จแล้ว (`specs/poc/reports/P1.md`) · เหลือ P3
- [ ] อัปเดต `config/learning.yaml` (`ocr.confirm_below_confidence`, `stars.*`) และ `config/ai.yaml` (model ที่เลือก) ผ่าน PR
  - ส่วน ocr เสร็จแล้ว (PR #45): `ocr.always_confirm: true` แทน threshold · AM-02 ยืนยันทุกครั้ง (ทีมตกลง) · เหลือ `stars.*` และ model ใน `ai.yaml` รอผล P3

**Done เมื่อ:** ตัดสินแล้วว่าใช้ provider ไหนอ่านลายมือ และใช้ embedding ตัวไหน

### S3 · 2–13 พ.ย.

- [ ] Label golden set คำตอบ 50 ข้อ (D8)
  - ทีมตกลง 21 ต.ค. (PR #51): คน label คือ May หรือ Junior ไม่ใช่ Jam เพราะ Jam ทำ P2 (`evals/README.md` "กฎ") · Jam เตรียมใบงาน `evals/answers/worksheet.md` แล้ว (รูป 30 ข้อ + ช่องคำตอบพิมพ์ 20 ข้อ) · เหลือ: เขียนคำตอบพิมพ์ 20 ข้อตามโควตาใน `evals/README.md` "ใบงาน" และ label ครบ 50 ข้อ
- [ ] P2: merge rules + LLM classifier (`prompts/check_answer/v1`) ใช้ SymPy service ของ Junior
- [x] Script `evals/run_eval.py` ออกคะแนน verdict, error type, บรรทัดผิด · เสร็จก่อนกำหนด (21 ต.ค. · PR #47) · ให้คะแนนจากไฟล์ prediction (`--predictions`) · นิยาม metric ใน `evals/README.md` "การให้คะแนน" · ต่อกับ checker จริงตอนทำ P2 · การรันใน CI เมื่อ prompt เปลี่ยน (§2.11) รอ Junior
- [ ] Report P2

**Done เมื่อ:** มีตัวเลข 3 ตัวของ P2 เทียบกับเป้า

### S4 · 16–27 พ.ย.

- [ ] P8-lite ร่วมกับทีม (เป็นเจ้าของ spec `compute_importance`)
- [ ] อัปเดต threshold ใน AI flow specs และ `learning-model.md` ตามผล P1 P2 P3 (D2)
- [ ] Test strategy 1 หน้าใน `specs/system/`

### Buffer · 30 พ.ย.–4 ธ.ค.

- [ ] ส่วน AI, การวัดผล และงานวิจัยรองรับในรายงาน
- [ ] สรุปตัวเลขของ P8-lite สำหรับ Self-Assessment

---

## ทั้งทีม

| Sprint | งานร่วม |
|---|---|
| S1 | review `requirements.md` แล้วอัปเดต SRS เป็น v1.1 (D1) · ตกลง Claude Code subscription · คุยเรื่องงานวิจัยรองรับ learning path |
| S2 | ตรวจ label ของกันและกัน (คน label ไม่ใช่คนทำ PoC) |
| S3 | ทดลองใช้หน้าแชทแล้วจด feedback |
| S4 | **P8-lite:** `/spec-to-tests` → review test ด้วยกัน → `/implement-feature` → เก็บ metrics |
| Buffer | รายงานเทอม 1 + ซ้อมนำเสนอ |
