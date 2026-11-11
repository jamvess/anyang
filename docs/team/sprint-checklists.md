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
  - 31 ต.ค. ทีมตกลงเลิกบังคับ approve (อยู่คนละ time zone · การรอ review ทำให้งานติด) · ruleset เปลี่ยนเป็น approve 0 คน ยังต้องเปิด PR + CI 3 ตัวผ่าน · แทนด้วย self-review `/code-review` ใน `/work-done` + บอกกลุ่มก่อน merge งานเสี่ยง (`CLAUDE.md` "How we work" 5)
- [x] ⭐ ให้ Claude Code scaffold `apps/api` และตรวจผล
- [x] ⭐ `npx supabase init` + `db push` `0001_init.sql` ขึ้น Supabase cloud `anyang-dev` + เปิด custom access token hook
- [x] GitHub Actions รันครบ 3 job และเขียวบน `main`
- [x] สร้าง GCP project, เปิด API, Artifact Registry, Secret Manager (`infra/README.md`)
  - 28 ต.ค. (PR #20): Jam สร้าง Free Trial `anyang-513006` (ถือ billing, budget alert $50) · Junior เป็น Owner · เปิด API 5 ตัว + Artifact Registry `anyang` · Secret Manager เปิดแล้วแต่ยังไม่สร้าง secret เพราะ `api-staging` ยังไม่ใช้ · ⚠️ ห้ามกด Activate/Upgrade · Gemini ใช้ผ่าน Vertex เท่านั้น
- [x] สร้าง Supabase project `anyang-staging` · ref `sfapuygntxuelsxsgkay` Singapore (21 ต.ค., PR #28)
  - 21 ต.ค. Jam ตั้ง Vercel env ทั้ง **Production** และ **Preview** (`NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`) ให้ชี้ `anyang-staging` (`sfapuygntxuelsxsgkay`) แบบ Config แล้ว redeploy production · มีผลเมื่อมีหน้าที่ import `lib/supabase.ts` (ตอนนี้ยังไม่มี production จึงไม่เคยพังจริง)
- [ ] ให้สิทธิ์ทีม: GitHub collaborator + Supabase org (เจ้าของ repo ทำ, `setup.md` A0), GCP (Jam: Vertex AI User)
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
  - ทำโดย Jam (1 พ.ย.) ช่วง solo · ทำได้บางส่วน
  - 1 พ.ย. (PR #99 · `specs/poc/reports/P4-lite.md`): วัดกับ Gemini จริงบน Vertex จากเครื่อง Jam (staging ยังเปิด live ไม่ได้) · `thinking: low` p95 3.87 s → `minimal` p95 1.20 s · 0.039 บาท/ข้อความ (`poc/P4-lite/cost.py` จาก log `ai_calls`) · `ai.yaml` 1.8 · เหลือ: วัดซ้ำบน staging `ttft.py --label staging-gemini` เมื่อหน้าเว็บส่ง token + `AUTH_REQUIRED=true` + env Supabase ของ api-staging
  - 1 พ.ย. (PR #103 · Jam ช่วง solo): rate limit ข้อความในห้องติว (`guards.rate_limit_messages_per_minute` · 429 `rate_limited`) + circuit breaker ต่อ provider ใน gateway (`gateway.circuit_breaker`) · `specs/features/ai/gateway-guards.md` · ก่อนเปิด live บน staging ยังเหลือ: `api-staging` ตรวจ token (`SUPABASE_URL`, `SUPABASE_ANON_KEY`, `AUTH_REQUIRED: "true"` · Junior), runtime SA (Junior), หน้า login (May)

**Done เมื่อ:** หน้า `/docs` แสดงครบทุก API และหน้าแชทของ May คุยกับ Gemini ผ่าน staging ได้

### S4 · 16–27 พ.ย.

- [ ] P8-lite ร่วมกับทีม (review test ของ `compute_importance`)
  - 8 พ.ย. test พร้อมให้ review ย้อนหลัง (PR #113 · `apps/api/tests/unit/test_stars.py`) · จดเวลาที่ใช้ใน `poc/P8-lite/metrics.md` §4 · test ที่ผิดจดใน §3
- [ ] อัปเดต architecture และ data model ตามผล PoC (D2, D3)
  - 1 พ.ย. (PR #101 · Jam ช่วง solo): `architecture.md` v1.2 ใส่ผล P1, P2, P3b, P4-lite แล้ว (model ของแต่ละ tier, embedding 768 มิติ, SymPy worker pool) · data model ได้ `0003` จาก P3 (PR #67) · เหลือ: อัปเดตอีกรอบหลัง P8-lite และ P2 ต่อเข้าห้องแชท
- [ ] (ถ้ามีเวลา) ต่อ P1 + P2 เข้าหน้าแชท: ส่งรูปแล้วได้ verdict
  - ทำโดย Jam (8 พ.ย.) ช่วง solo · ทำได้บางส่วน
  - 8 พ.ย. (PR #114 · `specs/features/check/photo-check-in-room.md`): ส่งรูป → `extract_answer` → `ocr_preview` · ยืนยัน → checker ของ P2 → `verdict` → purpose ใหม่ `explain_check` อธิบายทันที (AM-07) · smoke บน Vertex ในเครื่อง 3 รูปจาก `evals/` verdict ตรง label 3/3 · ผ่าน interface `ImageStore` + `RoomState` (เก็บใน memory) · **บน staging ยังเป็น stub** จนกว่าจะมี Storage · เหลือ (Junior): `/uploads` จริง + bucket/policy + `ImageStore` ที่อ่าน Supabase Storage, บันทึก `messages` / `problems` / `attempts`, ตัดสินข้อเสนอใน spec §10 ข้อ 3–8 · api.md: 404/422 ของ `image_path` (spec §11)
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
- [x] เขียนคำถาม 20 ข้อ + หน้าที่มีคำตอบ สำหรับวัด embedding (P3b) ลง `evals/topics/mth10101/retrieval_questions.md` (เทมเพลตและกติกาอยู่ใน branch `poc/P3b-embedding`) · คนเขียนต้องไม่ใช่ Jam · ส่งให้ Jam ภายใน จ. 26 ต.ค. · เสร็จ 21 ต.ค. (PR #46 เข้า #39): 20 ข้อ 19 หัวข้อ

**Done เมื่อ:** label ครบและส่งให้ Jam ก่อน ศ. 23 ต.ค. (Jam ต้องใช้รัน PoC) · คำถาม P3b ส่งภายใน จ. 26 ต.ค.

### S3 · 2–13 พ.ย.

- [ ] หน้าแชท P4-lite: อ่าน SSE ผ่าน `lib/sse.ts`, แสดงข้อความที่ไหลออกมา, render KaTeX, ส่งรูป
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
- [ ] เตรียมลำดับหน้าจอสำหรับ demo รวม
  - 21 ต.ค. ร่างแล้ว `docs/design/demo-flow.md` (PR #61): 15 นาที 7 ช่วง · ห้องติว live + wireframe คู่ผล PoC · คนพูดแบ่งตามงาน · ทางสำรอง + checklist ก่อน demo · เหลือเติมตัวเลข P2, P4-lite, P8-lite หลัง S3–S4 และให้ทีมตกลงลำดับ
  - 11 พ.ย. (PR #119) ร่างรอบ 2: live ย้ายมาห้องเดโม่ในเครื่อง May (staging เป็นโบนัส) · รวมช่วง 3+4 เป็น live 5:30 · ตัวเลข P1–P4-lite, P6-lite, P8-lite เติมแล้ว (P8-lite ยังไม่มี report · TTFT staging ยังไม่วัด) · **เหลือ: ทีมตกลงลำดับ** (ถามในกลุ่มแล้ว) · Jam ให้ role Vertex AI User แก่ May ก่อนซ้อม · May เตรียมรูปลายมือข้อ 2 ที่เขียนเอง

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

- [ ] เดโม่ห้องติวที่ใช้ได้จริงในเครื่อง ให้อาจารย์ดูก่อนทำต่อ (อาจารย์ขอ 9 พ.ย. · เพิ่มเอง)
  - 9 พ.ย. (PR #115 · `specs/features/tutor/demo-room.md` + `specs/features/planner/bkt-mastery.md`): `APP_ENV=local` วนได้จริงกับ Vertex · อัปโหลดรูปในเครื่อง · โจทย์ 5 ข้อ · BKT จริง (`app/domain/bkt.py`) ในการ์ดตอนเข้าห้อง · tutor ทักก่อน (`open_session`) · รู้โจทย์และจำบทสนทนา (`tutor_reply/v2`) · พิมพ์คำตอบแล้วตรวจ (`typed_answer`) · แสดงวิธีทำทีละขั้นทุกครั้ง (`explain_check/v2`) · ส่งแค่คำตอบยังไม่ผ่าน (`checker.min_working_lines`) · วิธีเปิดอยู่ใน spec §12 · staging ยังเป็น stub
  - 9 พ.ย. (PR #117 · `specs/features/tutor/answer-canvas.md`): canvas เขียนคำตอบอยู่ท้ายแชทเมื่อมีโจทย์ค้าง (เมาส์ / Apple Pencil / นิ้ว · ใส่รูป · ส่งเป็น PNG ทางเดิมของรูป) · ลองบนคอมแล้ว · iPad ยังไม่ได้ลอง · นับวิธีทำเป็นขั้น และให้โจทย์เดิมซ้ำเมื่อขาดวิธีทำ · ตัด `**` ในแชท · ดีไซน์ชั่วคราวรอ May (spec §10)
  - เหลือ: hint ladder ทำทีละขั้นก่อนเฉลย (`feat/hint-ladder` · ขัด AM-07 ต้องเสนอทีม) · อัดวิดีโอสำรองหลังงานนั้น · ลองบน iPad
- [ ] P8-lite ร่วมกับทีม (เป็นเจ้าของ spec `compute_importance`)
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

### Buffer · 30 พ.ย.–4 ธ.ค.

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
| Buffer | รายงานเทอม 1 + ซ้อมนำเสนอ |
