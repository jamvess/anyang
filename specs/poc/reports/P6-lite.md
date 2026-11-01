# PoC P6-lite · SaaS + CI/CD · report

| | |
|---|---|
| Owner | Junior (Jam วัดผลและเขียน report ช่วง solo 1 พ.ย.) |
| Sprint | S1–S2 (วัดผล 1 พ.ย.) |
| Date | 1 พ.ย. 2569 |
| Code | CI: `.github/workflows/ci.yml` · deploy: `infra/trigger-api-staging.yaml` + `infra/cloudbuild.yaml` (#83) · isolation: `apps/api/tests/integration/test_rls_isolation.py` · วัดผล: `poc/P6-lite/` · คำสั่งรันซ้ำ (ต้องมี `gh` และ `gcloud` ที่ login แล้ว · อ่านอย่างเดียว): `cd apps/api && uv run python ../../poc/P6-lite/deploy_latency.py` แล้ว `cd ../.. && bash poc/P6-lite/evidence.sh > poc/P6-lite/results/evidence.txt` · ผลของ report นี้: `poc/P6-lite/results/deploy-latency.json`, `poc/P6-lite/results/evidence.txt` |

## 1. คำถาม

deploy อัตโนมัติและแยกข้อมูลตาม tenant ได้จริงไหม

## 2. วิธีทดสอบ

- **Data:** ใช้ประวัติจริงของ repo · deploy: ทุก PR ที่ merge เข้า `main` หลังสร้าง trigger `api-staging-deploy` (28 ต.ค. 09:14 UTC) ถึง 1 พ.ย. = 14 PR · CI: ทุก run ของ `ci.yml` ที่ push เข้า `main` ตั้งแต่ commit แรก (12 ต.ค.) = 89 run · secret: ทุก commit ของทุก ref = 705 commit
- **Deploy:** PR ที่ "ควร deploy" คือ PR ที่มีไฟล์ตรงกับ `includedFiles` ของ trigger (`apps/api/**`, `config/**`, `prompts/**`, `infra/**`) · จับคู่กับ build ของ merge commit · เวลา = `mergedAt` ของ PR ถึง `finishTime` ของ build (ขั้นสุดท้ายคือ `gcloud run deploy` ซึ่งจบเมื่อ revision ใหม่รับ traffic) · ยืนยันด้วย image digest ว่า revision ของ `api-staging` รัน image ของ build นั้นจริง
- **Isolation:** ผลของ job `api-integration` (Supabase ในเครื่องของ CI ด้วย `supabase start` → `pytest tests/integration` ซึ่งมี `test_SA06_tenant_isolation` 3 ตาราง และ `test_SA06_ai_calls_isolated_and_not_insertable_by_users` ตั้งแต่ #95) · test ใน CI ข้ามเองไม่ได้: ถ้าไม่มี key จะ `raise` แทน `skip` · run ที่ไม่ผ่านเปิด log ดูทีละตัว
- **Secret:** GitHub secret scanning + push protection · grep pattern ของ key 10 แบบใน `git log -p --all` (Google, Anthropic, OpenAI, PEM, service account JSON, Supabase `sb_secret_`/`sb_publishable_`, JWT, GitHub token, Mathpix) · ไฟล์ `.env*` / key file ที่เคยถูก add · จำนวน secret ใน Secret Manager
- **สิ่งที่ไม่ได้ทดสอบ:** staging ทำงานถูกหลัง deploy (วัดแค่ว่า revision ใหม่รับ traffic · ไม่ได้ยิง `/health` หลังทุก deploy) · deploy ตอนมี secret (staging ยังเป็น `AI_PROVIDER=fake` ไม่มี secret ให้ใช้) · isolation ของตารางอื่นนอกจาก `exam_preps`, `attempts`, `messages`, `ai_calls` (4/27) · ย้ายไปเทอม 2 ตาม spec: Terraform, load test 50 SSE streams, organization tenant

## 3. ผล

| Metric | เกณฑ์ผ่าน | ผล | PASS / FAIL |
|---|---|---|---|
| merge แล้ว staging อัปเดตเอง | ภายใน 10 นาที | **8/8** PR ที่ควร deploy · 3.40–4.58 นาที (median 4.02) · ตอนวัด `api-staging` รัน image ของ #95 (ล่าสุด) · PR ที่ไม่ควร deploy 6 ตัวไม่มี build | **PASS** |
| isolation test ผ่านใน CI | ผ่าน | `api-integration` รันทุก push เข้า `main` · 84/89 success · 5 failure ล้มก่อนถึง test ทั้งหมด (ด้านล่าง) · ไม่มี run ที่ test isolation ล้ม | **PASS** |
| ไม่มี secret ใน git history | 0 | secret scanning + push protection เปิด · alert 0 · pattern 10 แบบ 0/705 commit · ไฟล์ `.env`/key ที่เคย add 0 | **PASS** |
| secret อยู่ใน Secret Manager (ข้อ "ทำ" 3) | ไม่มีใน repo | Secret Manager 0 secret · staging ยังไม่ใช้ secret (`cloudbuild.yaml` ไม่มี `--set-secrets`) · ไม่มี secret ใน repo | ผ่านโดยปริยาย · วัดใหม่ตอนเปิด live |

**5 run ที่ `api-integration` ล้ม** (ทุกตัวผ่านใน run ถัดไปโดยไม่แก้โค้ด)

| commit | วันที่ | สาเหตุ (จาก log) |
|---|---|---|
| 1346e9b | 12 ต.ค. | Docker Hub `toomanyrequests: Rate exceeded` ตอนดึง image ของ Supabase |
| 543e2f5, ce93a93 | 21 ต.ค. | registry `Data limit exceeded` ตอนดึง image |
| f195d25 | 21 ต.ค. | `Failed to resolve latest Supabase CLI release: rate limit exceeded` (`setup-cli` ใช้ `version: latest`) |
| 861bfca | 28 ต.ค. | port `54322` ถูกใช้อยู่ ตอน `supabase start` |

**เวลาแต่ละ deploy** (นาที): #83 4.58 · #87 3.79 · #80 4.02 · #89 3.40 · #91 4.03 · #93 4.14 · #94 3.87 · #95 3.87

## 4. การตัดสินใจ

**ผ่านครบทุกเกณฑ์** · เสนอใช้ Cloud Build trigger เป็นทางหลักต่อ และเก็บ `infra/deploy-staging.ps1` ไว้เป็นทางสำรองเหมือนเดิม (fallback ของ spec ไม่ต้องใช้) · เรื่อง deploy เป็นการตัดสินใจของ Junior (`roles.md`) **รอ Junior ยืนยัน**

- เวลาที่ใช้ทั้งหมดคือเวลา build + deploy (~4 นาที) เหลือเวลาจากเป้า 10 นาทีอีกเกินครึ่ง
- ความเสี่ยงของ CI อยู่ที่การดึง image และ CLI จากภายนอก ไม่ใช่ที่ test (§6)

## 5. สิ่งที่ต้องแก้ใน spec / config

- [x] `specs/poc/README.md` §P6-lite: เพิ่มบรรทัด "ผล" (PR นี้)
- [ ] (เสนอ · Junior ตัดสิน · `.github/` เป็นไฟล์เสี่ยง) `.github/workflows/ci.yml`: ตั้ง `supabase/setup-cli` เป็น version ที่ระบุแทน `latest` เพื่อไม่ต้องถาม GitHub API หา release ล่าสุดทุก run (สาเหตุของ f195d25)
- ไม่มีค่าใน `config/learning.yaml` หรือ `config/ai.yaml` ที่ต้องเปลี่ยน

## 6. ความเสี่ยงที่เหลือ

- **ก่อนเปิด live AI บน staging** (ข้อ ⚠️ ใน `infra/README.md`): ตรวจ Supabase JWT ทุก endpoint (URL เป็น public) · เปลี่ยน runtime SA ของ `api-staging` จาก default compute SA (role Editor ทั้ง project) เป็น SA ที่มีแค่ Vertex AI User + Secret Accessor · พอเริ่มใช้ secret ต้องวัดข้อ "secret อยู่ใน Secret Manager" ใหม่
- **CI ล้มเพราะของภายนอก** 5/89 run (5.6%) · ทุกครั้งผ่านใน run ถัดไป แต่ถ้าเกิดตอน merge ใกล้ demo จะเสียเวลา rerun · ลดได้ด้วยการ pin version ของ CLI (§5)
- **Isolation ครอบคลุม 4/27 ตาราง** · แผนให้ครบทุกตารางอยู่ใน S4 (`test-strategy.md` §5)
- **ตัวอย่างน้อย:** deploy 8 ครั้งใน 4 วัน · build ไม่เคยล้มเลยในช่วงนี้ จึงยังไม่เห็นว่าเวลาที่ build ล้มแล้วต้องแก้และ merge ใหม่จะนานแค่ไหน
- **grep หาได้เฉพาะ pattern ที่รู้จัก** · key รูปแบบอื่นอาศัย GitHub secret scanning (pattern ของ provider หลายร้อยแบบ + push protection กันตั้งแต่ตอน push)
