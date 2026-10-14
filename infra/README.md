# infra/

- `cloudbuild.yaml` · build + deploy backend ไป Cloud Run staging เมื่อ push เข้า `main`
- frontend deploy ผ่าน Vercel (เชื่อม GitHub repo, root directory = `apps/web`)
- Terraform ย้ายไปเทอม 2 (S6) ตอนนี้สร้าง resource ด้วยคำสั่งในหัวข้อ "สร้าง cloud resource" ด้านล่าง

ค่า `--concurrency` และ `--timeout` เป็นค่าเริ่มต้น ปรับตามผลวัดใน PoC P6-lite

## สร้าง cloud resource (Junior ทำครั้งเดียว)

ทำใน S1–S2 เป็นส่วนหนึ่งของ PoC P6-lite (ย้ายมาจาก `docs/team/setup.md` §5 ฉบับ 12 ต.ค.)

```bash
gcloud auth login
gcloud config set project <PROJECT_ID>
gcloud services enable run.googleapis.com cloudbuild.googleapis.com   artifactregistry.googleapis.com secretmanager.googleapis.com aiplatform.googleapis.com
gcloud artifacts repositories create anyang --repository-format=docker --location=asia-southeast1

# secrets (ค่าจริงใส่ผ่าน stdin ไม่พิมพ์ลง history)
printf '%s' "<service-role-key>" | gcloud secrets create supabase-service-role --data-file=-
printf '%s' "<anthropic-key>"    | gcloud secrets create anthropic-api-key --data-file=-
```

- สร้าง Cloud Build trigger: push เข้า `main` → ใช้ `infra/cloudbuild.yaml`
- ให้ service account ของ Cloud Build มีสิทธิ์ deploy Cloud Run และอ่าน secrets
- Supabase project ใหม่ (เช่น `anyang-staging`): `npx supabase login` → `npx supabase link --project-ref <ref>` → `npx supabase db push` แล้วเปิด Custom Access Token hook ใน Dashboard (Authentication → Hooks) · `anyang-dev` ทำแล้ว
- ให้สิทธิ์ Jam เป็น Vertex AI User เพื่อใช้ Gemini บนเครื่องด้วย `gcloud auth application-default login` (ไม่ต้องดาวน์โหลด key file)
