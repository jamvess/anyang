# api-staging: ตรวจ token ทุก endpoint + runtime SA แยก + Gemini จริงบน Vertex

| | |
|---|---|
| Owner | Junior |
| Branch | `chore/staging-live-auth` |
| Checklist item | เตรียม staging สำหรับ demo รวม |
| Status | in progress · 2026-11-11 |

## Plan

- [x] 1. 🙋 (11 พ.ย. · Dashboard: Healthy, migration ล่าสุด topic_sources) เช็คว่า `anyang-staging` เป็น `ACTIVE_HEALTHY` (`npx supabase projects list`) แล้วส่ง `SUPABASE_URL` + anon key (`sb_publishable_...`) ของ `anyang-staging` ให้ Claude · ค่านี้ไม่ใช่ secret (หน้าเว็บใช้อยู่แล้ว · `api-auth.md` §10 ข้อ 4)
- [x] 2. 🤖 `infra/env/api-staging.yaml`: `AUTH_REQUIRED: "true"`, `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `AI_PROVIDER: live`, `GOOGLE_CLOUD_PROJECT: anyang-513006`, `GOOGLE_CLOUD_LOCATION: global`
- [x] 3. 🤖 `infra/cloudbuild.yaml` + `infra/deploy-staging.ps1` (ตรงกัน): `--service-account=api-runtime@anyang-513006.iam.gserviceaccount.com` + `--set-secrets=SUPABASE_SERVICE_ROLE_KEY=supabase-service-role:latest`
- [x] 4. 🙋 สร้าง secret `supabase-service-role` ใน Secret Manager (พิมพ์ค่าเองผ่าน stdin · Claude ไม่เห็นค่า)
- [x] 5. 🤖 (หลัง Junior ok คำสั่ง) สร้าง SA `api-runtime` · `roles/aiplatform.user` ระดับ project · `roles/secretmanager.secretAccessor` เฉพาะ secret `supabase-service-role` · `cloudbuild-deployer` ได้ `roles/iam.serviceAccountUser` บน `api-runtime` (ถอดจาก default compute SA)
- [x] 6. 🤖 `infra/README.md`: อัปเดตหัวข้อ Backend (auth เปิด, runtime SA, secret, live) + "Monday demo checklist"
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
- 2026-11-11 · merge PR นี้พร้อม PR login ของ May (ทางเลือก 1) · Claude ไม่ merge เอง ต้องถาม Junior ทุกครั้ง
- 2026-11-11 · ลำดับงานของ Junior สำหรับวันจันทร์ (Junior ส่งกลุ่มแล้ว): 1) login + #120 2) exam prep API 3) บันทึก messages + resume 4) upload + Storage 5) ingestion (Jam เป็นเจ้าของ · Junior ช่วยเขียน DB) · ไม่ทันให้ตัดจากล่างขึ้นบน
- 2026-11-11 · Monday demo checklist มี 3 ข้อไปก่อน · เพิ่มการซ้อม journey เต็มวันเสาร์ 15 พ.ย. เมื่อชิ้นอื่นพร้อม

## Next step

ข้อ 7: รอ PR login ของ May → Junior บอกกลุ่ม (แก้ `infra/`) → ถาม Junior ก่อน merge #120 · หลัง deploy ทำข้อ 8 แล้วถอด `serviceAccountUser` ของ deployer ออกจาก default compute SA

## Waiting on

- May: หน้า login ที่ส่ง `Authorization: Bearer` (`api-auth.md` §10 ข้อ 1) · ถ้า merge ก่อนหน้านี้ ห้องติวบน Vercel จะได้ 401

## Notes for next time
- secret `supabase-service-role` เป็น key แบบใหม่ `sb_secret_` (ไม่ใช่ JWT `service_role` แบบเดิม) · supabase-py 2.32 สร้าง client ได้ · หลักฐานว่าเขียนได้: test RLS isolation บน staging ผ่านด้วย `SUPABASE_SERVICE_ROLE_KEY=sb_secret_…` ซึ่งใช้ client service role สร้าง user, tenant และแถว (Junior 11 พ.ย.) · ยังต้องยืนยันในข้อ 8 ว่ามีแถวใน `ai_calls` ถ้าไม่มี ให้ดู log `ai_calls insert failed`

- `anyang-staging` บน free tier ถูก pause ได้ · ถ้า JWKS ไม่ตอบ token จะตรวจไม่ได้ (ได้ `503 auth_unavailable`)
