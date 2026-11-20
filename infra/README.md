# infra/

- `cloudbuild.yaml` · build + deploy backend ไป Cloud Run `api-staging` เมื่อ push เข้า `main` (trigger `api-staging-deploy` จาก `trigger-api-staging.yaml`)
- `deploy-staging.ps1` + `cloudbuild-image.yaml` · deploy มือ (ทางสำรอง) · `env/api-staging.yaml` · env ที่ไม่ใช่ secret ใช้ทั้ง 2 ทาง
- frontend deploy ผ่าน Vercel ด้วย GitHub Actions (`.github/workflows/web-deploy.yml`) ดูหัวข้อ "Frontend · Vercel" ด้านล่าง
- Terraform ย้ายไปเทอม 2 (S6) ตอนนี้สร้าง resource ด้วยคำสั่งในหัวข้อ "สร้าง cloud resource" ด้านล่าง

ค่า `--concurrency` และ `--timeout` เป็นค่าเริ่มต้น ปรับตามผลวัดใน PoC P6-lite

## สร้าง cloud resource (Junior ทำครั้งเดียว)

ทำใน S1–S2 เป็นส่วนหนึ่งของ PoC P6-lite (ย้ายมาจาก `docs/team/setup.md` §5 ฉบับ 12 ต.ค.)

**ทำแล้ว 28 ต.ค. (PR #20):** project `anyang-513006` (project number `659706857266`) · เปิด API 5 ตัว · Artifact Registry `anyang` (docker, `asia-southeast1`) · ยังไม่ได้สร้าง secret เพราะ `api-staging` ยังไม่ใช้ (`AI_PROVIDER=fake`)

| GCP project | |
|---|---|
| ประเภท | **Free Trial** · $300 ภายใน 90 วัน · Jam สร้างและถือ billing · Junior เป็น Owner |
| ⚠️ ห้าม | กด **Activate** / **Upgrade** เป็น paid account · ถ้า credit หรือ 90 วันหมด resource จะหยุดเอง ไม่ตัดบัตร |
| Budget alert | $50 (Jam ตั้ง) · ไม่นับ promotional credits จึงเตือนเมื่อเริ่มจ่ายเงินจริง |
| Gemini | ใช้ผ่าน **Vertex AI เท่านั้น** · credit ของ trial ไม่ครอบคลุม API key ของ AI Studio (`GEMINI_API_KEY`) · gateway มี provider `vertex` แล้ว (31 ต.ค. · `specs/features/ai/gemini-vertex.md`): ตั้ง `GOOGLE_CLOUD_PROJECT` + `GOOGLE_CLOUD_LOCATION=global` · credential จาก ADC ไม่ใช้ key file · `api-staging` ใช้ผ่าน runtime SA `api-runtime` ที่มี `roles/aiplatform.user` (ทำแล้ว 11 พ.ย.) |

```bash
gcloud auth login
gcloud config set project anyang-513006
gcloud services enable run.googleapis.com cloudbuild.googleapis.com   artifactregistry.googleapis.com secretmanager.googleapis.com aiplatform.googleapis.com
gcloud artifacts repositories create anyang --repository-format=docker --location=asia-southeast1

```

- **Secret** (สร้างใน Console → Security → Secret Manager → Create secret · ค่าไม่ผ่าน shell history · Replication: Automatic)
  - `supabase-service-role` · ทำแล้ว 11 พ.ย. · key `sb_secret_…` ของ `anyang-staging` · `api-staging` อ่านเป็น env `SUPABASE_SERVICE_ROLE_KEY` (`--set-secrets`) · เปลี่ยนค่า = Add new version แล้ว deploy ใหม่ (`:latest` อ่านตอน instance start)
  - `anthropic-api-key` · ยังไม่สร้าง (fallback ใน `config/ai.yaml` ยังเป็น `TODO`)
- **Runtime SA `api-runtime`** (ทำแล้ว 11 พ.ย. · PR #120) · `api-staging` รันในนาม SA นี้แทน default compute SA (ซึ่งเป็น Editor ของทั้ง project) · มีแค่ 2 สิทธิ์:
  - `roles/aiplatform.user` ระดับ project (Vertex ให้ได้แค่ระดับนี้)
  - `roles/secretmanager.secretAccessor` เฉพาะบน secret `supabase-service-role` · secret ใหม่ต้องให้สิทธิ์ทีละตัว:

    ```powershell
    gcloud secrets add-iam-policy-binding <secret> --project=anyang-513006 --member="serviceAccount:api-runtime@anyang-513006.iam.gserviceaccount.com" --role="roles/secretmanager.secretAccessor"
    ```

- Cloud Build trigger: ทำแล้ว 29 ต.ค. (PR #83) · ดูหัวข้อ "Deploy อัตโนมัติ" ด้านล่าง
- service account ของ Cloud Build: ทำแล้ว 29 ต.ค. (`cloudbuild-deployer` · ยังไม่มีสิทธิ์อ่าน secret เพราะยังไม่ใช้)
- Supabase project ใหม่ (เช่น `anyang-staging`): `npx supabase login` → `npx supabase link --project-ref <ref>` → `npx supabase db push --remote --dry-run` → `npx supabase db push --remote` แล้วเปิด Custom Access Token hook ใน Dashboard (Authentication → Hooks) แล้ว `npx supabase unlink` (ถ้าลืมว่ายัง link อยู่ `db push` ครั้งหน้าจะลงผิด project) · `anyang-dev` ทำแล้ว
  - ⚠️ CLI เวอร์ชันที่ใช้อยู่ (เจอ 9 พ.ย.) ใช้ local stack เป็นค่า default: `db push`, `migration list`, `db query` ต้องใส่ `--remote` ไม่อย่างนั้นจะยิงไปที่ `127.0.0.1:54322` แล้วล้ม (ไม่แตะ project ที่ link ไว้) · ถ้า agent เป็นคนรัน CLI จะขอ `--yes` ให้ใส่หลังจาก Junior ok dry-run แล้วเท่านั้น
  - migration ที่ขึ้นแล้ว (9 พ.ย. · PR #116): `anyang-dev` `0001`–`0003` · `anyang-staging` `0001`–`0003` · เช็คด้วย `npx supabase migration list --remote` · ทั้งสอง project เปิด RLS ครบทุกตาราง public
  - `anyang-staging` อยู่บน free tier ไม่มีคนใช้นานจะถูก pause (`INACTIVE`) · กด Restore ใน Dashboard แล้วรอ `npx supabase projects list` ขึ้น `ACTIVE_HEALTHY` ก่อน link (Dashboard อาจขึ้น Healthy ก่อน · ช่วงนั้น CLI ยังรายงาน `COMING_UP`)
  - `anyang-staging` ทำแล้ว 21 ต.ค.: ref `sfapuygntxuelsxsgkay` · region `ap-southeast-1` (Singapore ใกล้ Cloud Run `asia-southeast1`) · `0001` + `0002` · RLS ครบ 27 ตาราง · hook เปิดแล้ว · `test_SA06_tenant_isolation` ผ่าน · Auth Site URL: `https://anyang-amber.vercel.app` (`anyang-dev` ยังเป็น `http://localhost:3000` เพราะใช้ local อย่างเดียว) · Auth Redirect URLs: `http://localhost:3000/**`, `https://anyang-*-anyang4.vercel.app/**` (glob ของ Supabase หลวมกว่า CORS regex · ต้องทบทวนตอนทำ `anyang-prod`)
- ให้สิทธิ์ Jam เป็น Vertex AI User เพื่อใช้ Gemini บนเครื่องด้วย `gcloud auth application-default login` (ไม่ต้องดาวน์โหลด key file)

## Backend · Cloud Run `api-staging`

> ⚠️ ห้ามตั้ง `AI_PROVIDER: live` คู่กับ `AUTH_REQUIRED: "false"` · URL เป็น public (`--allow-unauthenticated`) คนนอกเรียกแล้วกิน credit ได้
>
> **ตั้งแต่ PR #120 (merge พร้อมหน้า login ของ May):** `AUTH_REQUIRED: "true"` · ทุก endpoint นอก allowlist (`/health`, `/docs`, `/redoc`, `/openapi.json`) ต้องมี `Authorization: Bearer <Supabase JWT>` ไม่มีได้ `401 missing_token` (`specs/features/platform/api-auth.md`) · `AI_PROVIDER: live` บน Vertex · runtime SA `api-runtime` · service role key จาก Secret Manager · หน้าเว็บที่ไม่ส่ง token จะได้ 401 ทุก request

| | |
|---|---|
| URL | https://api-staging-659706857266.asia-southeast1.run.app (`/health`, `/docs`) · อีกชื่อของ service เดียวกัน: `https://api-staging-ws54gmdazq-as.a.run.app` |
| Region | `asia-southeast1` · `--min-instances=0` `--max-instances=2` `--concurrency=40` `--timeout=600` |
| Env | `infra/env/api-staging.yaml` (ไม่มี secret) · `APP_ENV=staging`, `AUTH_REQUIRED=true`, `SUPABASE_URL` + `SUPABASE_ANON_KEY` ของ `anyang-staging`, `AI_PROVIDER=live`, `GOOGLE_CLOUD_PROJECT`, `GOOGLE_CLOUD_LOCATION=global`, CORS ของ Vercel production + localhost + regex ของ preview |
| Secret | `SUPABASE_SERVICE_ROLE_KEY` ← `supabase-service-role:latest` (`--set-secrets`) · ใช้แค่ writer ของ `ai_calls` |
| Runtime SA | `api-runtime@anyang-513006.iam.gserviceaccount.com` (`--service-account`) |
| ตอนนี้ตอบอะไร | `/health` · ข้อความในห้องติวตอบด้วย Gemini จริง (`tutor_reply`) · endpoint อื่นยังเป็น stub ที่คืน fixture (`X-Stub: true`) |
| **Demo link** | https://anyang-amber.vercel.app/preps/00000000-0000-4000-8000-000000000001/room · ห้องติวบน Vercel production ที่ stream คำตอบ stub จาก `api-staging` (ตรวจใน Network แล้ว 28 ต.ค.) |

**Deploy อัตโนมัติ** (P6-lite · ตั้งแล้ว 29 ต.ค.)

| | |
|---|---|
| Trigger | `api-staging-deploy` (`asia-southeast1`) · ตั้งค่าใน `infra/trigger-api-staging.yaml` |
| รันเมื่อ | push เข้า `main` (`^main$`) ที่แก้ `apps/api/**`, `config/**`, `prompts/**` หรือ `infra/**` (แก้ `infra/README.md` ก็ deploy ใหม่ · ไม่เสียหาย) |
| ทำอะไร | `infra/cloudbuild.yaml`: build `apps/api/Dockerfile` → push `asia-southeast1-docker.pkg.dev/anyang-513006/anyang/api:$COMMIT_SHA` → `gcloud run deploy api-staging` ด้วย flag และ `env/api-staging.yaml` ชุดเดียวกับสคริปต์มือ |
| GitHub | connection 2nd gen `github-anyang` (`asia-southeast1`) · repository `anyang` → `jamvess/anyang` · Jam ต่อไว้ (ต้องใช้ admin ของ repo) |
| Service account | `cloudbuild-deployer@anyang-513006.iam.gserviceaccount.com` · `roles/run.admin` (project · ต้องใช้ตั้ง `allUsers` ของ `--allow-unauthenticated`) · `roles/artifactregistry.writer` (เฉพาะ repo `anyang`) · `roles/logging.logWriter` (project · build ใช้ `CLOUD_LOGGING_ONLY`) · `roles/iam.serviceAccountUser` (เฉพาะบน runtime SA `api-runtime` · 11 พ.ย.) · ⚠️ ยังมี binding เดิมบน `659706857266-compute@…` ไว้ rollback · ถอดหลัง deploy ด้วย `api-runtime` ผ่าน (`docs/worklog/chore-staging-live-auth.md` ข้อ 8) |
| ดู build | https://console.cloud.google.com/cloud-build/builds;region=asia-southeast1?project=anyang-513006 หรือ `gcloud builds list --region=asia-southeast1 --limit=5` |
| ดูว่า deploy commit ไหน | `gcloud run services describe api-staging --region=asia-southeast1 --format="value(spec.template.spec.containers[0].image)"` · tag = commit SHA |

- แก้ trigger: แก้ `infra/trigger-api-staging.yaml` แล้วรัน `gcloud builds triggers import --source=infra/trigger-api-staging.yaml --region=asia-southeast1` (ใช้ไฟล์แทน flag เพราะ cmd.exe กิน `^` ของ `^main$`)
- แก้ flag ของ deploy: แก้ทั้ง `cloudbuild.yaml` และ `deploy-staging.ps1` ให้ตรงกัน
- ห้ามกด **Run** trigger มือถ้า `cloudbuild.yaml` บน `main` ยังไม่ใช่ฉบับที่ต้องการ (trigger ใช้ไฟล์จาก commit ที่รัน)

**Deploy มือ** (ทางสำรอง ถ้า trigger มีปัญหา หรืออยาก deploy branch ที่ยังไม่ merge) จาก repo root ใน PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File infra\deploy-staging.ps1
```

- build image ด้วย Cloud Build (`infra/cloudbuild-image.yaml` · ไม่ต้องมี Docker ในเครื่อง) แล้ว `gcloud run deploy` · tag = commit (มี `-dirty-<เวลา>` ถ้ามีไฟล์ยังไม่ commit)
- `.gcloudignore` กันไม่ให้ upload `.env` และทุกอย่างใน `.gitignore` · ตรวจได้ด้วย `gcloud meta list-files-for-upload`
- env ใช้ `--env-vars-file` ไม่ใช้ `--set-env-vars` แบบ `^@^` เพราะ `gcloud.cmd` บน Windows ให้ cmd.exe กิน `^` และค่า CORS มี `,` `^` `$`

**ตรวจหลัง deploy**

```bash
curl -s https://api-staging-659706857266.asia-southeast1.run.app/health
curl -s -o /dev/null -D - -X OPTIONS https://api-staging-659706857266.asia-southeast1.run.app/health -H "Origin: https://anyang-amber.vercel.app" -H "Access-Control-Request-Method: POST" | grep -i access-control-allow-origin
```

**Monday demo checklist** (advisor update · ทำเช้าวันประชุม ก่อนเริ่ม 30 นาที)

1. **Supabase `anyang-staging` ต้อง ACTIVE** · free tier จะ pause project ที่ไม่มีคนใช้ · `npx supabase projects list` ต้องขึ้น `ACTIVE_HEALTHY` (Dashboard ขึ้น Healthy ก่อน CLI ได้) · ถ้าเป็น `INACTIVE` กด Restore ใน Dashboard แล้วรอ · ถ้า pause อยู่ login ไม่ได้ และ API ตอบ `503 auth_unavailable`
2. **อุ่น Cloud Run** · เปิด demo link (https://anyang-amber.vercel.app) 1 ครั้งก่อนประชุม และเปิด `curl -s https://api-staging-659706857266.asia-southeast1.run.app/health` · `--min-instances=0` ทำให้ request แรกเจอ cold start ประมาณ 6 วินาที (P6-lite)
3. **ทดสอบ login ด้วย demo account** · login บน demo link → เปิดห้องติว → ส่ง 1 ข้อความ → ต้องได้คำตอบจาก Gemini แบบ stream (ไม่ใช่ข้อความ stub) · ถ้าได้ 401 ให้ logout แล้ว login ใหม่ (token หมดอายุ)

**กัน cold start ทั้งช่วง demo** (ทางเลือก) ตั้ง min instance เป็น 1 ก่อน demo · หลัง demo ตั้งกลับเป็น 0 ทันที (instance ที่เปิดค้างกิน trial credit)

```powershell
gcloud run services update api-staging --region=asia-southeast1 --min-instances=1   # ก่อน demo
gcloud run services update api-staging --region=asia-southeast1 --min-instances=0   # หลัง demo
```

## Frontend · Vercel

| | |
|---|---|
| Production | https://anyang-amber.vercel.app |
| Vercel project | `anyang` ใน team `anyang4` (Hobby, account ของ Jam) · root directory = `apps/web` |
| Env (Preview) | `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY` ชี้ Supabase `anyang-staging` แล้ว 21 ต.ค. (Config) (URL ไม่มี `/rest/v1/` ต่อท้าย, key เป็น `sb_publishable_...`) · architecture.md: staging = Vercel preview |
| Env (Production) | ชี้ anyang-staging แล้ว 21 ต.ค. (Config) |
| `NEXT_PUBLIC_API_URL` | `https://api-staging-659706857266.asia-southeast1.run.app` ทั้ง Production + Preview (28 ต.ค.) |

**ทำงานยังไง**

- เปิด/อัปเดต PR ที่แก้ `apps/web/**` → job `deploy` สร้าง preview แล้วแนบปุ่ม **View deployment** ใน PR
- push เข้า `main` → deploy production
- workflow ใช้ Vercel CLI (`pull` → `build` → `deploy --prebuilt`) แทน Git integration ของ Vercel เพราะ Hobby ยอม Git deploy เฉพาะ commit ของเจ้าของ account · `apps/web/vercel.json` ปิด Git deploy ไว้กันซ้ำ
- step Deploy ซ่อน `.git` ชั่วคราว ไม่งั้น CLI ส่ง commit author ไปด้วยแล้ว deployment ขึ้น **Blocked** · job มี `timeout-minutes: 15`

**ตั้งค่าครั้งเดียว (ทำแล้ว 14 ต.ค.)**

1. Jam สร้าง project ใน Vercel: import `jamvess/anyang`, root directory `apps/web`, ใส่ env 2 ตัวด้านบน
2. Jam สร้าง token (Vercel → Account Settings → Tokens) แล้วใส่ GitHub Secrets: `VERCEL_TOKEN`, `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID` (2 ตัวหลังอยู่ใน `.vercel/project.json` หลังรัน `vercel link`)

**ข้อควรรู้**

- preview URL และลิงก์ Inspect เปิดได้เฉพาะ account ของ Jam (Vercel Authentication) · คนอื่นจะเจอ 404 หรือหน้า login
- token เป็นของ Jam ถ้าหมดอายุหรือถูกลบ ต้องให้ Jam สร้างใหม่แล้วอัปเดต `VERCEL_TOKEN`
- เพิ่มหรือแก้ env ที่ Vercel → Project → Settings → Environment Variables แล้ว**รัน workflow `web-deploy` ใหม่** · ปุ่ม Redeploy ของ Vercel ใช้ไม่ได้ เพราะ step `vercel pull --environment=…` ดึง env ตอน workflow รัน และค่า `NEXT_PUBLIC_*` ถูกฝังตอน `vercel build` ใน GitHub Actions ไม่ใช่บน Vercel
- ข้อความ template ให้ Jam (เจ้าของ Vercel) เมื่อต้องตั้ง env:

  ```
  Jam ช่วยตั้ง env ใน Vercel ให้หน่อย 🙏
  Vercel → project anyang → Settings → Environment Variables → Add
    Key:   <ชื่อตัวแปร เช่น NEXT_PUBLIC_API_URL>
    Value: <ค่า · URL ไม่มี / ท้าย>
    Environments: ✅ Production ✅ Preview
  แล้ว deploy ใหม่ (ไม่ใช่ปุ่ม Redeploy ของ Vercel):
  GitHub → Actions → web-deploy → run ล่าสุดของ main → Re-run all jobs
  preview ของ PR จะได้ค่าใหม่ตอน push commit ถัดไปของ PR นั้น (หรือ Re-run run ของ PR)
  ```
