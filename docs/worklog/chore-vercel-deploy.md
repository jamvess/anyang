# เชื่อม Vercel กับ repo

| | |
|---|---|
| Owner | May |
| Branch | `chore/vercel-deploy` |
| Checklist item | เชื่อม Vercel กับ repo (root `apps/web`) |
| Status | in progress · 2026-10-14 |

## Plan

- [x] 1. 🤖 เช็คว่า `apps/web` build ผ่านแบบเดียวกับที่ Vercel จะรัน (`pnpm build`, lint, typecheck) และสรุป env ที่ต้องใส่
- [ ] 2. 🙋 Junior (เจ้าของ repo `jamvess/anyang`) ติดตั้ง Vercel GitHub App ให้เข้าถึง repo นี้
- [ ] 3. 🙋 May import repo ใน Vercel: root `apps/web`, ใส่ env `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY` (ค่า staging จาก Junior)
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

## Next step

ขั้น 2: ทัก Junior ให้ติดตั้ง Vercel GitHub App บน repo `jamvess/anyang` และส่งค่า staging ของ Supabase URL + anon key มาให้

## Waiting on

Junior: ติดตั้ง Vercel GitHub App + ค่า env ของ `anyang-staging`

## Notes for next time

- Vercel Hobby + repo ส่วนตัวของคนอื่น: GitHub App ต้องติดตั้งโดยเจ้าของ repo และ Hobby อาจ block deploy จาก commit ของคนที่ไม่ใช่เจ้าของ Vercel account (ดูขั้น 2)
