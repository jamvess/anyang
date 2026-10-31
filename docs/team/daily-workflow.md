# ขั้นตอนทำงานประจำวัน

อัปเดต 14 ต.ค. 2569 · ใช้คู่กับ `setup.md` (ตั้งเครื่องครั้งแรก) และ `sprint-checklists.md` (งานของแต่ละ sprint)

## ⚡ โหมดอัตโนมัติ (ใช้แบบนี้เป็นหลัก)

ใช้ 4 คำสั่งนี้ใน Claude Code แล้ว AI จะพาทำทุกขั้นเอง เราแค่อ่านแล้วตอบ `ok` หรือบอกสิ่งที่ต้องแก้

```bash
cd ~/projects/anyang
claude
```

| คำสั่ง | ใช้ตอน | AI ทำอะไรให้ | เราทำอะไร |
|---|---|---|---|
| `/work-start Junior` (หรือ `May`, `Jam`) | เริ่มทุกครั้ง **ช่วง overlap** (อยู่ในคอลด้วยกัน แต่ละคนทำงานของตัวเองขนานกัน) | pull, อัปเดต library, บอกว่าเพื่อนเสร็จอะไรไปแล้ว, เสนองานให้เลือก, สร้าง branch, worklog, Draft PR และแผนทีละขั้น | เลือกเลขงาน แล้วตอบ `ok` กับแผน |
| `/work-start ALL` | เริ่มทุกครั้ง **ช่วง solo** (ทำคนเดียว เพื่อนอยู่คนละ time zone) | เหมือนข้างบน แต่เสนองานจาก**ทุกคน**ตามความสำคัญ: branch ค้างของตัวเอง → branch ของเพื่อนที่ `/work-pause` ไว้ → ข้อ ⭐ และข้อที่มีคนรอ · ข้ามงานที่ต้องใช้สิทธิ์หรือการตัดสินใจของคนอื่น · จดใน worklog ว่าใครทำต่อ | เลือกเลขงาน · บอกกลุ่มว่าหยิบงานของใคร (มีข้อความร่างให้) |
| (อัตโนมัติหลังแต่ละขั้น) `/work-check` | หลังทำเสร็จทุกขั้น | รัน test, อธิบายว่าทำอะไรไป, บอก **🔍 สิ่งที่ต้องเช็ค** 2–5 ข้อ | เช็คตามที่บอก แล้วตอบ `ok` → AI commit + push และทำขั้นต่อไปเอง |
| `/work-pause` | จะหยุดทั้งที่งานยังไม่เสร็จ | push ทุกอย่าง, เขียนลง worklog ว่าค้างตรงไหนและครั้งหน้าต้องทำอะไร, ร่างข้อความแชทกลุ่มให้ | ก๊อปข้อความไปแปะในกลุ่ม |
| `/work-done` | งานเสร็จแล้ว | ดึง main มารวม, รัน test ทั้งหมด, **อัปเดตเอกสารที่เกี่ยวข้อง**, ติ๊ก `sprint-checklists.md`, เขียน PR description, **self-review ด้วย `/code-review`** แล้วแก้, รอ CI เขียว แล้ว merge | เช็ค 3 ข้อ, ถ้าเป็นงานเสี่ยงบอกกลุ่มก่อน merge, ตอบ ok ให้ merge, ส่งข้อความในกลุ่ม |

**วงจร**

```
/work-start ชื่อ ─▶ เลือกงาน ─▶ ok แผน ─▶ ┌─ AI ทำ 1 ขั้น ─▶ 🔍 เราเช็ค ─▶ ok ─┐
                                         └──────────── วนจนครบ ◀──────────────┘
                                                    │
                          ยังไม่เสร็จแต่จะหยุด ◀─────┴────▶ เสร็จแล้ว
                                 /work-pause                 /work-done
                                                                │
                                  self-review + CI เขียว ─▶ Merge ─▶ /work-start
```

**สิ่งที่ AI ทำเองไม่ได้ (🙋)** AI จะบอกทีละคลิกว่าต้องทำอะไร เช่น กดใน Supabase/GCP Dashboard, ใส่ key ลง `.env`, ถ่ายรูปลายมือ, ตัดสินใจเรื่อง design, กด Merge บน GitHub

**solo กับ overlap** (ทีมตกลง 31 ต.ค.) · ช่วงที่ทำคนเดียวใช้ `/work-start ALL` หยิบงานของใครก็ได้ เพื่อให้งานเดินต่อตอนเจ้าของงานออฟไลน์ · ช่วงที่อยู่ในคอลด้วยกันใช้ชื่อตัวเองตามเดิม · **ก่อนเลิกงานต้อง `/work-pause` เสมอ** เพราะ `/work-start ALL` จะหยิบ branch ของเพื่อนเฉพาะที่ worklog เป็น `paused` · branch ที่ยังเป็น `in progress` ถือว่าเจ้าของกำลังทำอยู่ จะไม่มีใครแตะ

**ไฟล์ worklog** (`docs/worklog/<branch>.md`) เป็นที่ที่ AI จดว่างานถึงไหนแล้ว เพราะ Claude Code จำ session ก่อนไม่ได้ ครั้งหน้าพอพิมพ์ `/work-start` มันจะอ่านไฟล์นี้แล้วทำต่อได้ทันที พอ `/work-done` ไฟล์นี้จะถูกย้ายไปเป็น PR description

**ตั้งครั้งเดียว (แนะนำ):** ติดตั้ง GitHub CLI แล้ว AI จะเปิด PR, รอ CI และ merge ให้เอง (หลังเราตอบ ok) ไม่ต้องเข้าเว็บ

```powershell
winget install --id GitHub.cli -e
```

เปิด Git Bash ใหม่ แล้วรัน `gh auth login` (เลือก GitHub.com → HTTPS → Login with a web browser) ถ้าไม่ติดตั้ง AI จะให้ลิงก์มากดเองแทน

ส่วน A–H ด้านล่างคือขั้นตอนแบบทำเองทีละคำสั่ง ใช้เป็นคู่มืออ้างอิง หรือใช้ตอนที่คำสั่งอัตโนมัติมีปัญหา

---

## คู่มือแบบทำเอง

คำสั่งในกล่องให้วางใน **Git Bash ทีละบรรทัด** ส่วนข้อความภาษาอังกฤษในกล่องให้วางใน **Claude Code**

---

## A · เริ่มวัน (ทุกคน · 5–10 นาที)

**1. เปิด Git Bash แล้วเข้าโฟลเดอร์โปรเจกต์**

```bash
cd ~/projects/anyang
```

**2. ดึงงานล่าสุดของทีมลงมา**

```bash
git switch main
```
```bash
git pull
```

ถ้าขึ้นว่ามีไฟล์ที่ยังไม่ได้ commit ให้ดู "ปัญหาที่เจอบ่อย" ท้ายไฟล์

**3. อัปเดต library** (ถ้าเพื่อนเพิ่ม library ใหม่ เครื่องเราจะได้มีด้วย)

```bash
cd apps/api && uv sync && cd ../..
```
```bash
cd apps/web && pnpm install && cd ../..
```

**4. เปิด Claude Code แล้วถามสถานะทีม**

```bash
claude
```

วาง prompt ของตัวเอง

| คน | prompt |
|---|---|
| Junior | `I am Junior (backend + DevOps). Read docs/team/sprint-checklists.md and run git log --oneline -15. In Thai, tell me what teammates finished recently, what is left for me this sprint, and what I am waiting on. Do not change any files.` |
| May | `I am May (frontend + UX). Read docs/team/sprint-checklists.md and run git log --oneline -15. In Thai, tell me what teammates finished recently, what is left for me this sprint, and what I am waiting on. Do not change any files.` |
| Jam | `I am Jam (AI + evaluation). Read docs/team/sprint-checklists.md and run git log --oneline -15. In Thai, tell me what teammates finished recently, what is left for me this sprint, and what I am waiting on. Do not change any files.` |

**5. เช็ค GitHub** (เปิด `github.com/jamvess/anyang` → แท็บ **Pull requests**)

- ไม่มีใครต้องรอเรา approve แล้ว (ทีมตกลง 31 ต.ค. · ดูหัวข้อ F) · ถ้ามีเวลาค่อยดู PR ที่เพื่อน merge แล้วย้อนหลังตาม **D**
- มี Draft PR ของเพื่อนที่ทำเรื่องเดียวกับเราไหม → ถ้ามี ให้คุยกันก่อน จะได้ไม่ทำซ้ำ

**6. เลือกงาน 1 ชิ้น แล้วบอกในกลุ่ม**

เลือกจากข้อที่ยังไม่ติ๊กใน `sprint-checklists.md` โดยทำข้อที่มี ⭐ ก่อน หรือข้อที่เพื่อนรออยู่ แล้วพิมพ์ในกลุ่มว่า "วันนี้ทำ ___"

ถ้าเมื่อวานทำงานค้างไว้ ให้ไปที่ **C · ทำงานที่ค้างไว้ต่อ**

---

## B · เริ่มงานใหม่ 1 ชิ้น

**1. สร้าง branch** (ร่างของเราเอง)

```bash
git switch -c feat/<ชื่องานสั้นๆ>
```

ขึ้นต้นชื่อตามประเภทงาน: `feat/` ฟีเจอร์, `fix/` แก้บั๊ก, `chore/` setup, `docs/` เอกสาร, `poc/` PoC เช่น `feat/chat-page`, `poc/p1-handwriting`

**2. ถ้ายังไม่แน่ใจว่าจะทำยังไง ให้ถาม Claude chat ก่อน**

เปิดแชทใหม่ใน Project `อ่านยัง?` บอกว่าจะทำงานข้อไหน แล้วขอ prompt สำหรับ Claude Code

**3. สั่ง Claude Code**

- **งานฟีเจอร์:** `/spec-feature` → อ่าน spec → `/spec-to-tests` → **อ่าน test ให้ละเอียด** → `/implement-feature`
- **งาน setup, PoC หรือเอกสาร:** สั่งตรงๆ ได้ ถ้างานแตะหลายไฟล์ให้เพิ่มคำว่า `Plan first, wait for my OK before changing files.`

**4. อ่านสิ่งที่ Claude Code แก้**

ใน VS Code กดไอคอน Source Control ทางซ้าย แล้วกดดูแต่ละไฟล์ หรือพิมพ์ใน Claude Code ว่า `Show me a summary of every change you made.`

ถ้าไม่เข้าใจตรงไหน ให้ก๊อปรายงานของ Claude Code ไปถาม Claude chat

**5. Commit + push** (เซฟแล้วอัปโหลด)

```
Commit the changes with a clear message and push this branch.
```

**6. เปิด Draft PR** (แปะป้ายว่ากำลังทำ)

เปิด GitHub แล้วกดปุ่มเหลือง **Compare & pull request** → กดลูกศรข้างปุ่มสีเขียว → **Create draft pull request**

ทำข้อนี้**ทันทีที่ push ครั้งแรก** แม้งานยังไม่เสร็จ เพื่อนจะได้รู้ว่าเรากำลังทำเรื่องนี้อยู่

**7. ทำต่อไปเรื่อยๆ** วนข้อ 3 → 4 → 5 ได้ไม่จำกัด ทุกครั้งที่ push งานจะไปอยู่ใน Draft PR เดิม ส่วนตอนเลิกงานให้ไปที่ **E · ก่อนเลิกงาน**

**8. งานเสร็จแล้ว** ให้ไปที่ **F · ส่งงานให้เพื่อนตรวจ**

---

## C · ทำงานที่ค้างไว้ต่อ

**1. กลับไปที่ branch ของงานนั้น**

```bash
git branch
```

คำสั่งนี้แสดงรายชื่อ branch ทั้งหมดในเครื่อง ให้หาชื่องานของเรา แล้วรัน

```bash
git switch feat/<ชื่องาน>
```

**2. ดึงของใหม่จาก main มารวม** (ถ้าเพื่อน merge อะไรเข้าไปตั้งแต่เมื่อวาน)

```bash
git pull origin main
```

ถ้าขึ้น **CONFLICT** ให้ดู "ปัญหาที่เจอบ่อย"

**3. เปิด Claude Code แล้วเล่าให้มันฟังว่าทำถึงไหน** (session ใหม่จะจำงานของเมื่อวานไม่ได้)

```
We are continuing the work on this branch. Read the diff against main
(git diff main...HEAD) and the PR description, then summarize in Thai
what is done and what is left. Do not change any files yet.
```

ทำต่อจาก **B ข้อ 3**

---

## D · ดู PR ของเพื่อนย้อนหลัง (ไม่บังคับ)

ตั้งแต่ 31 ต.ค. ไม่ต้อง approve ก่อน merge แล้ว เพราะเราอยู่คนละ time zone และการรอ review ทำให้งานติด · หัวข้อนี้ใช้เมื่อมีเวลาและอยากดูงานของเพื่อนหลัง merge · ถ้าเจอปัญหาให้เปิด PR แก้ หรือบอกในกลุ่ม

**1.** เปิด GitHub → PR ของเพื่อน (แท็บ **Closed** ถ้า merge แล้ว) → แท็บ **Files changed**

**2. ให้ Claude Code ช่วยดู**

```bash
git fetch
```
```bash
git switch <ชื่อ branch ของเพื่อน>
```

```
Review this branch against main using CLAUDE.md rules. List only real problems,
with file and line, in Thai. Do not change any files.
```

**3. อ่านเองด้วย** โดยเฉพาะไฟล์ test เพราะ test เป็นตัวกำหนดว่าโค้ดต้องทำอะไร

**4. ถ้าเจอปัญหา:** เขียน comment ใน PR (ใช้ได้แม้ merge แล้ว) แล้วบอกเจ้าของในกลุ่ม · ถ้าแก้เองได้ให้เปิด PR ใหม่แก้เลย

**5. กลับมาที่งานของตัวเอง**

```bash
git switch main
```

---

## E · ก่อนเลิกงาน (ทุกคน · 5 นาที)

**1. Push งานที่ทำไว้ทั้งหมด** แม้ยังไม่เสร็จ คอมจะได้ไม่ใช่ที่เดียวที่มีงานเรา

```
Commit what we have so far with a "wip:" message and push.
```

**2. เขียนสถานะลงใน Draft PR** เพิ่มคอมเมนต์ใน PR 2–3 บรรทัด: วันนี้ทำอะไรไปแล้ว ติดอะไร พรุ่งนี้จะทำอะไรต่อ พรุ่งนี้เราจะได้รู้ว่าค้างตรงไหน และเพื่อนก็เห็นด้วย

**3. ถ้าติดเกิน 1 วัน ให้บอกในกลุ่ม** ว่าติดอะไรและรอใครอยู่

**4. ถ้าวันนี้ตัดสินใจอะไรใน chat** ให้เอาไปเขียนลง repo (spec, config หรือ PR description) ก่อนปิดเครื่อง

**5. ปิด dev server** ด้วย `Ctrl+C` ในทุกหน้าต่างที่เปิดค้างไว้ และพิมพ์ `/exit` ใน Claude Code

---

## F · ส่งงานและ merge เอง

**1. ดึงงานล่าสุดของเพื่อนมารวม**

```bash
git pull origin main
```

**2. รัน test ให้ผ่าน**

```
Run all lint and tests for the parts I changed and fix anything that fails.
Do not change tests that were already reviewed.
```

**3. ติ๊กเช็คลิสต์** เปิด `docs/team/sprint-checklists.md` แก้ `[ ]` เป็น `[x]` ในข้อที่ทำเสร็จ

**4. Commit + push รอบสุดท้าย**

```
Commit and push. Then write the PR description from .github/pull_request_template.md
so I can paste it on GitHub.
```

**5. Self-review**

```
Run /code-review high on this branch. Fix the real findings (never change tests
that were already reviewed) and write a "Self-review" section for the PR description.
```

**6. บน GitHub**
- วาง description ลงใน PR (รวมหัวข้อ Self-review)
- กด **Ready for review** (ไม่ต้องเลือก reviewer)
- **ถ้าเป็นงานเสี่ยง** ให้บอกในกลุ่ม **ก่อน merge**: migration หรือ RLS, ไฟล์กลาง (`CLAUDE.md`, `requirements.md`, `api.md`, `config/*.yaml`, `.env.example`), `infra/`, `.github/`

**7. Merge** เมื่อ CI ขึ้นติ๊กเขียวครบทุกตัว
- ruleset `main` บังคับแค่ CI `api`, `api-integration`, `web` ต้องผ่าน · ไม่ต้องมี approve (เปลี่ยนจาก 1 คนเมื่อ 31 ต.ค. · ทีมตกลง) · ยังห้าม push ตรงเข้า `main` และห้าม force push
- กด **Merge pull request** แล้วกด **Delete branch**
- บอกในกลุ่มว่า "merge ___ แล้ว · ใครว่างดูย้อนหลังได้"
- กลับไปทำ **A ข้อ 2** เพื่อดึง main ล่าสุด

---

## G · สิ่งที่แต่ละคนต้องทำเพิ่ม

### Junior · Backend + DevOps

| เมื่อไหร่ | ทำอะไร |
|---|---|
| ทุกเช้า | เช็คว่า CI บน `main` ยังเขียวอยู่ (GitHub → แท็บ **Actions**) ถ้าแดง ให้แก้ก่อนงานอื่น เพราะทุกคนได้รับผล |
| หลัง merge PR ที่มี migration ใหม่ | `npx supabase db push` ขึ้น `anyang-dev` แล้วบอกในกลุ่ม **มีแค่ Junior ที่รัน db push** |
| แก้ API (เพิ่มหรือเปลี่ยน endpoint) | เปิด backend ทิ้งไว้แล้วรัน `cd apps/web && pnpm gen:api` ใน PR เดียวกัน |
| ทุกวันศุกร์ | เช็คว่า `anyang-dev` ไม่ถูก pause (free plan จะ pause project ที่ไม่มีคนใช้ 7 วัน) |

### May · Frontend + UX

| เมื่อไหร่ | ทำอะไร |
|---|---|
| ก่อนสร้างหน้าจอใหม่ | อ่าน `specs/system/api.md` ว่าหน้านั้นใช้ข้อมูลอะไร ถ้า endpoint ยังไม่มี ให้ใช้ข้อมูลปลอมไปก่อน ไม่ต้องรอ Junior |
| ทุกครั้งที่ทดสอบหน้าเว็บ | เปิด backend (`cd apps/api && uv run fastapi dev app/main.py`) คู่กับ `pnpm dev` |
| เปลี่ยน flow หรือหน้าจอที่ไม่ตรงกับ wireframe | บอกในกลุ่มก่อน แล้วอัปเดต wireframe ด้วย |
| ก่อน push | ให้ Claude Code รัน `pnpm lint`, `pnpm typecheck`, `pnpm test` ให้ผ่าน |

### Jam · AI + การวัดผล

| เมื่อไหร่ | ทำอะไร |
|---|---|
| เปลี่ยนตัวเลขใน `config/learning.yaml` | ใส่ที่มาของตัวเลข ([A]/[B]/[calc]/[C]) ทุกครั้ง และบอกในกลุ่ม เพราะกระทบ logic ของ Junior |
| แก้ prompt ใน `prompts/` | สร้างเวอร์ชันใหม่ (`v2.md`) ห้ามแก้ทับเวอร์ชันเดิม แล้วรัน eval เทียบกับเวอร์ชันเก่า |
| ได้ข้อมูล PoC ใหม่ (รูปลายมือ, label) | เก็บใน `evals/` ตามรูปแบบใน `evals/README.md` ส่วนข้อมูลดิบให้ไว้ใน `evals/**/raw/` ซึ่งไม่ถูก commit |
| ได้ผล PoC แล้ว | `/poc-report <ID>` แล้วเปิด PR |

---

## H · ประจำสัปดาห์

| วัน | ใคร | ทำอะไร |
|---|---|---|
| จันทร์ | ทุกคน | อัปโหลดไฟล์ที่เปลี่ยนบน `main` เข้า Claude chat Project ของตัวเอง ดูรายการไฟล์ได้จาก `git log --since="1 week ago" --name-only --format= -- specs docs CLAUDE.md` |
| จันทร์ | ทุกคน | คุยกัน 15 นาที: งานของ sprint นี้ ใครทำอะไร ใครรอใคร |
| ศุกร์ | ทุกคน | Demo ของ sprint (ทุก 2 สัปดาห์) แล้วเช็คว่า `sprint-checklists.md` ติ๊กตรงกับงานที่เสร็จจริง |

---

## ปัญหาที่เจอบ่อย

| อาการ | แก้ |
|---|---|
| `git pull` ขึ้นว่า `Your local changes would be overwritten` | มีงานที่ยังไม่ได้ commit ให้สั่ง Claude Code `Commit these changes on a new branch` หรือถ้าไม่ต้องการแล้ว รัน `git restore .` (**งานที่ยังไม่ได้ commit จะหายถาวร**) |
| `CONFLICT` ตอน `git pull origin main` | สั่ง Claude Code `Resolve the merge conflicts. Explain each conflict and which side you kept.` แล้วอ่านทุกจุด ถ้าเป็นไฟล์ของเพื่อน ให้ถามเจ้าของไฟล์ก่อน |
| CI ขึ้นกากบาทแดง ❌ | กดที่ ❌ → Details → ก๊อป error ไปให้ Claude Code: `CI failed with this error: <วาง error>. Find the cause and fix it.` |
| ลืมสร้าง branch แล้วแก้บน `main` ไปแล้ว | ยังไม่ commit: `git switch -c feat/<ชื่องาน>` งานที่แก้จะย้ายมาที่ branch ใหม่ให้เอง · ถ้า commit ไปแล้ว: ถาม Claude chat |
| วางคำสั่งแล้วขึ้น `[200~` | กด `Ctrl+C` แล้ววางใหม่ทีละบรรทัด |
| Claude Code ขึ้น `Login expired` | `/exit` → `claude` → `/login` |
| เจอ usage limit ของ Pro | ทำงานที่ไม่ใช้ AI ระหว่างรอ: review PR, label ข้อมูล, wireframe, อ่าน spec |
| `pnpm gen:api` ขึ้น `ECONNREFUSED :8000` | ยังไม่ได้เปิด backend ให้เปิด `uv run fastapi dev app/main.py` ในอีกหน้าต่างก่อน |
| test ขึ้น `skipped` หรือต่อ Supabase ไม่ได้ | เช็ค `.env` หรือดูว่า `anyang-dev` ถูก pause ไหม (Dashboard → Restore) |
| ดิสก์เต็ม (`ENOSPC`) | ลบไฟล์ชั่วคราวของ Windows แล้วรัน `npm cache clean --force` กับ `uv cache clean` |
