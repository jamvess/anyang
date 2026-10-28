# วิธีตั้งค่าเครื่องและทำงานคู่ขนาน

อัปเดต 14 ต.ค. 2569 · ใช้แทนฉบับ 12 ต.ค. ซึ่งใช้ WSL กับ Docker ทีมเราไม่ได้ใช้ทั้งสองอย่างแล้ว

**ทีมเราทำงานแบบนี้**

- ใช้ Windows ธรรมดา และใช้ **Git Bash** เป็น terminal หลัก ไม่ใช้ WSL และไม่ใช้ Docker
- ตอน dev ทั้งทีมใช้ database เดียวกันคือ Supabase cloud project **`anyang-dev`**
- เขียนโค้ดด้วย **Claude Code** โดยแต่ละคนใช้บัญชี Pro ของตัวเอง ส่วน **Claude chat** ใช้คุยเรื่อง design หรือถามตอนติด
- **repo บน GitHub เป็นแหล่งความจริงแหล่งเดียว** ดูว่าใครทำอะไรเสร็จได้ที่ `docs/team/sprint-checklists.md` บน `main`

Part A ทำครั้งเดียวต่อเครื่อง ใช้เวลาประมาณ 1.5–2 ชม. ส่วน Part B คือกติกาการทำงานร่วมกัน (ขั้นตอนประจำวันอยู่ใน `daily-workflow.md`)

## สิ่งที่มีอยู่แล้วใน repo (ห้ามทำซ้ำ)

| ส่วน | สถานะ |
|---|---|
| repo `jamvess/anyang` + specs, `CLAUDE.md`, skills | ✅ |
| backend `apps/api` (FastAPI, `/health`, settings) | ✅ |
| frontend `apps/web` (Next.js, `Tex`, `lib/sse.ts`) | ✅ |
| Supabase `anyang-dev`: ทุกตาราง + RLS + custom access token hook | ✅ |
| Supabase `anyang-staging` (ใช้กับ Vercel preview): ทุกตาราง + RLS + custom access token hook | ✅ |
| CI ทั้ง 3 job (`api`, `api-integration`, `web`) เขียว | ✅ |

คนที่ตั้งเครื่องใหม่ทำแค่ **clone แล้วตั้งค่าเครื่องตัวเอง** ห้ามรัน `supabase init`, `supabase link`, `supabase db push`, `create-next-app` หรือ `uv init` ซ้ำ

---

# Part A · ตั้งค่าครั้งเดียว

## A0 · เจ้าของ repo ทำก่อน (บัญชี `jamvess`)

1. **GitHub:** repo `anyang` → Settings → Collaborators → **Add people** → ใส่ username ของ Junior และ May
2. **Supabase:** Dashboard → Organization ที่มี `anyang-dev` → Settings → **Team** → Invite → ใส่อีเมลของทั้งสองคน เลือก role **Developer** (ถ้าเข้าไปแล้วมองไม่เห็น API keys ให้เปลี่ยนเป็น Administrator)
3. ~~แก้ `.github/CODEOWNERS` เป็น username จริง~~ ทำแล้ว 19 ต.ค. (PR #21) · ถ้ามีคนเข้าทีมใหม่ ให้เพิ่ม username ในตาราง GitHub ของ `roles.md` และใน `.github/CODEOWNERS` ใน PR เดียวกัน

> **ห้ามส่ง key ให้กันทางแชท** ให้แต่ละคนเข้า Dashboard แล้วก๊อปเอง (ดู A5) ยกเว้น database password ซึ่ง Dashboard ไม่แสดง ให้บอกกันต่อหน้า

## A1 · บัญชีที่คนใหม่ต้องมี

| บัญชี | ทำอะไร |
|---|---|
| GitHub | สมัคร ส่ง username ให้เจ้าของ repo แล้ว**กดรับคำเชิญ**ในอีเมล หรือที่ github.com/notifications |
| Claude Pro | มีอยู่แล้ว ใช้ได้ทั้ง Claude Code และ chat |
| Supabase | สมัครด้วย**อีเมลเดียวกับที่ถูกเชิญ** แล้วกดรับคำเชิญ |

## A2 · ติดตั้งเครื่องมือ (Windows)

ติดตั้งตามลำดับนี้ Git ต้องมาก่อน เพราะเครื่องมืออื่นต้องใช้

| # | เครื่องมือ | วิธีติดตั้ง | เช็ค (ใน terminal ใหม่) |
|---|---|---|---|
| 1 | Git for Windows | [git-scm.com/downloads/win](https://git-scm.com/downloads/win) ติดตั้งโดยกด Next ตามค่า default จะได้ Git Bash กับ Credential Manager มาด้วย | `git --version` |
| 2 | Node.js **24** LTS | [nodejs.org](https://nodejs.org) เลือกเวอร์ชัน 24 ให้ตรงกับ CI | `node -v` → `v24.x` |
| 3 | pnpm | `npm install -g pnpm@10.34.7` | `pnpm -v` → `10.34.7` |
| 4 | uv + Python 3.12 | ใน **PowerShell**: `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 \| iex"` แล้วเปิด terminal ใหม่ รัน `uv python install 3.12` | `uv --version` |
| 5 | Claude Code | ใน **PowerShell**: `irm https://claude.ai/install.ps1 \| iex` | `claude --version` |
| 6 | VS Code | [code.visualstudio.com](https://code.visualstudio.com) + extensions: Python, Ruff, ESLint, Tailwind CSS IntelliSense, Claude Code | |

- ติดตั้งเสร็จทุกตัวแล้ว **ปิด terminal ทั้งหมดแล้วเปิดใหม่** ถ้าเจอ `not recognized` ให้ดูตารางปัญหาท้ายไฟล์
- **macOS:** ติดตั้ง Git ด้วย `xcode-select --install` · Node จาก nodejs.org · uv ด้วย `curl -LsSf https://astral.sh/uv/install.sh | sh` · Claude Code ด้วย `curl -fsSL https://claude.ai/install.sh | bash`
- **ยังไม่ต้องติดตั้ง:** Supabase CLI (ใช้ผ่าน `npx supabase` และ Junior คนเดียวที่ต้องใช้), Google Cloud CLI (ใช้ใน S2), Docker (ไม่ใช้)

## A3 · ตั้งค่า git (Git Bash)

```bash
git config --global user.name "Firstname Lastname"
git config --global user.email "อีเมลเดียวกับบัญชี GitHub"
git config --global core.longpaths true
git config --global credential.helper manager
git config --global pull.rebase false
```

- `user.email` ต้องตรงกับอีเมลใน GitHub (Settings → Emails) ไม่งั้น GitHub จะไม่นับ commit เป็นของเรา ถ้าตั้งซ่อนอีเมลไว้ ให้ใช้อีเมลแบบ `...@users.noreply.github.com` ที่แสดงในหน้านั้น
- `core.longpaths` แก้ปัญหา path ยาวเกินใน `node_modules` บน Windows
- `pull.rebase false` ทำให้ `git pull` ไม่ถามคำถามที่ชวนงง

## A4 · Clone repo

```bash
mkdir -p ~/projects && cd ~/projects
git clone https://github.com/jamvess/anyang.git
cd anyang
```

ครั้งแรก browser จะเปิดขึ้นมาให้ login GitHub ถ้าขึ้น `Repository not found` แปลว่ายังไม่ได้รับคำเชิญจาก A1

## A5 · ไฟล์ env (ห้าม commit · ห้ามให้ Claude Code อ่าน)

**1) `.env` ที่ root ใช้กับ backend**

```bash
cp .env.example .env
code .env
```

เข้า Supabase Dashboard แล้วเลือก project **`anyang-dev`**

| ตัวแปร | เอาค่ามาจาก |
|---|---|
| `SUPABASE_URL` | ปุ่ม **Connect** → แท็บ Framework → ดูบรรทัด `NEXT_PUBLIC_SUPABASE_URL` ในกล่อง `.env.local` (`https://xxxx.supabase.co`) |
| `SUPABASE_ANON_KEY` | Project Settings → **API Keys** → Publishable key (`sb_publishable_...`) |
| `SUPABASE_SERVICE_ROLE_KEY` | Project Settings → **API Keys** → Secret key (`sb_secret_...`) ⚠️ เทียบเท่ารหัส admin |
| `DATABASE_URL` | ปุ่ม **Connect** → แท็บ Direct → **Session pooler** · แทน `[YOUR-PASSWORD]` ด้วย database password ที่ขอจากเจ้าของ repo ต่อหน้า |
| `NEXT_PUBLIC_SUPABASE_URL` | ใช้ค่าเดียวกับ `SUPABASE_URL` |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | ใช้ค่าเดียวกับ `SUPABASE_ANON_KEY` |
| `CORS_ALLOW_ORIGINS` | ไม่ต้องแก้ ใช้ค่าใน `.env.example` (`http://localhost:3000`) · origin ที่ browser เรียก API ได้ ต้องตรงทุกตัวอักษร คั่นด้วย `,` ห้ามมี `*` หรือ `/` ท้าย · ถ้ารันเว็บที่ port อื่นให้เพิ่มที่นี่ |
| `CORS_ALLOW_ORIGIN_REGEX` | ไม่ต้องแก้ · ให้ Vercel preview ของ project เรา (`anyang-<hash>-anyang4.vercel.app`) เรียก API ได้ · URL branch alias (`anyang-git-…`) เรียกไม่ได้ · ว่าง = ปิด |

บรรทัดอื่น (`AI_PROVIDER=fake`, GCP, Anthropic, Sentry) ปล่อยไว้ตามเดิมก่อน

**เฉพาะคนที่รัน PoC กับ Gemini จริง** (ตอนนี้คือ Jam ใน P3) ให้ใส่ 2 ค่านี้ ส่วนคนอื่นปล่อยว่างไว้ได้ · ไม่ต้องเปลี่ยน `AI_PROVIDER` เพราะ script ของ PoC สร้าง gateway แบบ live เอง · ส่วน test ใช้ fake provider เสมอ

| ตัวแปร | ค่า |
|---|---|
| `GEMINI_API_KEY` | https://aistudio.google.com/apikey → **Create API key** → Copy · ⚠️ ถ้าเป็น free tier Google อาจเอาข้อมูลไปใช้ train ได้ จึงห้ามส่งข้อมูลของ user จริงหรือรูปลายมือของเพื่อนถ้ายังไม่ได้เปิด billing (AI-07) |
| `AI_MODEL_OVERRIDE` | model ที่จะใช้แทน `TODO-...` ใน `config/ai.yaml` เช่น `gemini:gemini-3.8-flash` |

**2) `apps/web/.env.local` ใช้กับ frontend**

```bash
cp .env.example apps/web/.env.local
code apps/web/.env.local
```

ลบบรรทัดอื่นทิ้งให้เหลือแค่ 3 บรรทัดนี้ **ห้ามมี service role key ในไฟล์นี้**

```
NEXT_PUBLIC_SUPABASE_URL=https://xxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=sb_publishable_...
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**3) ตรวจ:** รัน `git status` ถ้าไม่เห็น `.env` หรือ `.env.local` ในรายการ แปลว่าถูกต้อง

## A6 · ติดตั้ง dependency และรันทั้งระบบ

เปิด Git Bash 3 หน้าต่าง

**หน้าต่าง 1 · backend**

```bash
cd ~/projects/anyang/apps/api
uv sync
uv run pytest            # ต้องผ่านทั้งหมด ไม่มี failed และไม่มี skipped
uv run fastapi dev app/main.py
```

`pytest` จะสร้าง user ชั่วคราว (`sa06-*@example.test`) บน `anyang-dev` แล้วลบทิ้งเอง เป็นเรื่องปกติ ถ้าขึ้น `skipped` แปลว่าแอปอ่าน `.env` ไม่ได้ ให้กลับไปเช็ค A5

**หน้าต่าง 2 · frontend**

```bash
cd ~/projects/anyang/apps/web
pnpm install
pnpm test
pnpm dev
```

**หน้าต่าง 3 · เช็คว่าสองฝั่งต่อกันได้** (ตอนที่ backend ยังเปิดอยู่)

```bash
cd ~/projects/anyang/apps/web
pnpm gen:api
git status               # ต้องขึ้นว่า nothing to commit
```

**เช็คลิสต์**

- [ ] `uv run pytest` ผ่านทั้งหมด
- [ ] `pnpm test` ผ่าน
- [ ] `http://localhost:8000/docs` เปิดได้
- [ ] `http://localhost:3000` เปิดได้
- [ ] `pnpm gen:api` แล้ว git ไม่เห็นไฟล์เปลี่ยน

## A7 · Claude Code

```bash
cd ~/projects/anyang
claude
```

- browser จะเปิดให้ login ด้วยบัญชี **Claude Pro ของตัวเอง**
- ถ้าถามว่า trust โฟลเดอร์นี้ไหม ให้ตอบ Yes
- Claude Code จะอ่าน `CLAUDE.md`, `.claude/settings.json` และ skills (`/spec-feature`, `/spec-to-tests`, `/implement-feature`, `/poc-report`) เอง ลองพิมพ์ `/` จะเห็นรายการ skills

**ทดสอบครั้งแรก** ให้พิมพ์ข้อความนี้ (เปลี่ยนชื่อเป็นของตัวเอง)

```
I am May (frontend + UX). Read CLAUDE.md, apps/web/CLAUDE.md and docs/team/sprint-checklists.md.
In Thai, summarize: the project rules you must follow, what is already done, and my remaining
items this sprint. Do not change any files.
```

ถ้าคำตอบถูกต้อง แปลว่า Claude Code อ่าน repo ได้ครบ

## A8 · Claude chat (claude.ai)

บัญชี Pro **แชร์ Project ข้ามบัญชีไม่ได้** (ฟีเจอร์นี้มีเฉพาะแผน Team/Enterprise) ให้แต่ละคนสร้าง Project ของตัวเอง

1. claude.ai → **Projects** → Create project → ตั้งชื่อ `อ่านยัง?`
2. อัปโหลดไฟล์จาก repo เข้า Project knowledge

   | ไฟล์ | ทำไม |
   |---|---|
   | `CLAUDE.md` | กฎของโปรเจกต์ |
   | `specs/system/architecture.md`, `api.md`, `data-model.md`, `glossary.md` | ภาพรวมระบบ |
   | `specs/system/ai-orchestration.md`, `learning-model.md` | AI flows และตัวเลข |
   | `specs/requirements/requirements.md` | requirement ID |
   | `specs/poc/README.md` | PoC ของเทอมนี้ |
   | `docs/team/roles.md`, `sprint-checklists.md`, `setup.md` | หน้าที่ งาน และวิธีทำงาน |

3. ใส่ **Custom instructions** (เปลี่ยนชื่อและบทบาทเป็นของตัวเอง)

   ```
   โปรเจกต์นี้คือ "อ่านยัง?" senior project ของ CPE KMUTT ฉันชื่อ May รับผิดชอบ Frontend + UX
   ตอบเป็นภาษาไทย ใช้ศัพท์เทคนิคเป็นภาษาอังกฤษ ไฟล์ใน Project คือ spec ที่ทีมตกลงกันแล้ว
   ถ้าคำแนะนำขัดกับ spec ให้บอกก่อน งานโค้ดฉันทำด้วย Claude Code ใน repo
   ดังนั้นเมื่อแนะนำให้แก้โค้ด ให้เขียนเป็น prompt ภาษาอังกฤษสำหรับวางใน Claude Code
   ```

**กติกาการใช้ chat**

- chat ใช้คิด, ออกแบบ, อธิบาย error ส่วนการแก้ไฟล์ให้ทำผ่าน Claude Code ใน repo เท่านั้น
- **ถ้าตัดสินใจอะไรใน chat ต้องเอาไปใส่ใน repo** (spec, config หรือ PR description) เพราะ chat ของคนอื่นและ Claude Code มองไม่เห็นบทสนทนาของเรา
- ไฟล์ใน Project จะเก่าลงเรื่อยๆ ให้ทุกวันจันทร์อัปโหลดไฟล์ที่เปลี่ยนบน `main` ใหม่ (ดูได้จาก `git log --since="1 week ago" --name-only -- specs docs CLAUDE.md`)
- ห้ามวาง key, password หรือเนื้อหาไฟล์ `.env` ใน chat

---

# Part B · กติกาการทำงานคู่ขนาน

## B1 · ใครแก้ไฟล์ไหน (กันโค้ดชนกัน)

| โฟลเดอร์ / ไฟล์ | เจ้าของ | คนอื่นแก้ได้ไหม |
|---|---|---|
| `apps/api/`, `supabase/`, `infra/`, `.github/` | Junior | ได้ผ่าน PR แต่ต้องบอกในกลุ่มก่อน |
| `apps/web/` | May | ได้ผ่าน PR แต่ต้องบอกในกลุ่มก่อน |
| `prompts/`, `evals/`, `config/learning.yaml`, `specs/system/ai-orchestration.md`, `learning-model.md` | Jam | ได้ผ่าน PR แต่ต้องบอกในกลุ่มก่อน |
| **ไฟล์กลาง:** `CLAUDE.md`, `specs/requirements/requirements.md`, `specs/system/api.md`, `config/ai.yaml`, `docs/team/*` | ทุกคน | ประกาศในกลุ่มก่อนแก้ และเปิด PR เล็กๆ แยกจากงานอื่น |

**กฎพิเศษ**

- **Migration (`supabase/migrations/`) เป็นของ Junior คนเดียว** ห้ามแก้ไฟล์ที่ merge แล้ว ถ้าต้องเปลี่ยนให้เพิ่มไฟล์ใหม่ เช่น `0002_xxx.sql` หลัง merge Junior เป็นคนรัน `npx supabase db push` ขึ้น `anyang-dev` แล้วประกาศในกลุ่ม คนอื่น**ห้ามรัน `db push`**
- **ใครแก้ API คนนั้นรัน `pnpm gen:api`** ใน PR เดียวกัน เพื่อให้ `apps/web/lib/api-schema.ts` ตรงกับ API เสมอ
- **`specs/system/api.md` คือสัญญาระหว่าง frontend กับ backend** May สร้างหน้าจอตาม spec โดยใช้ข้อมูลปลอมไปก่อนได้ ไม่ต้องรอ endpoint จริง
- **`anyang-dev` ใช้ร่วมกันทั้งทีม** ห้ามลบข้อมูลของคนอื่น และ test ทุกตัวต้องลบข้อมูลที่ตัวเองสร้าง

## B2 · ทำงานประจำวัน

ดูที่ [`daily-workflow.md`](daily-workflow.md) ที่เดียว ทุกวันใช้แค่ 4 คำสั่งใน Claude Code: `/work-start <ชื่อ>` → (`/work-check` หลังทุกขั้น) → `/work-pause` หรือ `/work-done`

ในไฟล์นั้นมีทั้งวิธีดูว่าเพื่อนทำอะไรเสร็จแล้ว, วงจรของ 1 งาน, worklog, การ review PR ของเพื่อน (หัวข้อ D) และคู่มือแบบทำเองถ้าไม่ใช้คำสั่งอัตโนมัติ

## B3 · กฎการใช้ Claude Code ของทีม

1. **1 งาน = 1 session = 1 branch** เมื่อเปลี่ยนงานให้ `/exit` แล้วเปิดใหม่
2. **ให้วางแผนก่อนลงมือ** ถ้างานแตะหลายไฟล์
3. **อ่าน diff ทุกครั้งก่อน commit** ห้าม commit โค้ดที่ตัวเองยังไม่ได้อ่าน
4. **ห้ามให้ Claude แก้ test ที่ review แล้ว** ถ้า test ดูผิด ให้หยุดแล้วคุยในทีม
5. **ห้ามให้ Claude อ่าน `.env`** ถ้ามันขออนุญาตให้กด No (settings บล็อกไว้แล้ว)
6. **ใช้ AI coding tool ตัวเดียว** คือ Claude Code ห้ามติดตั้งตัวอื่นที่แก้ repo พร้อมกัน
7. **กรอกตัวเลขใน PR template** (% โค้ดที่ agent เขียน, จำนวนรอบ red → green) ทีมต้องใช้ตัวเลขนี้ใน Self-Assessment
8. **ถ้า Claude ทำผิดเรื่องเดิมซ้ำ** ให้เพิ่มกฎใน `CLAUDE.md` ผ่าน PR แทนการบอกซ้ำทุกครั้ง
9. **ถ้าเจอ usage limit ของ Pro** ให้สลับไปทำงานที่ไม่ใช้ AI ก่อน เช่น review PR, label ข้อมูล, wireframe

---

## ปัญหาที่พบบ่อย

| อาการ | แก้ |
|---|---|
| `uv` / `claude` / `pnpm` not recognized | ปิด terminal และ VS Code ทั้งหมดแล้วเปิดใหม่ ถ้ายังไม่หาย ให้เช็คว่า `%USERPROFILE%\.local\bin` อยู่ใน PATH |
| clone ขึ้น `Password authentication is not supported` | `git config --global credential.helper manager` แล้ว clone ใหม่ (browser จะเปิดให้ login) |
| clone ขึ้น `Repository not found` | ยังไม่ได้รับคำเชิญ collaborator |
| `uv run pytest` ขึ้น `skipped` | แอปอ่านค่า Supabase ใน `.env` ไม่ได้ ให้เช็คว่าไฟล์อยู่ที่ root และกรอกครบ |
| test ขึ้น `connection refused` หรือ timeout | Supabase free plan จะ **pause project ที่ไม่มีคนใช้ 7 วัน** ให้เข้า Dashboard แล้วกด Restore |
| JWT ไม่มี `tenant_id` | custom access token hook ถูกปิด ให้ไปเปิดที่ Dashboard → Authentication → Hooks |
| RLS ทำให้ query ได้ 0 แถว | backend ไม่ได้ส่ง JWT ของ user ไปกับ request ให้ Supabase |
| `Filename too long` | `git config --global core.longpaths true` |
| `Port 3000/8000 is already in use` | มี dev server ค้างอยู่ในหน้าต่างอื่น ให้กด `Ctrl+C` ในหน้าต่างนั้น |
| `pnpm install` ขึ้น lockfile error ใน CI | อย่าใช้ `npm install` ใน `apps/web` ให้ใช้ `pnpm` เท่านั้น |
| Gemini ตอบ 403 (ตั้งแต่ S2) | รัน `gcloud auth application-default login` แล้วขอสิทธิ์ Vertex AI User จาก Junior |
