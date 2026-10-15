# เชื่อม Vercel กับ repo

| | |
|---|---|
| Owner | May |
| Branch | `chore/vercel-deploy` |
| Checklist item | เชื่อม Vercel กับ repo (root `apps/web`) |
| Status | in progress · 2026-10-15 |

## Plan

- [x] 1. 🤖 เช็คว่า `apps/web` build ผ่านแบบเดียวกับที่ Vercel จะรัน (`pnpm build`, lint, typecheck) และสรุป env ที่ต้องใส่
- [x] 2. 🙋 Junior (เจ้าของ repo `jamvess/anyang`) ติดตั้ง Vercel GitHub App ให้เข้าถึง repo นี้
- [x] 3. 🙋 May import repo ใน Vercel: root `apps/web`, ใส่ env `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY` (ค่า staging จาก Junior)
- [x] 4. 🙋 May ขออนุญาต Junior ในแชทกลุ่ม: เพิ่ม `.github/workflows/web-deploy.yml` และแก้ `infra/README.md` (Junior เป็นเจ้าของทั้งสองที่)
- [x] 5. 🤖 เขียน `.github/workflows/web-deploy.yml` (Vercel CLI: preview ทุก PR, production เมื่อ push `main`) + `apps/web/vercel.json` ปิด Git auto-deploy ของ Vercel
- [x] 6. 🙋 Jam (`jamvess`) สร้าง Vercel token และใส่ GitHub Secrets `VERCEL_TOKEN`, `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID`
- [x] 7. 🙋 เช็คว่า PR #5 ได้ preview URL จาก workflow และไม่มี check ของ Vercel ที่ fail อีก
- [x] 8. 🤖 บันทึก URL และขั้นตอนลง `infra/README.md` + ติ๊ก checklist ใน `sprint-checklists.md`

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
- 2026-10-14 · `jamvess` = Jam (เจ้าของ repo) · ยืนยันจาก `roles.md` ที่แก้ใน PR #6
- 2026-10-14 · deploy ผ่าน GitHub Actions + Vercel CLI แทน Git integration · Hobby block commit ของคนที่ไม่ใช่เจ้าของ account, ทางนี้ฟรีและทุกคน deploy ได้ (ใช้ token ของ Jam)
- 2026-10-15 · step Deploy ย้าย `.git` ออกชั่วคราว (`mv` ไป `$RUNNER_TEMP` แล้ว `trap` คืน) · Jam ยืนยันว่า deployment ขึ้น **Blocked** เพราะ CLI ส่ง commit author ไปด้วย ซ่อน `.git` แล้ว CLI ไม่มี git metadata จะส่ง · ใช้ `mv` แทน `rm -rf` เพราะ post-job cleanup ของ `actions/checkout` ยังใช้ `.git`
- 2026-10-15 · ใส่ `timeout-minutes: 15` ให้ job `deploy` · deployment ที่ถูก block ทำให้ CLI รอจนครบ 6 ชม.
- 2026-10-14 · เพิ่ม `apps/web/vercel.json` (`git.deploymentEnabled: false`) แทนการตั้งใน dashboard · เห็นใน code review และไม่ deploy ซ้ำกับ workflow (เปลี่ยนจาก decision แรกที่ไม่เพิ่ม `vercel.json`)

## Done today (2026-10-15)

- ขั้น 8: เพิ่มหัวข้อ "Frontend · Vercel" ใน `infra/README.md` (URL, วิธีทำงาน, ตั้งค่าครั้งเดียว, ข้อควรรู้) + ติ๊ก "เชื่อม Vercel กับ repo" ใน `sprint-checklists.md`
- ขั้น 7: run 38677768121 เขียว 1m08s · `✓ Ready in 6s` · preview https://anyang-fshojwlvv-anyang4.vercel.app · Jam กด View deployment ใน PR #5 แล้วเห็นหน้าเว็บ

- ขั้น 7: run 38542548369 ค้าง `Building…` 6 ชม. จน GitHub ตัด · ลิงก์ Inspect เปิดด้วย account ของ May ได้ 404 (ไม่ได้อยู่ใน team `anyang4`) · Jam เปิดแล้วเห็น **Blocked** · แก้ `web-deploy.yml` ให้ซ่อน `.git` ตอน deploy + `timeout-minutes: 15`

## Done 2026-10-14

- ขั้น 7 ติด: re-run `web-deploy` (run 38538233366) · pull + build ผ่าน, upload สำเร็จ, Vercel สร้าง deployment https://anyang-1cwn5kdz7-anyang4.vercel.app (Inspect: https://vercel.com/anyang4/anyang/AMF6hYHS1AX1D4MiTjf31oF2avJy) แต่ CLI ค้างที่ `Building…` 17 นาที จึง cancel
- ขั้น 6: Jam ใส่ secret `VERCEL_TOKEN`, `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID` แล้ว (เห็นใน `gh secret list`)
- ขั้น 5: เขียน `.github/workflows/web-deploy.yml` (Vercel CLI 64.0.2: pull → build → deploy --prebuilt, preview/production ตาม event) + `apps/web/vercel.json` ปิด Git deploy · actionlint ผ่าน
- ขั้น 4: Junior อนุญาตในแชทกลุ่มให้แก้ `.github/workflows/` และ `infra/README.md`

- ขั้น 1: `pnpm build`, lint, typecheck, test ของ `apps/web` ผ่าน · env ที่ต้องใช้มีแค่ 2 ตัว
- สร้าง draft PR #5 (ตอน start ครั้งแรกยังไม่ได้สร้าง)
- ขั้น 2–3: Vercel project `anyang` อยู่ใน account GitHub `jamvess` · root `apps/web` · env ชี้ `anyang-staging` · production https://anyang-amber.vercel.app เปิดได้
- ขั้น 4 ติด: Vercel check ของ PR #5 (commit `5d8e0a6`) **fail** ด้วยข้อความ `Git author jantarat32443 must have access to the project on Vercel to create deployments.` เพราะ Vercel Hobby ยอม deploy เฉพาะ commit ของเจ้าของ account

## Next step

ครบทุกขั้นแล้ว · รัน `/work-done` เพื่อเปลี่ยน PR #5 จาก draft เป็น ready for review

## Waiting on

ไม่มี

## Notes for next time

- GitHub accounts (ยืนยันจาก `roles.md`): `jamvess` = Jam (เจ้าของ repo), `jnmonsicha2000` = Junior, `jantarat32443` = May
- ค่า Supabase ใน `apps/web/.env.local` ของ May เป็น project บน cloud (ไม่ใช่ localhost) ไม่ได้ใช้ใน Vercel · ใช้ `anyang-staging` ซึ่งยังไม่มีตาราง (รอ Junior รัน migration) แต่หน้าแรกยังไม่อ่าน DB
- ปุ่ม Adjust GitHub App Permissions ใน Vercel ช่วยไม่ได้ ถ้า repo อยู่ใน account ส่วนตัวของคนอื่น
- ใช้ `!` ใน Claude Code แล้วจะรันด้วย bash (ใช้ `rm` ไม่ใช่ `del`)
- เช็ค branch ก่อนเขียนไฟล์เสมอ · มีครั้งหนึ่งที่ repo ถูกสลับไป `main` ระหว่าง session

- Vercel Hobby + repo ส่วนตัวของคนอื่น: GitHub App ต้องติดตั้งโดยเจ้าของ repo และ Hobby อาจ block deploy จาก commit ของคนที่ไม่ใช่เจ้าของ Vercel account (ดูขั้น 2)
- ลิงก์ Inspect ของ team `anyang4` เปิดได้เฉพาะ account ของ Jam (Hobby มีสมาชิกคนเดียว) · account ของ May ได้ 404
- Vercel team slug คือ `anyang4` · preview URL ถูกป้องกันด้วย Vercel Authentication (curl ได้ 302 ไป SSO) เช็คสถานะจากภายนอกไม่ได้ ต้องเปิด Inspect ด้วย account ที่มีสิทธิ์
- ดู log ของ job ได้ด้วย `gh run view --job=<id> --log` (ใช้ได้หลัง job จบแล้วเท่านั้น) · re-run ด้วย `gh run rerun <run-id>`
- ตรวจ workflow ได้ด้วย `uvx --from actionlint-py actionlint .github/workflows/*.yml`
