# API ตรวจ Supabase JWT ทุก endpoint

| | |
|---|---|
| Owner | Jam |
| Branch | `feat/api-jwt-auth` |
| Checklist item | ⭐ API ตรวจ Supabase JWT ทุก endpoint: อ่าน `Authorization: Bearer <jwt>` (api.md "Auth") → ได้ `tenant_id`, `user_id` → ตั้ง `ai_call_context` และส่ง JWT ต่อให้ Supabase ให้ RLS ทำงาน · ไม่มีหรือผิด → 401 |
| Status | in progress · 2026-11-01 |

## Plan

- [ ] 1. 🤖 `/spec-feature` → `specs/features/platform/api-auth.md` (SA-06, AI-04 · api.md Conventions "Auth"): FastAPI dependency อ่าน Bearer → ตรวจด้วย `supabase.auth.get_claims(jwt)` (ES256 ตรวจกับ JWKS ที่ cache ไว้ ไม่ยิง network ทุก request · HS256 ของ Supabase ในเครื่อง/CI fallback เป็น `get_user`) → `tenant_id` จาก claim ของ custom access token hook + `user_id` จาก `sub` → `ai_call_context` · Supabase client ต่อ request ที่ส่ง JWT ของ user (RLS) · error 401 แบบ `ErrorResponse` · `/health`, `/docs`, `/openapi.json` ไม่ต้องมี token · จดคำถามที่เปิดอยู่
- [ ] 2. 🙋 Jam review spec + ตัดสินข้อ "เปิดบังคับเมื่อไหร่" (หน้าเว็บยังไม่ส่ง token · ดู Notes)
- [ ] 3. 🤖 `/spec-to-tests`: unit (token ปลอมที่เซ็นด้วย key ES256 ที่สร้างใน test + JWKS ปลอม · ไม่ต่อ network) · integration (user จริงจาก Supabase ในเครื่อง/CI: มี token → 200 · ไม่มี/ผิด/หมดอายุ → 401 · client ต่อ request เห็นแค่แถวของ tenant ตัวเอง)
- [ ] 4. 🙋 Jam review test
- [ ] 5. 🤖 `/implement-feature` (`app/auth.py` หรือ `app/db/` · ต่อ dependency กับ router ห้องติว · `tutor_turn.reply_events` ตั้ง `ai_call_context` ข้างใน generator ตาม `call_context.py`)
- [ ] 6. 🤖 ruff + pytest + integration (🙋 เปิด Docker Desktop ถ้าจะรันกับ Supabase ในเครื่อง · ไม่งั้นรันกับ `anyang-dev` เหมือน #95)
- [ ] 7. 🤖 `/work-done`

## Definition of done

- ทุก endpoint ยกเว้น `/health`, `/docs`, `/openapi.json`: ไม่มี token, token ผิด, หมดอายุ หรือไม่มี `tenant_id` → `401` แบบ `{"error": {"code", "message"}}` · token ถูก → ได้ `tenant_id`, `user_id` ใน request
- AI call ใน request ที่ผ่าน auth ได้ `ai_call_context` → มีแถวใน `ai_calls` (ปิดช่องที่ค้างจาก #95)
- มี Supabase client ต่อ request ที่ส่ง JWT ของ user ให้ RLS ทำงาน + integration test ว่าเห็นแค่ tenant ตัวเอง (SA-06)
- ไม่ทำให้หน้า demo บน Vercel พังก่อนหน้าเว็บส่ง token (ตามที่ตัดสินในขั้น 2)
- CI เขียว · checklist ข้อ JWT ติ๊กหรือมีหมายเหตุว่าเหลืออะไร

## Decisions

- 2026-11-01 · Jam รับข้อนี้เอง (เพิ่มใน checklist S3 ของ Jam · PR #97) · งาน backend จึงชวน Junior ดูย้อนหลัง

## Next step

ขั้น 1: รัน `/spec-feature SA-06 AI-04` → `specs/features/platform/api-auth.md` ตามแผนข้อ 1

## Waiting on

- May: หน้าเว็บยังไม่มี login และไม่ส่ง `Authorization` (ไม่มีใน `apps/web/lib`, `apps/web/app`) · ต้องมีก่อนจะบังคับ 401 บน staging ได้
- Junior: (1) ยืนยันวิธีตรวจ (`get_claims` + JWKS) และการเพิ่ม `pyjwt` เป็น dependency ตรงถ้าต้องใช้ (2) `api-staging` ยังไม่มี `SUPABASE_URL` / `SUPABASE_ANON_KEY` (`infra/env/api-staging.yaml`) (3) `anyang-staging` (`sfapuygntxuelsxsgkay`) ต่อไม่ได้ตอน 1 พ.ย. (`/auth/v1/.well-known/jwks.json` ไม่ตอบ · อาจถูก pause)

## Notes for next time

- 1 พ.ย. `anyang-dev` เซ็น JWT ด้วย ES256 (JWKS มี key `EC`/`ES256`) · Supabase CLI ในเครื่องเซ็นด้วย HS256 · `supabase-py` 2.32 มี `auth.get_claims(jwt)`: asymmetric ตรวจกับ JWKS, HS256 fallback ไป `get_user`
- `pyjwt` + `cryptography` อยู่ใน `uv.lock` แล้วผ่าน `supabase` (ยังไม่ใช่ dependency ตรง)
