# วิธีตั้งค่าโปรเจกต์ (AI-first ด้วย Claude Code)

อัปเดต 12 ต.ค. 2569 · ทำตามลำดับ §1 → §6 ใช้เวลาประมาณ 2–3 ชม. ต่อคน (§4–§5 Junior ทำครั้งเดียว)

**แนวคิด:** เราให้ Claude Code เป็นคนเขียนโค้ดส่วนใหญ่ แต่ทุกอย่างที่ Claude Code ทำต้องอ้างอิง `CLAUDE.md` และ `specs/` ของ repo ดังนั้นสิ่งแรกที่ต้องทำคือวาง starter files (โฟลเดอร์นี้) ลง repo ก่อนเริ่มเขียนโค้ด

---

## 1. บัญชีที่ต้องมี

| บัญชี | ใครสร้าง | ใช้ทำอะไร | หมายเหตุ |
|---|---|---|---|
| GitHub organization + repo `anyang` | Junior | โค้ด, PR, CI | เพิ่มทุกคนเป็น member |
| Claude (Pro, Max หรือ Team) หรือ Anthropic Console | ทุกคน | ใช้ Claude Code | แผน free ใช้ Claude Code ไม่ได้ ตกลงกันในทีมว่าใช้แบบไหน |
| Google Cloud project `anyang` + billing / credit | Junior | Cloud Run, Vertex AI (Gemini), STT/TTS | ให้ Jam สิทธิ์ Vertex AI User |
| Supabase: project `anyang-staging` | Junior | DB, Auth, Storage บน cloud | local ใช้ Docker ไม่ต้องมีบัญชี |
| Vercel | May | deploy frontend | import จาก GitHub repo |
| Anthropic Console API key | Jam | provider สำรอง (Claude) ใน gateway | แยกจาก subscription ของ Claude Code |
| Sentry | Junior | error tracking | free tier พอ |
| Figma | May | hi-fi (เทอม 2) | |

## 2. เครื่องมือบนเครื่อง (ทุกคน)

แนะนำ macOS หรือ Linux ถ้าใช้ Windows ให้ใช้ **WSL 2** แล้วทำทุกอย่างใน WSL

| เครื่องมือ | เวอร์ชัน | ติดตั้ง | เช็ค |
|---|---|---|---|
| Git | ล่าสุด | macOS: มากับ Xcode CLT · WSL: `sudo apt install git` | `git --version` |
| Node.js | 22 LTS | [nodejs.org](https://nodejs.org) หรือ nvm | `node -v` |
| pnpm | ล่าสุด | `corepack enable` | `pnpm -v` |
| uv (Python) | ล่าสุด | `curl -LsSf https://astral.sh/uv/install.sh \| sh` แล้ว `uv python install 3.12` | `uv --version` |
| Docker | Docker Desktop หรือ OrbStack (macOS) | จากเว็บผู้ผลิต | `docker ps` |
| Supabase CLI | ล่าสุด | ใช้ผ่าน `npx supabase ...` (ต้องการ Node 20+) หรือติดตั้ง global ผ่าน Homebrew / Scoop | `npx supabase --version` |
| Google Cloud CLI | ล่าสุด | [cloud.google.com/sdk](https://cloud.google.com/sdk/docs/install) | `gcloud --version` |
| VS Code | ล่าสุด | + extensions: Python, Ruff, ESLint, Tailwind CSS, Claude Code | |

## 3. ติดตั้ง Claude Code

```bash
# macOS, Linux, WSL
curl -fsSL https://claude.ai/install.sh | bash

# ตรวจ
claude --version
claude doctor
```

จากนั้นเข้าโฟลเดอร์ repo แล้วรัน `claude` ระบบจะเปิด browser ให้ login ด้วยบัญชี Claude (Pro/Max/Team) หรือ Console

สิ่งที่ Claude Code อ่านจาก repo นี้โดยอัตโนมัติ

| ไฟล์ | หน้าที่ |
|---|---|
| `CLAUDE.md` (root และใน `apps/*`) | กฎของโปรเจกต์ที่ต้องทำตามทุกครั้ง |
| `.claude/settings.json` | คำสั่งที่อนุญาตให้รันได้ไม่ต้องถาม และไฟล์ที่ห้ามอ่าน (`.env`) |
| `.claude/skills/*/SKILL.md` | คำสั่ง `/spec-feature`, `/spec-to-tests`, `/implement-feature`, `/poc-report` |

## 4. สร้าง repo และโครงโปรเจกต์ (Junior ทำครั้งเดียว)

### 4.1 วาง starter files

```bash
git clone git@github.com:<org>/anyang.git && cd anyang
# copy ทุกอย่างจากโฟลเดอร์ anyang-starter มาไว้ที่ root ของ repo (รวม .claude, .github, .gitignore)
git add . && git commit -m "chore: add specs, CLAUDE.md and project config" && git push
```

ตั้ง branch protection ของ `main`: ต้องผ่าน PR, review 1 คน, CI ผ่าน

### 4.2 ให้ Claude Code สร้างโครงโค้ด

รัน `claude` ที่ root ของ repo แล้วพิมพ์ทีละข้อ ตรวจผลก่อนไปข้อถัดไป

**Prompt 1 · backend**

```
Read CLAUDE.md and apps/api/CLAUDE.md. Scaffold apps/api with uv:
- uv init --app, Python 3.12
- dependencies: fastapi[standard], sse-starlette, pydantic-settings, pyyaml, supabase, sympy, google-genai, anthropic
- dev dependencies: pytest, pytest-asyncio, httpx, ruff
- create the folder layout from apps/api/CLAUDE.md with empty modules
- app/settings.py loads env vars and config/learning.yaml + config/ai.yaml into typed settings
- a /health endpoint and one test for it
- a Dockerfile for Cloud Run (port from $PORT)
Do not implement features yet. Run the tests and ruff, then show me the tree.
```

**Prompt 2 · frontend**

```
Read CLAUDE.md and apps/web/CLAUDE.md. Scaffold apps/web with pnpm create next-app
(TypeScript, Tailwind, ESLint, App Router). Add katex, @supabase/supabase-js, @supabase/ssr,
vitest and @testing-library/react. Create the folder layout from apps/web/CLAUDE.md,
a Tex component with one test, lib/sse.ts (POST + ReadableStream reader) with one test,
and scripts: dev, build, lint, typecheck, test, gen:api. Do not build screens yet.
```

**Prompt 3 · database**

```
Run `npx supabase init` (keep supabase/migrations/0001_init.sql), enable the custom access
token hook in supabase/config.toml for public.custom_access_token_hook, then start Supabase
and reset the database. Write apps/api/tests/integration/test_rls_isolation.py named
test_SA06_tenant_isolation that signs up two users and proves user A cannot read or write
user B's exam_preps, attempts and messages. Run it.
```

ส่วน hook ใน `supabase/config.toml` ต้องเป็นแบบนี้

```toml
[auth.hook.custom_access_token]
enabled = true
uri = "pg-functions://postgres/public/custom_access_token_hook"
```

**Prompt 4 · CI**

```
Check .github/workflows/ci.yml against the scaffolded apps and fix any command that does
not exist yet. Open a PR "chore: scaffold apps" with the PR template filled in.
```

## 5. Cloud (Junior ทำครั้งเดียว ใน S1–S2 เป็นส่วนหนึ่งของ PoC P6-lite)

```bash
gcloud auth login
gcloud config set project <PROJECT_ID>
gcloud services enable run.googleapis.com cloudbuild.googleapis.com \
  artifactregistry.googleapis.com secretmanager.googleapis.com aiplatform.googleapis.com
gcloud artifacts repositories create anyang --repository-format=docker --location=asia-southeast1

# secrets (ค่าจริงใส่ผ่าน stdin ไม่พิมพ์ลง history)
printf '%s' "<service-role-key>" | gcloud secrets create supabase-service-role --data-file=-
printf '%s' "<anthropic-key>"    | gcloud secrets create anthropic-api-key --data-file=-
```

- สร้าง Cloud Build trigger: push เข้า `main` → ใช้ `infra/cloudbuild.yaml`
- ให้ service account ของ Cloud Build มีสิทธิ์ deploy Cloud Run และอ่าน secrets
- Supabase cloud: `npx supabase login` → `npx supabase link --project-ref <ref>` → `npx supabase db push` แล้วเปิด Custom Access Token hook ใน Dashboard (Authentication → Hooks)
- Vercel (May): import repo, root directory `apps/web`, ใส่ env `NEXT_PUBLIC_*`

ใช้ Gemini บนเครื่องตัวเองตอน dev: `gcloud auth application-default login` (ไม่ต้องดาวน์โหลด key file)

## 6. ทุกคน: รันบนเครื่องตัวเอง

```bash
git clone git@github.com:<org>/anyang.git && cd anyang
cp .env.example .env                      # เติมค่าจาก `npx supabase status`
cp .env.example apps/web/.env.local       # ใช้เฉพาะ NEXT_PUBLIC_*

npx supabase start && npx supabase db reset
cd apps/api && uv sync && uv run pytest && uv run fastapi dev app/main.py   # :8000/docs
cd apps/web && pnpm install && pnpm test --run && pnpm dev                  # :3000
```

**เช็คว่าพร้อมแล้ว**

- [ ] `claude doctor` ไม่มี error
- [ ] `http://localhost:8000/docs` เปิดได้
- [ ] `http://localhost:3000` เปิดได้
- [ ] `uv run pytest` และ `pnpm test --run` ผ่าน
- [ ] เปิด PR ทดลองแล้ว CI รันครบ

---

## 7. ทำงานประจำวันกับ Claude Code

### วงจรของ 1 งาน

```
git switch -c feat/<area>-<feature>
claude
> /spec-feature scope/compute-importance SM-03     # หรือแก้ spec ที่มีอยู่
   → คน review spec
> /spec-to-tests specs/features/scope/compute-importance.md
   → คน review test (สำคัญที่สุด) แล้ว commit test ก่อน
> /implement-feature specs/features/scope/compute-importance.md
   → อ่าน diff ทุกไฟล์ก่อน commit
git push → เปิด PR → teammate review → merge → staging อัปเดตเอง
```

### กฎการใช้ Claude Code ของทีม

1. **1 งาน = 1 session = 1 branch** เริ่ม session ใหม่เมื่อเปลี่ยนงาน จะได้ไม่ปน context
2. **ให้วางแผนก่อนลงมือ** สำหรับงานที่แตะหลายไฟล์ ให้ Claude อธิบายแผนก่อน แล้วค่อยให้แก้
3. **อ่าน diff ทุกครั้ง** ก่อน commit ห้าม commit โค้ดที่ไม่ได้อ่าน
4. **ห้ามให้ Claude แก้ test ที่ review แล้ว** ถ้า test ดูผิด ให้หยุดแล้วคุยกันในทีม
5. **ห้ามใส่ secret ในแชท** หรือในไฟล์ที่ commit (settings บล็อกการอ่าน `.env` ไว้แล้ว)
6. **เก็บตัวเลขให้ Self-Assessment:** ใน PR template กรอก % โค้ดที่ agent เขียนและจำนวนรอบ red → green
7. **ถ้า Claude ทำผิดซ้ำเรื่องเดิม** ให้เพิ่มกฎใน `CLAUDE.md` ผ่าน PR แทนการบอกซ้ำทุกครั้ง
8. **PoC** ใช้ `/poc-report P1` เขียน report จากผลที่วัดได้

### ปัญหาที่พบบ่อย

| อาการ | แก้ |
|---|---|
| `claude` not found หลังติดตั้ง | เปิด terminal ใหม่ หรือดู `claude doctor` |
| `supabase start` ค้าง | เปิด Docker ก่อน, ครั้งแรกต้องโหลด image นาน |
| JWT ไม่มี `tenant_id` | ยังไม่ได้เปิด custom access token hook (§4.2 หรือ Dashboard) |
| RLS ทำให้ query ได้ 0 แถว | backend ไม่ได้ส่ง JWT ของ user ต่อให้ Supabase |
| Gemini ตอบ 403 บนเครื่อง | รัน `gcloud auth application-default login` และขอสิทธิ์ Vertex AI User จาก Junior |
