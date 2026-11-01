# Architecture (v1.2)

v1.2 (2026-11-01 · D2): ตรวจกับที่ตั้งจริงแล้ว · ที่มาของแต่ละข้ออยู่ใน `infra/README.md`, `config/ai.yaml`, `.github/workflows/` และ report PoC ใน `specs/poc/reports/` · ของที่ยังไม่สร้างเขียนว่า **แผน** และสถานะรวมอยู่ในหัวข้อ "สร้างแล้วหรือยัง" ด้านล่าง

## ภาพรวม 3 ชั้น

เส้นประ (ทั้งเส้นเชื่อมและกรอบ) = ยังเป็นแผน

```mermaid
flowchart TB
  U[ผู้เรียน · browser] <-->|HTTPS| W
  subgraph Vercel
    W[Next.js · TypeScript · Tailwind · KaTeX]
  end
  W <-->|REST + SSE · Bearer JWT| A
  subgraph Cloud Run · asia-southeast1
    A[FastAPI · ตรวจ JWT] --> D[domain: checker]
    A -.-> DP[domain: stars · bkt · planner · stage machine · buddy · spacing]
    A --> S[services: checker · tutor turn]
    A -.-> SP[services: ingestion · scope edit]
    S --> G[AI gateway: routing · retry · circuit breaker · log]
    G -.-> GP[answer-leak check · fallback]
    S --> M[SymPy service · worker pool + timeout]
  end
  G -->|primary · ADC| V[Gemini · Vertex AI]
  G -.->|fallback · แผน| C[Claude API]
  G -.->|แผน · เทอม 2| T[Google Cloud STT / TTS]
  G --> L[(ai_calls + Cloud Logging)]
  A <--> DB[(Supabase · PostgreSQL + pgvector · RLS)]
  A -.->|แผน| ST[(Supabase Storage)]
  A -->|ตรวจ JWT · JWKS| AU
  W <--> AU[Supabase Auth · Google login แผน · UM-02]

  classDef plan stroke-dasharray: 5 5
  class DP,SP,GP,C,T,ST plan
```

- **AI gateway** (`apps/api/app/ai/gateway.py`) เลือก provider จาก prefix ของ model id ใน `config/ai.yaml`:
  - `vertex:` คือ Gemini บน Vertex AI ใช้ ADC ไม่มี key file (`specs/features/ai/gemini-vertex.md`)
  - `gemini:` คือ Gemini API key ใช้ตอน dev หรือ `AI_MODEL_OVERRIDE`
  - `AI_PROVIDER=fake` ใช้ใน test และบน `api-staging` ตอนนี้
  - provider ของ Claude และ Mathpix ยังไม่มีในโค้ด · ใน `ai.yaml` ยังเป็น `TODO`
- **Auth** (`specs/features/platform/api-auth.md`): หน้าเว็บส่ง access token ของ Supabase · API ตรวจด้วย JWKS ของ Supabase Auth ได้ `tenant_id` + `user_id` แล้วส่ง JWT ต่อให้ Supabase เพื่อให้ RLS ทำงาน
  - `AUTH_REQUIRED=false` ให้ request ที่ไม่มี token ผ่านได้ ระหว่างที่หน้าเว็บยังไม่ login (token ที่ผิดยังได้ 401)
  - **`api-staging` ตอนนี้ไม่ตรวจ token เลย** เพราะไม่มี `SUPABASE_URL` / `SUPABASE_ANON_KEY` (api.md Conventions) · token ปลอมก็ผ่านโดยไม่มี tenant · เส้น "ตรวจ JWT" ในแผนภาพจึงยังไม่จริงบน staging
- **Log ของ AI** (`specs/features/ai/ai-calls-log.md`): ทุก call เขียน log JSON (logger `app.ai.calls` → Cloud Logging) · call ที่มี tenant บันทึกลงตาราง `ai_calls` ด้วย service role **เฉพาะเมื่อมี `SUPABASE_SERVICE_ROLE_KEY`** · `api-staging` ยังไม่มี secret และไม่มี tenant จึงยังไม่มีแถวใน `ai_calls` มีแค่ log ใน Cloud Logging

## Tech stack (ตกลงแล้ว)

| ชั้น | เลือก | เหตุผลสั้นๆ |
|---|---|---|
| Frontend | Next.js (App Router) + TypeScript + Tailwind + KaTeX · PWA เป็นแผน (ยังไม่มี manifest) | ทีมคุ้น, deploy ง่ายบน Vercel, KaTeX render สมการเร็ว |
| Hosting frontend | Vercel (Hobby, team `anyang4`) · deploy ด้วย Vercel CLI จาก GitHub Actions | Hobby ยอม Git deploy เฉพาะ commit ของเจ้าของ account (`infra/README.md` "Frontend · Vercel") |
| Backend | FastAPI + Pydantic + `sse-starlette` | Python ใช้ SymPy และ AI SDK ได้ตรง, Pydantic ตรวจ structured output |
| Hosting backend | Google Cloud Run (Docker, Artifact Registry `anyang`) · project `anyang-513006` (Free Trial) · Secret Manager เปิดแล้วแต่ยังไม่มี secret | scale ถึง 0 ได้, ใช้ GCP credit, อยู่ใกล้ Vertex AI |
| Streaming | SSE | ทิศทางเดียว server → client พอสำหรับแชท ง่ายกว่า WebSocket บน Cloud Run |
| Database | Supabase: PostgreSQL + pgvector + Auth + Storage + RLS · region Singapore | DB, vector, auth, file อยู่ที่เดียว RLS แยก tenant ที่ระดับ DB |
| LLM | `gemini-3.5-flash` บน Vertex AI ทุก tier ข้อความ (P2, P3, P4-lite) · Claude API เป็น fallback (แผน) | สลับได้ผ่าน `config/ai.yaml` · ใช้ Vertex เพราะ credit ของ trial ไม่ครอบคลุม API key ของ AI Studio |
| Vision / OCR | `gemini-3.5-flash-lite` (P1: line accuracy 95.2% · วัดผ่าน AI Studio API `gemini:` ยังไม่ได้วัดซ้ำบน `vertex:` ที่ `ai.yaml` ใช้) · Mathpix เป็น fallback ที่ยังไม่ได้ทดสอบ | |
| Embedding | `gemini-embedding-2` 768 มิติ (P3b: recall@4 19/20) | |
| Voice | Google Cloud STT / TTS (เทอม 2) | |
| Math | SymPy ใน worker process ที่เปิดค้างไว้ (`checker.sympy_workers`) + timeout จาก config | ตัดสินถูกผิดแบบ deterministic · worker ที่เปิดค้างไว้ไม่ต้องเสีย cold start ~1.9 วินาทีทุกครั้ง (`sympy-service.md`) |
| Retrieval | เขียนเอง (`topic_chunks` + pgvector) ไม่ใช้ LangChain | test ง่าย ควบคุม prompt ได้ |
| CI/CD | GitHub Actions `ci` (job `api`, `api-integration`, `web`) + `web-deploy` (Vercel) · Cloud Build trigger `api-staging-deploy` (backend) | |
| Observability | `ai_calls` table + Cloud Logging (JSON) · Sentry เป็นแผน (มีแค่ setting `SENTRY_DSN` ยังไม่ได้ต่อ) | |
| Dev tools | uv, Ruff, pytest, pnpm, ESLint, Prettier, Vitest, Figma, Claude Code | |

## Environments

| Env | Frontend | Backend | Database | ใช้ทำอะไร |
|---|---|---|---|---|
| local | `pnpm dev` | `uv run fastapi dev` | Supabase cloud `anyang-dev` (ทั้งทีมใช้ร่วมกัน · `docs/team/setup.md`) · `supabase start` (Docker) เป็นทางเลือกสำหรับลอง migration ก่อน `db push` (setup.md ไม่ให้ทุกคนลง Docker) | พัฒนา, test |
| CI | — | pytest ใน GitHub Actions | `supabase start` ใน job `api-integration` (ใส่ migration ทุกไฟล์ใหม่ทุกครั้ง) | test รวม RLS isolation |
| staging | Vercel production `https://anyang-amber.vercel.app` + preview ต่อ PR | Cloud Run `api-staging` (`asia-southeast1`, min 0 / max 2 instance) · `AI_PROVIDER=fake`, `AUTH_REQUIRED=false` (`infra/env/api-staging.yaml`) | Supabase `anyang-staging` (`sfapuygntxuelsxsgkay`) | demo, PoC, Alpha |
| prod | แผน · เทอม 2 | แผน · Cloud Run `api-prod` | แผน · Supabase `anyang-prod` | Beta, Pilot |

ยังไม่มี Vercel domain แยกสำหรับ staging · production ของ Vercel ชี้ไปที่ `api-staging` และ `anyang-staging` (`infra/README.md`)

**Deploy**
- **backend:** push เข้า `main` ที่แก้ `apps/api/**`, `config/**`, `prompts/**` หรือ `infra/**` → trigger `api-staging-deploy` ของ Cloud Build → build image → deploy `api-staging` (P6-lite: 3.40–4.58 นาที)
  - trigger ไม่ได้รอ GitHub Actions · ที่กันของพังคือกฎของ `main` (ruleset) ที่ต้องให้ `api`, `api-integration`, `web` ผ่านก่อน merge
  - กันได้ไม่หมด: ruleset ไม่บังคับให้ branch ตาม `main` ล่าสุด (`strict` = false) · 2 PR ที่ผ่าน CI แยกกันอาจพังเมื่อรวมกัน แล้ว deploy ทันที · `ci` ที่รันบน `main` จะแจ้งหลัง deploy
  - ทางสำรองคือ `infra/deploy-staging.ps1`
- **frontend:** PR ที่แก้ `apps/web/**` → workflow `web-deploy` สร้าง preview · push เข้า `main` → deploy production
- **prod:** แผนคือกด promote (เทอม 2)
- **migration:** Junior รัน `npx supabase db push` ขึ้น `anyang-dev` และ `anyang-staging` หลัง merge · CI ไม่ได้ push ให้ · 1 พ.ย. `anyang-staging` มี `0001` + `0002` (`infra/README.md`) · `0003` (PR #67) รอ Junior push

## สร้างแล้วหรือยัง (2026-11-01)

| ส่วน | สถานะ | ที่มา |
|---|---|---|
| AI gateway: `ai.call`, `ai.stream`, routing, retry, log `ai_calls`, circuit breaker ต่อ provider | สร้างแล้ว · **answer-leak check และ fallback ยังไม่มี** (`gateway.py`) · breaker เปิดแล้วล้มทันทีแล้ว degrade | `ai-calls-log.md`, `gemini-vertex.md`, `gateway-guards.md` |
| Rate limit ข้อความในห้องติว (`guards.rate_limit_messages_per_minute`) | สร้างแล้ว · นับในหน่วยความจำต่อ instance · ไม่มี token นับต่อ IP (ปลอมได้ · ห้ามเปิด live ขณะ `AUTH_REQUIRED=false`) | `gateway-guards.md` |
| ตรวจ JWT ทุก endpoint | สร้างแล้ว · `api-staging` ยังไม่ตรวจเลย (ไม่มี `SUPABASE_URL` / `SUPABASE_ANON_KEY`) รอหน้าเว็บ login | `api-auth.md` |
| ห้องติว: ข้อความ text stream จาก gateway | สร้างแล้ว (P4-lite) · ยังไม่บันทึก `messages` · endpoint อื่นของห้องเป็น stub (`X-Stub: true`) | `tutor-reply-stream.md` |
| หน้าตรวจขอบเขต | stub 3 endpoint (api.md v1.6) | PR #100 |
| ตรวจคำตอบ: SymPy service + merge rules + classifier | สร้างแล้ว ยังไม่ต่อเข้าห้องแชท | `sympy-service.md`, `check-answer-classifier.md` |
| `domain/`: stars, bkt, planner, stage machine, buddy, spacing | แผน · มีแค่ `checker.py` · `compute_importance` ทำใน P8-lite (S4) | `compute-importance.md` |
| ingestion (classify → อ่าน PDF → สกัดหัวข้อ → ดาว) | แผน · มีแค่โค้ดของ PoC ใน `poc/P3/` | P3.md |
| Upload ไฟล์และรูปขึ้น Storage | แผน | api.md "Exam prep และ scope", "ห้องติว" |
| หน้าเว็บ login (Google · UM-02) | แผน · ต้องตั้ง Google provider + redirect URL ใน Supabase Auth | requirements.md UM-02 |
| STT / TTS, Sentry, PWA, prod | แผน | |

## Multi-tenant

Target user ของ v1 คือนักเรียนรายคน แต่ data architecture เป็น multi-tenant ตั้งแต่แรก นักเรียนแต่ละคนเป็น personal tenant และ schema รองรับ organization tenant (สถาบัน → สาขา → ห้อง) โดยไม่ต้อง migrate รายละเอียดใน `data-model.md` และ ai-orchestration §3.4 · infrastructure เป็น pool model (ทุก tenant ใช้ Cloud Run และ Supabase ร่วมกัน แยกด้วย RLS)

## โครงสร้างโค้ด

ดู `apps/api/CLAUDE.md` และ `apps/web/CLAUDE.md`
