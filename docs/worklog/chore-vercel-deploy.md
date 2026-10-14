# เชื่อม Vercel กับ repo

| | |
|---|---|
| Owner | May |
| Branch | `chore/vercel-deploy` |
| Checklist item | เชื่อม Vercel กับ repo (root `apps/web`) |
| Status | in progress · 2026-10-14 |

## Plan

- [ ] 1. 🤖 เช็คว่า `apps/web` build ผ่านแบบเดียวกับที่ Vercel จะรัน (`pnpm build`, lint, typecheck) และสรุป env ที่ต้องใส่
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

## Next step

ขั้น 1: รัน `pnpm build`, `pnpm lint`, `pnpm typecheck` ใน `apps/web`

## Waiting on

ไม่มี

## Notes for next time

- Vercel Hobby + repo ส่วนตัวของคนอื่น: GitHub App ต้องติดตั้งโดยเจ้าของ repo และ Hobby อาจ block deploy จาก commit ของคนที่ไม่ใช่เจ้าของ Vercel account (ดูขั้น 2)
