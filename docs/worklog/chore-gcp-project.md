# สร้าง GCP project + เปิด API, Artifact Registry, Secret Manager

| | |
|---|---|
| Owner | Junior |
| Branch | `chore/gcp-project` |
| Checklist item | สร้าง GCP project, เปิด API, Artifact Registry, Secret Manager (`infra/README.md`) |
| Status | in progress · 2026-10-19 |

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

## Next step

🙋 Junior: ติดตั้ง gcloud CLI แล้ว login ตามขั้น 1

## Waiting on

ไม่มี

## Notes for next time

- Vertex ใน project นี้แก้เรื่อง AI-07 ของ Jam ได้ (P1 ห้ามส่งรูปลายมือผ่าน free tier ของ AI Studio) เพราะเป็น billing account แบบจ่ายเงิน
