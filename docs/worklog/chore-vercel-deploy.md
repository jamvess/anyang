# เชื่อม Vercel กับ repo

| | |
|---|---|
| Owner | May |
| Branch | `chore/vercel-deploy` |
| Checklist item | เชื่อม Vercel กับ repo (root `apps/web`) |
| Status | paused · 2026-10-14 |

## Plan

- [x] 1. 🤖 เช็คว่า `apps/web` build ผ่านแบบเดียวกับที่ Vercel จะรัน (`pnpm build`, lint, typecheck) และสรุป env ที่ต้องใส่
- [x] 2. 🙋 Junior (เจ้าของ repo `jamvess/anyang`) ติดตั้ง Vercel GitHub App ให้เข้าถึง repo นี้
- [x] 3. 🙋 May import repo ใน Vercel: root `apps/web`, ใส่ env `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY` (ค่า staging จาก Junior)
- [ ] 4. 🙋 เปิด production URL ดูว่าหน้าแรกขึ้น และเช็คว่า draft PR นี้ได้ preview URL
- [ ] 5. 🤖 บันทึก URL และขั้นตอนลง `infra/README.md` + ติ๊ก checklist ใน `sprint-checklists.md`

## Definition of done

- Vercel project เชื่อม `jamvess/anyang` แล้ว root directory = `apps/web`
- push เข้า `main` → production deploy อัตโนมัติ, เปิด PR → ได้ preview URL
- หน้าแรกของ production URL เปิดได้
- URL และวิธีตั้งค่าอยู่ใน repo

## Decisions

- 2026-10-14 · ยังไม่เพิ่ม `vercel.json` · Vercel ตรวจ Next.js + pnpm จาก `apps/web` เองได้ ค่อยเพิ่มถ้าจำเป็น
- 2026-10-14 · ตอนนี้ใส่ env แค่ 2 ตัว (`NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`) · โค้ดใน `apps/web` อ่านแค่ 2 ตัวนี้ (`lib/supabase.ts`) ส่วน `NEXT_PUBLIC_API_URL` ค่อยใส่เมื่อมี `api-staging` บน Cloud Run
- 2026-10-14 · ไม่ต้องตั้ง Node version ใน Vercel เอง · `package.json` มี `engines.node: >=24` และ `packageManager: pnpm@10.34.7` อยู่แล้ว Vercel อ่านจากตรงนี้
- 2026-10-14 · env บน Vercel ชี้ไปที่ Supabase `anyang-staging` · `NEXT_PUBLIC_SUPABASE_URL` ต้องไม่มี `/rest/v1/` ต่อท้าย และใช้ publishable key (`sb_publishable_...`) เป็น `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- 2026-10-14 · production URL: https://anyang-amber.vercel.app (เช็คแล้วได้ 200, title "อ่านยัง?")

## Done today (2026-10-14)

- ขั้น 1: `pnpm build`, lint, typecheck, test ของ `apps/web` ผ่าน · env ที่ต้องใช้มีแค่ 2 ตัว
- สร้าง draft PR #5 (ตอน start ครั้งแรกยังไม่ได้สร้าง)
- ขั้น 2–3: Vercel project `anyang` อยู่ใน account GitHub `jamvess` · root `apps/web` · env ชี้ `anyang-staging` · production https://anyang-amber.vercel.app เปิดได้
- ขั้น 4 ติด: Vercel check ของ PR #5 (commit `5d8e0a6`) **fail** ด้วยข้อความ `Git author jantarat32443 must have access to the project on Vercel to create deployments.` เพราะ Vercel Hobby ยอม deploy เฉพาะ commit ของเจ้าของ account

## Next step

ถาม May 2 ข้อแล้วทำตามคำตอบ:
1. GitHub `jamvess` เป็นของใคร (May บอกว่า Jam แต่ชื่อจริงใน `roles.md` ชี้ว่าน่าจะเป็น Junior เวสสภู ส่วน `jnmonsicha2000` น่าจะเป็น Jam มนสิชา) คนนี้ต้องเป็นคนสร้าง Vercel token และใส่ GitHub Secrets
2. เลือกทางแก้ Vercel: (1 แนะนำ) deploy ผ่าน GitHub Actions + Vercel CLI · (2) Vercel Pro แล้วเชิญเข้า team · (3) เปลี่ยน repo เป็น public · (4) ยอมรับไปก่อน

ถ้าเลือก 1: เพิ่มขั้นในแผน → 🤖 เขียน `.github/workflows/web-deploy.yml` (preview ทุก PR, production เมื่อ push `main`) หลังได้รับอนุญาตจาก Junior (เจ้าของ `.github/`) → 🙋 เจ้าของ `jamvess` ใส่ secret `VERCEL_TOKEN`, `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID` → ปิด Git auto-deploy ของ Vercel เพื่อไม่ให้ deploy ซ้ำ

## Waiting on

May: คำตอบ 2 ข้อข้างบน

## Notes for next time

- GitHub accounts ตามที่ May บอก: `jamvess` = Jam, `jnmonsicha2000` = Junior, `jantarat32443` = May (ยังไม่ยืนยัน เพราะขัดกับชื่อจริงใน `roles.md`)
- ค่า Supabase ใน `apps/web/.env.local` ของ May เป็น project บน cloud (ไม่ใช่ localhost) ไม่ได้ใช้ใน Vercel · ใช้ `anyang-staging` ซึ่งยังไม่มีตาราง (รอ Junior รัน migration) แต่หน้าแรกยังไม่อ่าน DB
- ปุ่ม Adjust GitHub App Permissions ใน Vercel ช่วยไม่ได้ ถ้า repo อยู่ใน account ส่วนตัวของคนอื่น
- ใช้ `!` ใน Claude Code แล้วจะรันด้วย bash (ใช้ `rm` ไม่ใช่ `del`)
- เช็ค branch ก่อนเขียนไฟล์เสมอ · มีครั้งหนึ่งที่ repo ถูกสลับไป `main` ระหว่าง session

- Vercel Hobby + repo ส่วนตัวของคนอื่น: GitHub App ต้องติดตั้งโดยเจ้าของ repo และ Hobby อาจ block deploy จาก commit ของคนที่ไม่ใช่เจ้าของ Vercel account (ดูขั้น 2)
