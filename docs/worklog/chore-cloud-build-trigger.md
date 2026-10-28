# Cloud Build trigger: merge เข้า main → build → deploy api-staging อัตโนมัติ (P6-lite)

| | |
|---|---|
| Owner | Junior |
| Branch | `chore/cloud-build-trigger` |
| Checklist item | Cloud Build trigger: merge → deploy `api-staging` อัตโนมัติ (P6-lite) |
| Status | in progress · 2026-10-29 |

## Plan

ต่อจาก PR #20 (deploy มือด้วย `infra/deploy-staging.ps1`) · Junior รัน `gcloud` ใน PowerShell เองทีละคำสั่ง · การต่อ GitHub ต้องใช้สิทธิ์ admin ของ repo จึงเป็นงานของ Jam

- [x] 1. 🤖 แก้ `infra/cloudbuild.yaml` ให้ตรงกับ `deploy-staging.ps1`: `--env-vars-file=infra/env/api-staging.yaml` (`AI_PROVIDER=fake`), `--allow-unauthenticated`, `--max-instances=2`, `asia-southeast1`, ไม่มี `--set-secrets` (เอา `anthropic-api-key` และ `supabase-service-role` ออก) · `options.logging: CLOUD_LOGGING_ONLY` (บังคับเมื่อใช้ service account ที่สร้างเอง) · + sub-bullet เรื่อง `min-instances` ใน `sprint-checklists.md`
- [x] 2. 🙋 สร้าง service account `cloudbuild-deployer` และให้ role ที่ใช้ deploy (Claude ให้คำสั่งทีละตัว): `run.admin` (deploy + ตั้ง `allUsers` invoker ของ `--allow-unauthenticated`), `artifactregistry.writer`, `logging.logWriter` และ `iam.serviceAccountUser` บน runtime SA ของ Cloud Run (`659706857266-compute@developer.gserviceaccount.com`)
- [x] 3. 🙋 Jam ต่อ GitHub กับ Cloud Build (2nd gen, `asia-southeast1`) แล้ว link repo `jamvess/anyang` (Claude ร่างขั้นตอนให้ส่ง Jam)
- [ ] 4. 🙋 สร้าง trigger `api-staging-deploy` ด้วย `gcloud builds triggers create github`: branch `^main$` เท่านั้น · `--included-files=apps/api/**,config/**,prompts/**,infra/**` · `--build-config=infra/cloudbuild.yaml` · `--service-account` = `cloudbuild-deployer`
- [ ] 5. 🤖 อัปเดต `infra/README.md` (trigger, SA, roles, วิธีดู build) + checklist
- [ ] 6. 🙋 ทดสอบจริง: merge PR นี้ (แก้ `infra/**` จึง trigger เอง) → ดู build ใน Console → Claude ตรวจว่า image ของ revision ใหม่ใช้ tag = commit ของ merge และ `/health` + CORS ยังผ่าน

## Definition of done

- merge PR แล้ว staging อัปเดตเองภายใน 10 นาที (checklist S2 ของ Junior) · revision ใหม่ใช้ image tag = `$COMMIT_SHA` ของ merge commit
- trigger รันเฉพาะ push เข้า `main` ที่แก้ `apps/api/**`, `config/**`, `prompts/**` หรือ `infra/**`
- env ของ revision ที่ trigger deploy ตรงกับ `infra/env/api-staging.yaml` (`AI_PROVIDER=fake`, CORS ครบ) และไม่มี secret
- `infra/README.md` ตรงกับที่ตั้งจริง · ติ๊ก checklist ข้อ Cloud Build trigger

## Done today

- 2026-10-29 · ขั้น 1: แก้ `infra/cloudbuild.yaml` + sub-bullet `min-instances` ใน checklist + note runtime SA ใน `infra/README.md`
- 2026-10-29 · ขั้น 3: Jam ต่อ GitHub (`github-anyang` / `anayang`)
- 2026-10-29 · ขั้น 2: SA `cloudbuild-deployer@anyang-513006.iam.gserviceaccount.com` · `run.admin` (project) · `artifactregistry.writer` (เฉพาะ repo `anyang`) · `logging.logWriter` (project) · `iam.serviceAccountUser` (เฉพาะบน `659706857266-compute@developer.gserviceaccount.com`) · IAM policy ยืนยันว่า compute SA มี `roles/editor`
- 2026-10-29 · ขั้น 4 (ไฟล์): `infra/trigger-api-staging.yaml` สำหรับ `gcloud builds triggers import`

## Decisions

- 2026-10-29 · สร้าง trigger จากไฟล์ `infra/trigger-api-staging.yaml` + `gcloud builds triggers import` แทน flag ของ `triggers create` · `--branch-pattern=^main$` ผ่าน `gcloud.cmd` แล้ว cmd.exe จะกิน `^` (เหลือ `main$` ซึ่ง match branch อย่าง `foo-main` ด้วย) · ไฟล์ยัง version ไว้ใน repo และใช้ import ซ้ำเพื่ออัปเดตได้ · ไฟล์เป็น ASCII ล้วน
- 2026-10-29 · `artifactregistry.writer` ให้เฉพาะ repo `anyang` และ `iam.serviceAccountUser` ให้เฉพาะบน compute SA ไม่ให้ระดับ project · least privilege

- 2026-10-29 · Jam ต่อ GitHub แล้ว: connection 2nd gen `github-anyang` (`asia-southeast1`) · repository ชื่อ **`anayang`** (พิมพ์ผิด แต่ชี้ `jamvess/anyang` จริง · Junior ตรวจด้วย `gcloud builds repositories list`) · ใช้ชื่อนี้ตามจริงใน trigger ไม่แก้ชื่อ

- 2026-10-29 · (Junior) ก่อนเปิด `AI_PROVIDER=live` ต้องย้าย `api-staging` ไปใช้ runtime SA แยกที่มีแค่ Vertex AI User + Secret Manager Secret Accessor · default compute SA ได้ Editor ทั้ง project · ไม่ทำใน PR นี้ จดไว้ใน `infra/README.md` ข้างคำเตือนเรื่อง live
- 2026-10-29 · `cloudbuild.yaml` ใช้ `--env-vars-file` เหมือนสคริปต์ จึงไม่ต้องเขียน `$` ของ regex เป็น `$$` (Cloud Build แทนค่าเฉพาะใน `cloudbuild.yaml` ไม่แทนในไฟล์ที่ gcloud อ่าน) · note เก่าใน checklist เรื่อง `$$` และ `^@^` จึงไม่ใช้แล้ว

- 2026-10-29 · ใช้ service account แยก `cloudbuild-deployer` แทน default ของ Cloud Build · ให้สิทธิ์เท่าที่ต้องใช้ deploy และเห็นชัดว่า trigger ทำอะไรได้บ้าง
- 2026-10-29 · ห้ามกด Run trigger มือก่อน PR นี้ merge · `cloudbuild.yaml` บน `main` ยังตั้ง `AI_PROVIDER=live` + secret ที่ไม่มีอยู่ · การ merge PR นี้ (แก้ `infra/**`) คือการทดสอบครั้งแรก

## Next step

ขั้น 4: Junior รัน `gcloud builds triggers import --source=infra/trigger-api-staging.yaml --region=asia-southeast1` จาก repo root แล้ว `gcloud builds triggers describe api-staging-deploy --region=asia-southeast1` ดูว่า `branch: ^main$` ครบ · ห้ามกด Run trigger

## Waiting on

ไม่มี

## Notes for next time

- `infra/**` รวม `infra/README.md` ด้วย แก้ docs ใน `infra/` ก็ deploy ใหม่ (ไม่มีผลเสีย แค่ build ประมาณ 3 นาที)
