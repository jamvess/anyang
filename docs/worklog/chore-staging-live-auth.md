# api-staging: ตรวจ token ทุก endpoint + runtime SA แยก + Gemini จริงบน Vertex

| | |
|---|---|
| Owner | Junior |
| Branch | `chore/staging-live-auth` |
| Checklist item | เตรียม staging สำหรับ demo รวม |
| Status | in progress · 2026-11-11 |

## Plan

- [ ] 1. 🙋 เช็คว่า `anyang-staging` เป็น `ACTIVE_HEALTHY` (`npx supabase projects list`) แล้วส่ง `SUPABASE_URL` + anon key (`sb_publishable_...`) ของ `anyang-staging` ให้ Claude · ค่านี้ไม่ใช่ secret (หน้าเว็บใช้อยู่แล้ว · `api-auth.md` §10 ข้อ 4)
- [ ] 2. 🤖 `infra/env/api-staging.yaml`: `AUTH_REQUIRED: "true"`, `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `AI_PROVIDER: live`, `GOOGLE_CLOUD_PROJECT: anyang-513006`, `GOOGLE_CLOUD_LOCATION: global`
- [ ] 3. 🤖 `infra/cloudbuild.yaml` + `infra/deploy-staging.ps1` (ตรงกัน): `--service-account=api-runtime@anyang-513006.iam.gserviceaccount.com` + `--set-secrets=SUPABASE_SERVICE_ROLE_KEY=supabase-service-role:latest`
- [ ] 4. 🙋 สร้าง secret `supabase-service-role` ใน Secret Manager (พิมพ์ค่าเองผ่าน stdin · Claude ไม่เห็นค่า)
- [ ] 5. 🤖 (หลัง Junior ok คำสั่ง) สร้าง SA `api-runtime` · `roles/aiplatform.user` ระดับ project · `roles/secretmanager.secretAccessor` เฉพาะ secret `supabase-service-role` · `cloudbuild-deployer` ได้ `roles/iam.serviceAccountUser` บน `api-runtime` (ถอดจาก default compute SA)
- [ ] 6. 🤖 `infra/README.md`: อัปเดตหัวข้อ Backend (auth เปิด, runtime SA, secret, live) + "Monday demo checklist"
- [ ] 7. 🙋 บอกกลุ่ม (แก้ `infra/`) แล้ว merge ตามเวลาที่ตกลงในข้อ Decisions · trigger deploy เอง
- [ ] 8. 🤖 ตรวจหลัง deploy: `/health` 200 · route ใดๆ ไม่มี token → 401 `missing_token` · token ของ demo account → ข้อความ tutor stream จาก Gemini · มีแถวใน `ai_calls` · runtime SA = `api-runtime`

## Definition of done

- `api-staging` รันด้วย `api-runtime` (ไม่ใช่ default compute SA ที่เป็น Editor)
- ทุก endpoint นอก allowlist ตอบ 401 เมื่อไม่มี token · `AUTH_REQUIRED: "true"` ใน `infra/env/api-staging.yaml`
- `AI_PROVIDER=live` ผ่าน Vertex · service role key มาจาก Secret Manager ไม่อยู่ในไฟล์ใน repo
- `infra/README.md` มี Monday demo checklist (Supabase ACTIVE, เปิด demo link ก่อนประชุมให้ Cloud Run อุ่น, ทดสอบ login ด้วย demo account)

## Decisions

- 2026-11-11 · เป้าหมายคือ advisor update วันจันทร์ (ไม่ใช่ demo ศุกร์ 13 พ.ย.) · user journey เดียวบน staging: login → สร้าง exam prep → upload sheet → topics → ห้องติว AI จริง → บันทึกและกลับมาต่อได้ · ให้ใช้ได้ภายในเย็นวันอาทิตย์ · ส่วนไหนยังไม่พร้อมต้องล้มอย่างนุ่มนวล (stub มีป้ายชัด) ไม่ใช่พัง
- 2026-11-11 · runtime SA แยก `api-runtime` · env ที่ไม่ใช่ secret อยู่ใน `infra/env/api-staging.yaml` · secret อยู่ใน Secret Manager

## Next step

ข้อ 1: Junior ส่ง URL + anon key ของ `anyang-staging`

## Waiting on

- May: หน้า login ที่ส่ง `Authorization: Bearer` (`api-auth.md` §10 ข้อ 1) · ถ้า merge ก่อนหน้านี้ ห้องติวบน Vercel จะได้ 401

## Notes for next time

- `anyang-staging` บน free tier ถูก pause ได้ · ถ้า JWKS ไม่ตอบ token จะตรวจไม่ได้ (ได้ `503 auth_unavailable`)
