# infra/

- `cloudbuild.yaml` · build + deploy backend ไป Cloud Run staging เมื่อ push เข้า `main`
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
| Gemini | ใช้ผ่าน **Vertex AI เท่านั้น** · credit ของ trial ไม่ครอบคลุม API key ของ AI Studio (`GEMINI_API_KEY`) · `GeminiProvider` ตอนนี้ยังใช้ API key ต้องเพิ่มทาง Vertex ก่อนเปิด live (งาน AI gateway ใน S3) |

```bash
gcloud auth login
gcloud config set project anyang-513006
gcloud services enable run.googleapis.com cloudbuild.googleapis.com   artifactregistry.googleapis.com secretmanager.googleapis.com aiplatform.googleapis.com
gcloud artifacts repositories create anyang --repository-format=docker --location=asia-southeast1

# secrets (ค่าจริงใส่ผ่าน stdin ไม่พิมพ์ลง history)
printf '%s' "<service-role-key>" | gcloud secrets create supabase-service-role --data-file=-
printf '%s' "<anthropic-key>"    | gcloud secrets create anthropic-api-key --data-file=-
```

- สร้าง Cloud Build trigger: push เข้า `main` → ใช้ `infra/cloudbuild.yaml`
- ให้ service account ของ Cloud Build มีสิทธิ์ deploy Cloud Run และอ่าน secrets
- Supabase project ใหม่ (เช่น `anyang-staging`): `npx supabase login` → `npx supabase link --project-ref <ref>` → `npx supabase db push` แล้วเปิด Custom Access Token hook ใน Dashboard (Authentication → Hooks) แล้ว `npx supabase unlink` (ถ้าลืมว่ายัง link อยู่ `db push` ครั้งหน้าจะลงผิด project) · `anyang-dev` ทำแล้ว
  - `anyang-staging` ทำแล้ว 21 ต.ค.: ref `sfapuygntxuelsxsgkay` · region `ap-southeast-1` (Singapore ใกล้ Cloud Run `asia-southeast1`) · `0001` + `0002` · RLS ครบ 27 ตาราง · hook เปิดแล้ว · `test_SA06_tenant_isolation` ผ่าน · Auth Site URL: `https://anyang-amber.vercel.app` (`anyang-dev` ยังเป็น `http://localhost:3000` เพราะใช้ local อย่างเดียว) · Auth Redirect URLs: `http://localhost:3000/**`, `https://anyang-*-anyang4.vercel.app/**` (glob ของ Supabase หลวมกว่า CORS regex · ต้องทบทวนตอนทำ `anyang-prod`)
- ให้สิทธิ์ Jam เป็น Vertex AI User เพื่อใช้ Gemini บนเครื่องด้วย `gcloud auth application-default login` (ไม่ต้องดาวน์โหลด key file)

## Backend · Cloud Run `api-staging`

> ⚠️ ห้ามเปิด AI_PROVIDER=live บน api-staging จนกว่าจะเช็ค Supabase JWT ทุก endpoint · URL เป็น public (--allow-unauthenticated) คนนอกเรียกแล้วกิน credit ได้

| | |
|---|---|
| URL | https://api-staging-659706857266.asia-southeast1.run.app (`/health`, `/docs`) · อีกชื่อของ service เดียวกัน: `https://api-staging-ws54gmdazq-as.a.run.app` |
| Region | `asia-southeast1` · `--min-instances=0` `--max-instances=2` `--concurrency=40` `--timeout=600` |
| Env | `infra/env/api-staging.yaml` (ไม่มี secret) · `APP_ENV=staging`, `AI_PROVIDER=fake`, CORS ของ Vercel production + localhost + regex ของ preview |
| ตอนนี้ตอบอะไร | `/health` + stub ห้องติวที่คืน fixture (`X-Stub: true`) · ยังไม่เรียก Supabase หรือ AI |

**Deploy มือ** (ทางสำรองของ P6-lite จนกว่า Cloud Build trigger จะมี) จาก repo root ใน PowerShell:

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

**Demo-day (ศ. 30 ต.ค.)** กัน cold start: เย็นพฤหัส 29 ต.ค. ตั้ง min instance เป็น 1 · หลัง demo ตั้งกลับเป็น 0 ทันที (instance ที่เปิดค้างกิน trial credit)

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
- เพิ่ม env ใหม่ (เช่น `NEXT_PUBLIC_API_URL` ตอนมี `api-staging`) ที่ Vercel → Project → Settings → Environment Variables แล้ว deploy ใหม่
