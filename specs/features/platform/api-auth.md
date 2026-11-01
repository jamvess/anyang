# Feature: API ตรวจ Supabase JWT ทุก endpoint

| | |
|---|---|
| Area | platform |
| Requirements | SA-06, NFR-S1, AI-04, SA-03, NFR-P1 |
| Owner | Jam (งาน backend · Junior ดูย้อนหลัง) |
| Reviewer | Jam · Junior (ข้อ backend ใน §10) · May (§10 ข้อ 1 · หน้าเว็บ) |
| Status | implemented (PR #98) · approved (Jam 2026-11-01 · §10 ข้อ 2, 3 ตามข้อเสนอ · ข้อ 1 รอ May · ข้อ 4–6 ใช้ข้อเสนอไปก่อน รอ Junior) |
| Related system spec | `api.md` Conventions "Auth", "Error" · `0001_init.sql` `custom_access_token_hook`, `current_tenant_id()`, RLS ทุกตาราง · `apps/api/CLAUDE.md` "Database" · `ai-calls-log.md` §2.1 (`ai_call_context`) · `tutor-reply-stream.md` §9–10 ข้อ 1 · `infra/README.md` ⚠️ "ห้ามเปิด AI_PROVIDER=live …" |

## 1. Context

`api.md` กำหนดว่าทุก request ส่ง `Authorization: Bearer <jwt>` ของ Supabase และ backend ส่ง token นี้ต่อให้ Supabase เพื่อให้ RLS ทำงาน แต่ API ตอนนี้ไม่อ่าน token เลย ผลคือ (1) `ai_calls` ไม่มีแถวเพราะไม่รู้ tenant (`ai-calls-log.md`) (2) ยังบันทึก `messages` ไม่ได้ (3) เปิด live AI บน `api-staging` ไม่ได้เพราะ URL เป็น public · feature นี้เพิ่มการตรวจ token เป็น FastAPI dependency ของทุก endpoint ที่ไม่ใช่ public ได้ `tenant_id` + `user_id` ไปใช้ใน request ตั้ง `ai_call_context` ให้ AI call และมี Supabase client ต่อ request ที่ส่ง JWT ของ user · หน้าเว็บยังไม่มี login และไม่ส่ง token จึงมีสวิตช์ `AUTH_REQUIRED` (Jam ตัดสิน 2026-11-01) ให้ staging ปิดการบังคับไว้ก่อน

## 2. Behavior

**1. ตรวจ token** (dependency `get_auth` ใน module ใหม่ `app/auth.py`)

1. อ่าน header `Authorization` · รูปแบบต้องเป็น `Bearer <token>` (ไม่สนตัวพิมพ์ของคำว่า `Bearer`) · header อื่นหรือว่าง = ไม่มี token
2. ตรวจ token ด้วย `supabase.auth.get_claims(token)` ของ client ที่ใช้ anon key (สร้างครั้งเดียวต่อ process) · ES256 (Supabase cloud) ตรวจลายเซ็นกับ JWKS ที่ cache ไว้ ไม่ยิง network ทุก request · HS256 (Supabase ในเครื่องและใน CI) fallback เป็น `get_user` ที่ถาม Auth server · ตรวจ `exp` ด้วย
3. ต้องมี claim `sub` (UUID ของ user) และ `tenant_id` (UUID ที่ `custom_access_token_hook` ใส่ · `0001_init.sql`) · `role` ต้องเป็น `authenticated` (กัน anon key ซึ่งก็เป็น JWT แต่ไม่ใช่ user)
4. ผ่าน → คืน `AuthContext(tenant_id: UUID, user_id: UUID, token: str)`
5. การตรวจต้องไม่ block event loop (เช่น เรียก client แบบ async หรือรันใน thread)

**2. ตอบเมื่อไม่ผ่าน** (`401` · body เป็น `ErrorResponse` · header `WWW-Authenticate: Bearer`)

| กรณี | `error.code` |
|---|---|
| ไม่มี token (และ `AUTH_REQUIRED=true`) | `missing_token` |
| ลายเซ็นผิด, รูปแบบผิด, หมดอายุ, `role` ไม่ใช่ `authenticated` | `invalid_token` |
| ไม่มี `sub` หรือ `tenant_id` หรือไม่ใช่ UUID | `invalid_token` |
| Supabase Auth ติดต่อไม่ได้ (network, timeout, 429, 5xx) · **`503`** ไม่มี `WWW-Authenticate` · เพิ่มจาก self-review ของ #98 เพราะ 401 จะทำให้ supabase-js ไล่ทุกคนไป login ใหม่ตอน Supabase ล่ม | `auth_unavailable` |

`message` เป็นข้อความคงที่ ไม่มีรายละเอียดจาก exception (รายละเอียดอยู่ใน log ระดับ INFO พร้อม `request_id` · ไม่ log ตัว token)

**3. สวิตช์ `AUTH_REQUIRED`** (env ใหม่ · `EnvSettings.auth_required: bool = True`)

| | มี token ที่ถูก | มี token ที่ผิด | ไม่มี token |
|---|---|---|---|
| `true` | ผ่าน · `AuthContext` | `401 invalid_token` | `401 missing_token` |
| `false` | ผ่าน · `AuthContext` | `401 invalid_token` | ผ่าน · ไม่มี `AuthContext` (`None`) |

- ค่าเริ่มต้นใน code เป็น `true` (ปลอดภัยไว้ก่อน) · `infra/env/api-staging.yaml` ตั้ง `AUTH_REQUIRED: "false"` จนกว่าหน้าเว็บจะส่ง token (§10 ข้อ 1) · `.env.example` ดู §10 ข้อ 2
- ถ้า `SUPABASE_URL` หรือ `SUPABASE_ANON_KEY` ว่าง: `AUTH_REQUIRED=true` → แอป start ไม่ได้ (`get_settings()` หรือ lifespan raise · พังตอน deploy ไม่ใช่ตอน request แรก เหมือน config อื่นใน `app/main.py`) · `AUTH_REQUIRED=false` → ไม่ตรวจ token เลย ทุก request ไม่มี `AuthContext` และ log WARNING 1 ครั้งตอน start (api-staging ตอนนี้ไม่มี env ของ Supabase · §10 ข้อ 4)

**4. Endpoint ไหนต้องตรวจ**

- ทุก route ของแอปต้องผ่าน `get_auth` ยกเว้น allowlist: `GET /health`, `/docs`, `/docs/oauth2-redirect`, `/redoc`, `/openapi.json` · CORS preflight (`OPTIONS`) จบที่ CORS middleware ก่อนถึง route จึงไม่โดนตรวจ
- ใส่เป็น dependency ระดับ router (`APIRouter(dependencies=...)` หรือ `include_router(..., dependencies=...)`) เพื่อให้ router ใหม่ต้องใส่ด้วย · มี test ที่ไล่ทุก route ใน `app.routes` แล้วยืนยันว่าทุกตัวนอก allowlist ตอบ 401 เมื่อไม่มี token (`AUTH_REQUIRED=true`) · router ใหม่ที่ลืมใส่จะทำให้ test นี้ล้ม
- OpenAPI: ทุก route ที่ตรวจมี response `401` แบบ `ErrorResponse` และ security scheme `HTTPBearer` (หน้า `/docs` มีปุ่ม Authorize · `pnpm gen:api` ได้ type ของ 401)

**5. ใช้ผลการตรวจ**

- `POST /sessions/{id}/messages` ส่ง `AuthContext` ให้ `tutor_turn.reply_events` · `reply_events` ครอบ `gateway.stream(...)` ด้วย `with ai_call_context(tenant_id, user_id):` **ข้างใน generator** (ตาม docstring ของ `app/ai/call_context.py` · ถ้าครอบนอก `EventSourceResponse` context จะหมดก่อน stream รัน) · ไม่มี `AuthContext` → ไม่ตั้ง context (เหมือนเดิม: log อย่างเดียว)
- `session_id` ยังไม่ตั้ง เพราะ session ยังเป็น stub ที่ไม่มีแถวใน `tutor_sessions` (FK ของ `ai_calls.session_id` · `ai-calls-log.md` Open point 4 ของ #95)
- Dependency `get_user_db(auth) -> supabase.Client`: client ต่อ request ที่ใช้ anon key + header `Authorization: Bearer <token ของ user>` ให้ RLS ใช้ `current_tenant_id()` · endpoint ตอนนี้ยังไม่มีตัวไหนอ่าน DB (เป็น stub) · feature นี้เตรียม dependency + integration test ว่า RLS ทำงานผ่านมัน · ห้ามใช้ service role ใน request ของ user (`apps/api/CLAUDE.md`) ยกเว้น `ai_calls` writer ที่มีอยู่แล้ว

## 3. Inputs and outputs

| | Type / schema | ตัวอย่าง |
|---|---|---|
| Input | header `Authorization` · env `AUTH_REQUIRED`, `SUPABASE_URL`, `SUPABASE_ANON_KEY` | `Authorization: Bearer eyJhbGciOiJFUzI1NiIsImtpZCI6…` |
| Output (ผ่าน) | `AuthContext(tenant_id, user_id, token)` ใน request · `ai_call_context` ระหว่าง stream | `tenant_id=4c1e…`, `user_id=9b0a…` |
| Output (ไม่ผ่าน) | `401` + `WWW-Authenticate: Bearer` + `ErrorResponse` | `{"error": {"code": "invalid_token", "message": "Sign in again"}}` |

## 4. Acceptance criteria

Unit test ไม่ต่อ network: token เซ็นด้วย key ES256 ที่สร้างใน test และ JWKS ของ key นั้นป้อนให้ตัวตรวจ (หรือแทนตัวตรวจด้วยของปลอมผ่าน `app.dependency_overrides`) · integration ใช้ user จริงของ Supabase ในเครื่อง/CI (HS256) แบบเดียวกับ `test_rls_isolation.py`

**ตรวจ token (`AUTH_REQUIRED=true`)**

- **AC-1 (SA-06)** Given token ES256 ที่ถูก มี `sub`, `tenant_id`, `role=authenticated` When เรียก endpoint ที่ตรวจ Then ผ่าน และ handler ได้ `AuthContext` ที่ `tenant_id`, `user_id` ตรงกับ claim
- **AC-2 (SA-06)** Given ไม่มี header `Authorization` When เรียก endpoint ที่ตรวจ Then `401` · `error.code = missing_token` · มี `WWW-Authenticate: Bearer` · body ผ่าน `ErrorResponse`
- **AC-3 (SA-06)** Given header ที่ไม่ใช่ Bearer (`Basic abc`, `Bearer` เปล่า, ว่าง) When เรียก Then `401 missing_token` · และ `bearer <token>` ตัวเล็กผ่านได้เหมือน AC-1
- **AC-4 (SA-06)** Given token ที่ (ก) ลายเซ็นผิด (ข) เซ็นด้วย key อื่นที่ไม่อยู่ใน JWKS (ค) หมดอายุ (ง) ไม่ใช่ JWT (parametrize) When เรียก Then `401 invalid_token`
- **AC-5 (SA-06)** Given token ที่ถูกแต่ (ก) ไม่มี `tenant_id` (ข) `tenant_id` ไม่ใช่ UUID (ค) ไม่มี `sub` (ง) `role=anon` (parametrize) When เรียก Then `401 invalid_token`
- **AC-6 (SA-06)** Given token ผิด When เรียก Then `error.message` เป็นข้อความคงที่ ไม่มีข้อความจาก exception และ log ไม่มีตัว token

**สวิตช์**

- **AC-7 (SA-06)** Given `AUTH_REQUIRED=false` When ไม่มี token Then ผ่าน และ handler ได้ `None` · When token ผิด Then `401 invalid_token` · When token ถูก Then ได้ `AuthContext`
- **AC-8 (SA-06)** Given `AUTH_REQUIRED=true` และ `SUPABASE_URL` ว่าง When start แอป (หรือ `get_settings()`) Then raise พร้อมข้อความที่บอกชื่อ env ที่ขาด · Given `AUTH_REQUIRED=false` และ `SUPABASE_URL` ว่าง Then start ได้ · มี WARNING 1 บรรทัด · request ที่มี token ก็ผ่านโดยไม่มี `AuthContext`

**Endpoint ไหนต้องตรวจ**

- **AC-9 (SA-06)** Given `AUTH_REQUIRED=true` และไม่มี token When ไล่ทุก route ใน `app.routes` (ใส่ UUID ใน path parameter) Then ทุก route นอก allowlist ตอบ `401` · route ใน allowlist (`/health`, `/docs`, `/openapi.json` …) ตอบ 200
- **AC-10 (SA-06)** Given ไม่มี token When `OPTIONS` preflight จาก origin ที่อนุญาต Then ได้ header CORS ปกติ ไม่ใช่ 401
- **AC-11 (SA-06)** Given `/openapi.json` Then ทุก route ที่ตรวจมี response `401` อ้าง `ErrorResponse` และมี security scheme แบบ HTTP bearer

**ใช้ผลการตรวจ**

- **AC-12 (AI-04, SA-03)** Given token ที่ถูกของ tenant T, user U และ gateway ปลอมที่มี `AICallLog` กับ writer ปลอม When `POST /sessions/{id}/messages` ด้วย `{text}` แล้วอ่าน stream จนจบ Then writer ได้ 1 แถว `tenant_id = T`, `user_id = U`, `purpose = tutor_reply`, `session_id = null`
- **AC-13 (AI-04)** Given `AUTH_REQUIRED=false` และไม่มี token When ส่งข้อความเดียวกัน Then stream ได้เหมือนเดิม (`token` … `done`) และ writer ไม่ได้แถว (log อย่างเดียว)
- **AC-16 (SA-06)** (self-review #98) Given Supabase Auth ตอบไม่ได้ (เช่น JWKS ตอบ 503) When เรียกด้วย token Then `503 auth_unavailable` ไม่ใช่ 401 · และไม่มี `WWW-Authenticate`
- **AC-17 (AI-04)** (self-review #98) Given token ที่ถูก When client ปิด stream กลางทาง Then writer ยังได้ 1 แถวที่มี `tenant_id` (`status = error`)
- **AC-14 (NFR-P1)** Given token ES256 ที่ถูก When เรียก 2 ครั้งติดกัน Then ตัวตรวจขอ JWKS ไม่เกิน 1 ครั้ง (cache) และไม่ยิง Auth server (`get_user`)

**Integration (Supabase ในเครื่อง/CI)**

- **AC-15 (SA-06)** Given user จริง A (signup trigger ให้ personal tenant · hook ใส่ `tenant_id`) When เรียก endpoint ที่ตรวจด้วย access token ของ A Then ผ่าน และ `AuthContext.tenant_id` = tenant ของ A · token ของ A ที่แก้ตัวอักษรท้ายสุด → `401 invalid_token`
- **AC-tenant (SA-06, NFR-S1)** Given user A, B มีแถว `exam_preps` คนละแถว When ใช้ `get_user_db(AuthContext ของ A)` select `exam_preps` Then เห็นแค่แถวของ A · insert แถวที่ `tenant_id` ของ B → ถูกปฏิเสธ (`42501`)

**ไม่มี** AC-boundary: feature นี้ไม่ใช้ค่าใน `config/learning.yaml` · ค่า `exp` ใช้ของ Supabase (`jwt_expiry` ใน `supabase/config.toml`)

## 5. Data changes

ไม่มี · ใช้ `custom_access_token_hook` และ policy ใน `0001_init.sql` ตามเดิม

## 6. API / SSE changes

| Endpoint / event | Request | Response |
|---|---|---|
| ทุก endpoint นอก allowlist (ตอนนี้ 4 endpoint ของห้องติว) | header `Authorization: Bearer <jwt>` (มีอยู่แล้วใน api.md Conventions · ตอนนี้บังคับจริง) | เพิ่ม `401` แบบ `ErrorResponse` code `missing_token` / `invalid_token` + `WWW-Authenticate: Bearer` |
| OpenAPI | — | security scheme `HTTPBearer` + response 401 ทุก route ที่ตรวจ (`pnpm gen:api` ใหม่) |

## 7. AI calls

ไม่มี (ไม่เรียก AI เพิ่ม · แค่ตั้ง `ai_call_context` ให้ call ที่มีอยู่)

## 8. Test plan

| Test | ระดับ | ครอบคลุม AC |
|---|---|---|
| `test_SA06_valid_token_gives_tenant_and_user` | unit | AC-1 |
| `test_SA06_missing_token_is_401` | unit | AC-2 |
| `test_SA06_non_bearer_header_is_missing_token` (parametrize + ตัวเล็ก) | unit | AC-3 |
| `test_SA06_bad_token_is_401` (parametrize 4 แบบ) | unit | AC-4 |
| `test_SA06_token_without_tenant_or_user_is_401` (parametrize 4 แบบ) | unit | AC-5 |
| `test_SA06_401_hides_details_and_never_logs_the_token` | unit | AC-6 |
| `test_SA06_auth_not_required_lets_anonymous_through` | unit | AC-7 |
| `test_SA06_required_auth_needs_supabase_settings` | unit | AC-8 |
| `test_SA06_every_route_outside_allowlist_needs_a_token` | unit | AC-9 |
| `test_SA06_cors_preflight_is_not_blocked` | unit | AC-10 |
| `test_SA06_openapi_documents_bearer_and_401` | unit | AC-11 |
| `test_AI04_chat_turn_writes_ai_calls_row_for_the_token_user` | unit | AC-12 |
| `test_AI04_anonymous_chat_turn_still_streams_without_a_row` | unit | AC-13 |
| `test_NFRP1_es256_check_fetches_jwks_once` | unit | AC-14 |
| `test_SA06_real_supabase_token_passes_and_tampered_fails` | integration | AC-15 |
| `test_SA06_user_db_client_sees_only_own_tenant` | integration | AC-tenant |

Unit อยู่ใน `apps/api/tests/unit/test_api_auth.py` · integration ใน `apps/api/tests/integration/test_api_auth_db.py`

Test เดิมของห้องติว (`test_room_stubs.py`, `test_room_api_contract.py`, `test_tutor_reply_stream_api.py`, `test_tutor_reply_stream_review.py`) เรียก endpoint โดยไม่มี token และ review แล้ว ห้ามแก้ · จึงให้ `tests/conftest.py` ตั้ง `AUTH_REQUIRED=false` เป็นค่าเริ่มต้นของ test (`os.environ.setdefault` แบบเดียวกับ `AI_PROVIDER=fake`) · test ของ feature นี้เปิด `true` เอง (§10 ข้อ 3)

## 9. Out of scope

- หน้า login และการส่ง token ของหน้าเว็บ (May · §10 ข้อ 1)
- บันทึก `messages` และ `tutor_sessions` จริง (ตั้ง `session_id` ใน `ai_call_context` ทำพร้อมกัน)
- เปิด `AI_PROVIDER=live` บน api-staging: ต้องมี feature นี้ + `AUTH_REQUIRED=true` บน staging + เปลี่ยน runtime SA (`infra/README.md` ⚠️) · เป็นงานแยก
- role `teacher` / `admin` (SA-01) และ organization tenant · quota ต่อ user (§2.10) · rate limit
- refresh token: เป็นหน้าที่ของ client (supabase-js)

## 10. Open questions

1. **(May · หน้าเว็บ)** หน้าเว็บยังไม่มี login และไม่ส่ง `Authorization` · เมื่อไหร่จะมี และใช้แบบไหน (email/password, magic link, หรือ `signInAnonymously` ของ Supabase ให้หน้า demo เข้าได้โดยไม่ต้องสมัคร) · ระหว่างนี้ staging ใช้ `AUTH_REQUIRED=false`
2. **(Jam)** `.env.example` ควรตั้ง `AUTH_REQUIRED=` เป็นอะไร · ข้อเสนอ: `false` พร้อม comment "เปลี่ยนเป็น true เมื่อหน้าเว็บส่ง token" เพราะ May รันเว็บกับ API ในเครื่องโดยไม่มี login · ค่าเริ่มต้นใน code ยังเป็น `true` (production และ CI integration)
3. **(Jam)** test เดิมของห้องติวใช้ `AUTH_REQUIRED=false` ผ่าน `conftest.py` (§8) โอเคไหม · ทางอื่นคือแก้ test เดิมให้ส่ง token ซึ่งห้ามทำเพราะ review แล้ว
4. **(Junior · deploy)** `api-staging` ยังไม่มี `SUPABASE_URL` / `SUPABASE_ANON_KEY` · ใส่เพิ่มใน `infra/env/api-staging.yaml` ได้ไหม (anon key ไม่ใช่ secret ใช้ในหน้าเว็บอยู่แล้ว) · ถ้ายังไม่ใส่ staging จะไม่ตรวจ token เลย (§2.3) · และ `anyang-staging` ต่อไม่ได้ตอน 1 พ.ย. (`/auth/v1/.well-known/jwks.json` ไม่ตอบ · อาจถูก pause)
5. **(Junior · backend)** ใช้ `supabase.auth.get_claims` (ไม่ต้องเพิ่ม dependency · HS256 fallback ไป `get_user`) หรือ verify เองด้วย `pyjwt` + JWKS (ต้องเพิ่ม `pyjwt[crypto]` เป็น dependency ตรง · HS256 ต้องมี JWT secret ของ Supabase ในเครื่อง) · ข้อเสนอ: `get_claims`
6. **(Junior)** `error.code` ของ 401 เป็น `missing_token` / `invalid_token` · เป็นส่วนหนึ่งของรายการ code ที่ api.md "รอตัดสิน" ข้อ 3 ยังเปิดอยู่

## 11. Spec changes needed

- `specs/system/api.md` (ไฟล์กลาง · ต้องถามก่อนแก้ · บอกกลุ่ม) Conventions "Auth": เพิ่มว่า endpoint ที่ไม่มี token หรือ token ผิดตอบ `401` code `missing_token` / `invalid_token` + allowlist (`/health`, `/docs`, `/openapi.json`) + สวิตช์ `AUTH_REQUIRED` ระหว่างที่หน้าเว็บยังไม่ส่ง token
- `.env.example` (ไฟล์กลาง) + `docs/team/setup.md` A5: `AUTH_REQUIRED` · `infra/env/api-staging.yaml` (ไฟล์เสี่ยง): `AUTH_REQUIRED: "false"` (และ §10 ข้อ 4)
- `infra/README.md` ⚠️ "ห้ามเปิด AI_PROVIDER=live …": อัปเดตเงื่อนไขเป็น "จนกว่า staging จะตั้ง `AUTH_REQUIRED=true` (`api-auth.md`)"
