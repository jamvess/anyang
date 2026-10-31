# PoC specs · เทอม 1 (ฉบับลด scope)

PoC คือการลองทำส่วนที่ยากที่สุดแบบเล็กที่สุด เพื่อพิสูจน์ว่าทำได้ก่อนสร้างทั้งระบบ ทุกตัวจบด้วย report 1 หน้าที่ `specs/poc/reports/<ID>.md` (template: `_REPORT_TEMPLATE.md`, เขียนด้วย `/poc-report <ID>`)

โค้ดของ PoC อยู่ในโฟลเดอร์ `poc/<ID>/` ของ repo ใช้ได้ทั้ง notebook และ script แต่ต้องรันซ้ำได้ด้วยคำสั่งเดียวที่เขียนไว้ใน README ของ PoC นั้น ส่วนโค้ดที่จะใช้ต่อจริง (เช่น SymPy service, gateway) ให้เขียนใน `apps/api` ตั้งแต่แรก

ลำดับ: P6-lite → P1, P3 → P2, P4-lite → P8-lite

---

## P6-lite · SaaS + CI/CD · Junior · S1–S2

- **คำถาม:** deploy อัตโนมัติและแยกข้อมูลตาม tenant ได้จริงไหม
- **ทำ:**
  1. GitHub Actions: lint + test ของ web และ api ทุก PR (`.github/workflows/ci.yml`)
  2. Cloud Build: merge เข้า `main` → build image → push Artifact Registry → deploy Cloud Run `api-staging`
  3. Secret ทั้งหมดอยู่ใน Secret Manager ไม่มีใน repo
  4. Integration test `test_SA06_tenant_isolation`: สร้าง 2 user ผ่าน Supabase Auth แล้วยืนยันว่า user A อ่าน/เขียน `exam_preps`, `attempts`, `messages` ของ B ไม่ได้
- **ผ่านเมื่อ:** merge แล้ว staging อัปเดตเองภายใน 10 นาที, isolation test ผ่านใน CI, ไม่มี secret ใน git history
- **ถ้าไม่ผ่าน:** deploy ด้วย `gcloud run deploy` script แทน Cloud Build
- **ย้ายไปเทอม 2:** Terraform, load test 50 SSE streams, API สร้าง organization tenant

## P1 · อ่านลายมือคณิต · Jam · S2

- **คำถาม:** Vision LLM อ่านลายมือเป็น LaTeX รายบรรทัดได้แม่นพอไหม และ confidence ใช้แยกบรรทัดที่อ่านผิดได้ไหม
- **Data:** `evals/handwriting/` 30–50 รูป แต่ละรูปมีไฟล์เฉลย (LaTeX รายบรรทัด) ที่ May พิมพ์ (คนพิมพ์เฉลยไม่ใช่คนทำ PoC)
- **ทำ:** รันทุกรูปกับ 3 ตัวเลือก (Gemini vision, Claude vision, Mathpix) ใช้ prompt `prompts/extract_answer/v1.md` ให้คะแนนรายบรรทัดด้วย SymPy (บรรทัดถูก = เท่ากันทางคณิตศาสตร์กับเฉลย) แล้ววาด precision–recall ของ confidence
- **Metrics:** line accuracy ต่อ provider, ต้นทุนต่อรูป, latency, recall ของการจับบรรทัดที่อ่านผิดที่ threshold ต่างๆ
- **ผ่านเมื่อ:** มี provider ที่ line accuracy ≥ 80% และมี threshold ที่จับบรรทัดอ่านผิดได้ ≥ 95%
- **ผลที่ต้องได้:** เลือก provider + ค่า `ocr.confirm_below_confidence` ใน `config/learning.yaml`
- **ถ้าไม่ผ่าน:** ใช้ Mathpix เป็นหลัก (ขอ budget ก่อน S3)
- **ผล (20 ต.ค. · `specs/poc/reports/P1.md`):** ทดสอบแค่ Gemini free tier (Claude/Mathpix ต้องเสียเงิน) · line accuracy 95.2% ผ่าน · threshold ไม่ผ่าน · ไม่ใช้ fallback Mathpix เพราะสิ่งที่ไม่ผ่านคือ confidence ไม่ใช่ความแม่น · ทีมตกลงให้ยืนยันทุกครั้ง (`ocr.always_confirm` · PR #45)

## P3 · เอกสาร → หัวข้อ + ดาว · Jam (+ Junior ช่วย ingest) · S2

- **คำถาม:** สกัดหัวข้อจาก PDF ภาษาไทยได้ตรงกับที่คนทำไหม
- **Data:** วิชาคณิต 1 วิชา: ชีท + ข้อสอบเก่า 2 ชุด · label หัวข้อ, ดาว และ map ข้อสอบรายข้อโดย May + Jam ก่อนรัน
- **ทำ:** pipeline ตาม ai-orchestration §2.3 ขั้น 4–5 (extract → chunk → embed → A5 map → A6 merge → A7 map questions → `compute_importance`) และลอง embedding 2–3 ตัวกับคำถามภาษาไทย 20 ข้อ
- **Metrics:** % หัวข้อที่ตรงกับ label, % ดาว ★★★ ที่ตรง, recall@4 ของ retrieval, เวลาต่อไฟล์, ต้นทุนต่อไฟล์, overlap ของหัวข้อระหว่างอาจารย์ (ถ้ามีข้อสอบคนละอาจารย์)
- **ผ่านเมื่อ:** หัวข้อตรง ≥ 80%, ★★★ ตรง ≥ 80%, ≤ 3 นาที/ไฟล์
- **ผลที่ต้องได้:** embedding model + มิติ vector, ขนาด chunk, ค่า `stars.*` ที่ยืนยันแล้ว
- **ถ้าไม่ผ่าน:** ใช้ Google Document AI กับไฟล์สแกน และปรับ prompt A5/A6

## P2 · ตรวจคำตอบ · Jam (รวม SymPy service · ย้ายจาก Junior 21 ต.ค.) · S3

- **คำถาม:** SymPy + LLM ตัดสินถูกผิดและจำแนก error ได้ตามเป้าไหม
- **Data:** `evals/answers/` 50 คำตอบ (expression, factored, equation) label: verdict, error_type, first_wrong_line
- **ทำ:** SymPy service (`apps/api/app/math/`) + merge rules + LLM classifier (`prompts/check_answer/v1.md`) ตาม ai-orchestration §2.4
- **ผ่านเมื่อ:** verdict ≥ 95% (47/50), error_type ≥ 80%, first_wrong_line ≥ 85%
- **ถ้าไม่ผ่าน:** ลด error types เหลือ 4 (รวม calculation+sign, รวม concept+prerequisite)
- **ผล (31 ต.ค. · `specs/poc/reports/P2.md`):** ผ่านทั้ง 3 เป้าบน Vertex (`gemini-3.5-flash`, prompt v1): verdict 50/50 = 100%, error_type 27/28 = 96.4%, first_wrong_line 24/24 = 100% · SymPy ตัดสิน verdict 45 ข้อ LLM 5 · ใช้ 6 error types ตามเดิม ไม่ต้องทำ prompt v2 · ข้อควรระวัง: label ร่างโดย AI (May ยืนยัน), ตัวอย่าง 50 ข้อจากวิชาเดียว

## P4-lite · Chat AI ที่ stream ได้ · May (web) + Junior (api) · S3

- **คำถาม:** stream คำตอบผ่าน SSE บน Cloud Run เร็วพอไหม และสลับผู้ให้บริการ AI ได้ไหม
- **ทำ:** หน้าแชท Next.js ↔ `POST /sessions/{id}/messages` (SSE) ↔ `ai.call("tutor_reply")` → Gemini · provider interface มี fake provider · render KaTeX · log `ai_calls`
- **Metrics:** TTFT p50/p95 จาก 50 ข้อความบน staging, ต้นทุนต่อข้อความ, เปลี่ยน `AI_PROVIDER=fake` แล้ว test ผ่านโดยไม่แก้โค้ด
- **ผ่านเมื่อ:** TTFT p95 < 2 วินาที, สลับ provider ได้ด้วย config, มีตัวเลขต้นทุน
- **ย้ายไปเทอม 2:** stage machine, planner, buddy scene, fallback ไป Claude, circuit breaker

## P8-lite · SDD/TDD ด้วย Claude Code · ทั้งทีม · S4

- **คำถาม:** pipeline spec → test → code ใช้ได้จริงไหม
- **ทำ:** ใช้ `specs/features/scope/compute-importance.md` ผ่านครบ: `/spec-feature` (มีร่างให้แล้ว แค่ review) → `/spec-to-tests` → ทีม review test → `/implement-feature` → CI → PR review
- **Metrics:** % โค้ดที่ agent เขียน (นับบรรทัดใน PR), จำนวนรอบ red → green, บั๊กที่ test จับได้ก่อน merge, เวลาที่คนใช้ review · กรอกใน `poc/P8-lite/metrics.md` ระหว่างทำ (นับบรรทัดด้วย `poc/P8-lite/agent_lines.sh`)
- **เตรียมแล้ว (31 ต.ค. · PR #89):** spec approved · 27 AC · test plan 19 ชื่อ
- **ผ่านเมื่อ:** merge ได้โดย CI เขียว และเก็บ metrics ครบ (ใช้ใน Self-Assessment)
