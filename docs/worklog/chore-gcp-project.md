# สร้าง GCP project + เปิด API, Artifact Registry, Secret Manager

| | |
|---|---|
| Owner | Junior |
| Branch | `chore/gcp-project` |
| Checklist item | สร้าง GCP project, เปิด API, Artifact Registry, Secret Manager (`infra/README.md`) |
| Status | paused · 2026-10-19 · รอทีมตัดสินใจเรื่อง billing |

## Plan

- [ ] 1. 🙋 ติดตั้ง gcloud CLI แล้ว login (เครื่องยังไม่มี `gcloud`)
- [ ] 2. 🙋 สร้าง project ใน GCP Console + ผูก billing + ตั้ง budget alert · บอก Project ID ให้ Claude
- [ ] 3. 🤖 `gcloud config set project` + เปิด API 5 ตัว (`run`, `cloudbuild`, `artifactregistry`, `secretmanager`, `aiplatform`) + สร้าง Artifact Registry `anyang` (docker, `asia-southeast1`) · ตรวจด้วย `gcloud services list --enabled` และ `gcloud artifacts repositories list`
- [ ] 4. 🤖 สร้าง secret เปล่า `supabase-service-role` และ `anthropic-api-key` ตามชื่อใน `infra/cloudbuild.yaml` (ยังไม่ใส่ค่า · ค่าจริงใส่ตอนทำ Supabase staging และ Cloud Build trigger)
- [ ] 5. 🙋 + 🤖 ให้สิทธิ์ Jam เป็น Vertex AI User: Junior บอกอีเมล Google ของ Jam → Claude รัน `gcloud projects add-iam-policy-binding`
- [ ] 6. 🤖 อัปเดต docs: `infra/README.md` (Project ID, ทำแล้ววันไหน), `docs/team/setup.md` A2 (gcloud CLI) และ A5 (ค่า `GOOGLE_CLOUD_PROJECT`)

## Definition of done

- มี GCP project ที่ผูก billing และมี budget alert
- API 5 ตัวเปิดแล้ว · Artifact Registry `anyang` อยู่ที่ `asia-southeast1` · Secret Manager มี secret ตามชื่อใน `cloudbuild.yaml`
- Jam มี role Vertex AI User
- `infra/README.md` และ `setup.md` ตรงกับที่ตั้งจริง · ติ๊ก checklist ข้อนี้ + เขียน sub-bullet ว่าข้อ "ให้สิทธิ์ทีม" ส่วน GCP เสร็จแล้ว

## Decisions

- 2026-10-19 · สร้าง secret เปล่าก่อน ใส่ค่าทีหลัง · key ของ Supabase staging ยังไม่มี (project ยังไม่ได้สร้าง) และ Claude ห้ามแตะค่า secret
- 2026-10-19 · ยังไม่เริ่มขั้น 1 · Junior ไม่ต้องการผูกบัตรเครดิต (GCP บังคับผูก billing ก่อนเปิด Cloud Run/Cloud Build/Artifact Registry/Vertex แม้ใช้แค่โควตาฟรี) · พักงานไว้เพื่อปรึกษาทีม · ทางเลือก: (1) ขอ Google Cloud for Education credit จากอาจารย์ (ไม่ต้องใช้บัตร, ตรงกับ `architecture.md` ที่เขียนว่า "ใช้ GCP credit", แนะนำ) (2) free trial $300 ด้วยบัตรของใครสักคน (3) ย้าย backend ไปโฮสต์ฟรี เช่น Render / Hugging Face Spaces = เปลี่ยน architecture, เครื่องหลับทำให้วัด TTFT ไม่ได้, และไม่แก้ AI-07 ของ P1

## Done today

- 2026-10-19 · เขียนแผน 6 ขั้น + เปิด draft PR #20 · เช็คว่าเครื่องยังไม่มี `gcloud`
- 2026-10-19 · คุยเรื่องค่าใช้จ่าย: งานนี้เอง (เปิด API, Artifact Registry, secret เปล่า) ไม่มีค่าใช้จ่าย · ที่มีค่าใช้จ่ายจริงคือ Gemini บน Vertex (คิดตาม token)

## Next step

ถ้าทีมเลือก credit จากอาจารย์หรือบัตร: เริ่มขั้น 1 (ติดตั้ง gcloud ด้วย `winget install --id Google.CloudSDK -e` แล้ว `! gcloud auth login`) และขั้น 2 ใช้ billing account จาก coupon/trial · ถ้าทีมเลือกโฮสต์ฟรี: ปิด PR นี้ แล้วเริ่ม branch ใหม่ที่แก้ `specs/system/architecture.md` (D2) ก่อน

## Waiting on

- 🙋 ทีม: ตัดสินใจเรื่อง billing ของ GCP (credit อาจารย์ / บัตร / โฮสต์ฟรี) · ร่างข้อความขอ credit จากอาจารย์อยู่ในแชทของ session 19 ต.ค.: ใช้ Cloud Run + Vertex สำหรับ PoC ประมาณการไม่เกิน $50 (ตัวเลขเดาคร่าวๆ)

## Notes for next time

- ถ้ารอ credit นานเกิน ~23 ต.ค. ให้คุยทางเลือกโฮสต์ฟรี เพื่อให้ demo S2 (30 ต.ค.) ทัน · ระหว่างรอทำ Supabase `anyang-staging` + CODEOWNERS ได้ (ไม่ต้องใช้เงิน)

- Vertex ใน project นี้แก้เรื่อง AI-07 ของ Jam ได้ (P1 ห้ามส่งรูปลายมือผ่าน free tier ของ AI Studio) เพราะเป็น billing account แบบจ่ายเงิน
