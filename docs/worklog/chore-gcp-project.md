# สร้าง GCP project + เปิด API, Artifact Registry, Secret Manager

| | |
|---|---|
| Owner | Junior |
| Branch | `chore/gcp-project` |
| Checklist item | สร้าง GCP project, เปิด API, Artifact Registry, Secret Manager (`infra/README.md`) |
| Status | in progress · 2026-10-28 |

## Plan

แผนใหม่ 2026-10-28: demo ศ. 30 ต.ค. ต้องมี URL ของ `api-staging` ก่อน จึง deploy ด้วยสคริปต์ `gcloud run deploy` (ทางสำรองของ P6-lite) แล้วค่อยทำ Cloud Build trigger ถ้ามีเวลา · Junior รัน `gcloud` ใน PowerShell เองทีละคำสั่ง แล้วส่ง output ให้ Claude ดู

- [x] 1. 🙋 ติดตั้ง gcloud CLI แล้ว login (`juniormonsicha.kt@gmail.com`)
- [x] 2. 🙋 Jam สร้าง project `anyang-513006` (Free Trial) ผูก billing และตั้ง budget alert $50 · Junior เป็น Owner · `gcloud projects describe` ได้ `ACTIVE`
- [x] 3. 🙋 `gcloud config set project anyang-513006` + เปิด API 5 ตัว (`run`, `cloudbuild`, `artifactregistry`, `secretmanager`, `aiplatform`) + สร้าง Artifact Registry `anyang` (docker, `asia-southeast1`)
- [ ] 4. 🤖 เขียน `infra/deploy-staging.ps1` (build image ด้วย Cloud Build → `gcloud run deploy api-staging` ที่ `asia-southeast1`) + `.gcloudignore` · `--allow-unauthenticated` (browser เรียกตรง) · env: `APP_ENV=staging`, `AI_PROVIDER=fake`, `CORS_ALLOW_ORIGINS=https://anyang-amber.vercel.app,http://localhost:3000` + `CORS_ALLOW_ORIGIN_REGEX` ของ preview (`.env.example`) · ใช้ตัวคั่นแบบกำหนดเองของ gcloud (`^@^`) เพราะค่า origins มี `,`
- [ ] 5. 🙋 รันสคริปต์ → ได้ URL · 🤖 ตรวจ `/health`, `/docs` และ header CORS จาก origin ของ Vercel ด้วย `curl`
- [ ] 6. 🤖 อัปเดต docs: `infra/README.md` (Project ID, URL, วิธี deploy มือ, demo-day note), `docs/team/setup.md` (gcloud, `GOOGLE_CLOUD_PROJECT`), checklist · ร่างข้อความถึง Jam ให้ตั้ง `NEXT_PUBLIC_API_URL` (อ่านใน `apps/web/lib/httpTransport.ts` `apiUrl()`) ใน Vercel ทั้ง Production + Preview เป็น URL ของ Cloud Run แล้ว redeploy (ค่า `NEXT_PUBLIC_*` ฝังตอน build) · เขียนใน PR ว่าช่วง 3 ของ demo (`docs/design/demo-flow.md`) จะตอบจาก stub (`AI_PROVIDER=fake`) จนกว่า gateway ทาง Vertex จะเสร็จ
- [ ] 7. (ถ้ามีเวลา) 🙋 + 🤖 Cloud Build trigger: merge → deploy `api-staging` · แก้ `infra/cloudbuild.yaml` ให้ตรงกับสคริปต์ (env CORS, ไม่ใช้ `anthropic-api-key`)

## Definition of done

- มี GCP project ที่ผูก billing และมี budget alert (ทำแล้ว)
- API 5 ตัวเปิดแล้ว · Artifact Registry `anyang` อยู่ที่ `asia-southeast1`
- `api-staging` บน Cloud Run ตอบ `GET /health` = `{"status":"ok"}` และ preflight จาก `https://anyang-amber.vercel.app` ได้ `access-control-allow-origin`
- `infra/README.md` และ `setup.md` ตรงกับที่ตั้งจริง · ติ๊ก checklist ข้อ "สร้าง GCP project" + เขียน sub-bullet ใต้ข้อ Cloud Build trigger ว่ามีทางสำรองแล้ว

## Decisions

- 2026-10-28 · **Demo-day:** เย็นพฤหัส 29 ต.ค. ตั้ง `gcloud run services update api-staging --region=asia-southeast1 --min-instances=1` กัน cold start · หลัง demo ศ. 30 ต.ค. ตั้งกลับเป็น `--min-instances=0` ทันที (instance ที่เปิดค้างกิน trial credit)

- 2026-10-28 · ทีมเลือก Free Trial ของ GCP · Jam สร้าง project `anyang-513006` และถือ billing · Junior เป็น Owner · budget alert $50 (Jam ตั้ง · ไม่นับ promotional credits จึงเตือนเมื่อจ่ายเงินจริง)
- 2026-10-28 · **ห้ามกด Activate / Upgrade เป็น paid account เด็ดขาด** · Free Trial = $300 ภายใน 90 วัน หมดแล้ว resource หยุดเอง ไม่ตัดบัตร
- 2026-10-28 · Gemini ใช้ผ่าน **Vertex AI เท่านั้น** · credit ของ Free Trial ไม่ครอบคลุม API key ของ AI Studio · ⚠️ ตอนนี้ `GeminiProvider` (`app/ai/gateway.py` `build_default_gateway`) ใช้ `GEMINI_API_KEY` (AI Studio) ต้องเพิ่มทาง Vertex ก่อนเปิด `AI_PROVIDER=live` บน Cloud Run (งาน AI gateway ของ S3)
- 2026-10-28 · deploy ครั้งแรกใช้ `AI_PROVIDER=fake` และไม่ใช้ secret · endpoint ตอนนี้มีแค่ `/health` + stub ห้องติวที่คืน fixture (`X-Stub: true`) ยังไม่เรียก Supabase หรือ AI · จึงไม่สร้าง secret เปล่า (`supabase-service-role`, `anthropic-api-key`) ในรอบนี้
- 2026-10-28 · ไม่ต้องให้ role Vertex AI User กับ Jam เพราะ Jam สร้าง project จึงเป็น Owner อยู่แล้ว

- 2026-10-19 · สร้าง secret เปล่าก่อน ใส่ค่าทีหลัง · key ของ Supabase staging ยังไม่มี (project ยังไม่ได้สร้าง) และ Claude ห้ามแตะค่า secret
- 2026-10-19 · ยังไม่เริ่มขั้น 1 · Junior ไม่ต้องการผูกบัตรเครดิต (GCP บังคับผูก billing ก่อนเปิด Cloud Run/Cloud Build/Artifact Registry/Vertex แม้ใช้แค่โควตาฟรี) · พักงานไว้เพื่อปรึกษาทีม · ทางเลือก: (1) ขอ Google Cloud for Education credit จากอาจารย์ (ไม่ต้องใช้บัตร, ตรงกับ `architecture.md` ที่เขียนว่า "ใช้ GCP credit", แนะนำ) (2) free trial $300 ด้วยบัตรของใครสักคน (3) ย้าย backend ไปโฮสต์ฟรี เช่น Render / Hugging Face Spaces = เปลี่ยน architecture, เครื่องหลับทำให้วัด TTFT ไม่ได้, และไม่แก้ AI-07 ของ P1

## Done today

- 2026-10-28 · ขั้น 3: set project · เปิด API 5 ตัว (operation `acf.p2-659706857266-…` สำเร็จ) · สร้าง Artifact Registry `anyang` (docker, `asia-southeast1`) · project number `659706857266`
- 2026-10-28 · resume: Jam สร้าง project แล้ว · เขียนแผนใหม่ (deploy มือก่อน trigger)

- 2026-10-19 · เขียนแผน 6 ขั้น + เปิด draft PR #20 · เช็คว่าเครื่องยังไม่มี `gcloud`
- 2026-10-19 · คุยเรื่องค่าใช้จ่าย: งานนี้เอง (เปิด API, Artifact Registry, secret เปล่า) ไม่มีค่าใช้จ่าย · ที่มีค่าใช้จ่ายจริงคือ Gemini บน Vertex (คิดตาม token)

## Next step

ขั้น 4: เขียน `infra/deploy-staging.ps1` + `.gcloudignore` ตามแผน แล้วให้ Junior review ก่อนรัน

## Waiting on

- ไม่มี

## Notes for next time

- ถ้าไม่ได้ตั้ง `NEXT_PUBLIC_API_URL` ใน Vercel หน้าห้องติวจะไม่ได้เรียก localhost แต่ `apiUrl()` จะ throw `NEXT_PUBLIC_API_URL must be set` ตอนเปิดห้อง

- ถ้ารอ credit นานเกิน ~23 ต.ค. ให้คุยทางเลือกโฮสต์ฟรี เพื่อให้ demo S2 (30 ต.ค.) ทัน · ระหว่างรอทำ Supabase `anyang-staging` + CODEOWNERS ได้ (ไม่ต้องใช้เงิน)

- Vertex ใน project นี้แก้เรื่อง AI-07 ของ Jam ได้ (P1 ห้ามส่งรูปลายมือผ่าน free tier ของ AI Studio) เพราะเป็น billing account แบบจ่ายเงิน
