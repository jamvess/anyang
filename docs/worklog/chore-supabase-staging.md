# สร้าง Supabase project `anyang-staging`

| | |
|---|---|
| Owner | Junior |
| Branch | `chore/supabase-staging` |
| Checklist item | สร้าง Supabase project `anyang-staging` |
| Status | in progress · 2026-10-19 |

## Plan

- [ ] 1. 🙋 สร้าง project `anyang-staging` ใน Supabase Dashboard (org เดียวกับ `anyang-dev`, region Southeast Asia (Singapore) ให้ตรงกับ Cloud Run `asia-southeast1`) · เก็บ database password ไว้ใน password manager · บอก Project ref ให้ Claude
- [ ] 2. 🙋 + 🤖 `npx supabase login` (Junior login ใน browser) → `npx supabase link --project-ref <ref>` (Junior พิมพ์ password เอง) → Claude รัน `npx supabase db push --dry-run` ให้ดูก่อน → Junior ตอบ ok → `npx supabase db push`
- [ ] 3. 🤖 ตรวจ: `npx supabase migration list` ต้องเห็น `0001` ทั้งฝั่ง Local และ Remote · จากนั้น `npx supabase unlink` กัน `db push` ครั้งหน้าไปลง staging โดยไม่ตั้งใจ
- [ ] 4. 🙋 ตรวจ RLS ใน Dashboard (Table Editor ทุกตารางต้องไม่มีป้าย "RLS disabled") + เปิด Custom Access Token hook (`public.custom_access_token_hook`)
- [ ] 5. 🙋 ตั้ง Auth URL: Site URL = `https://anyang-amber.vercel.app` (ค่าเดียวกับ `anyang-dev` ถ้า dev ตั้งไว้ต่างจากนี้ ให้ใช้ตาม dev)
- [ ] 6. 🙋 Jam เปลี่ยน env ของ Vercel (`NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`) ให้ชี้ `anyang-staging` แล้ว redeploy · `infra/README.md` บอกว่าชี้ staging แล้ว แต่ตอนนั้น staging ยังไม่มี จึงน่าจะยังชี้ `anyang-dev` อยู่
- [ ] 7. 🤖 อัปเดต docs: `infra/README.md` (staging ทำแล้ววันไหน, Project ref, region) และ `setup.md` ตาราง "สิ่งที่มีอยู่แล้วใน repo"

## Definition of done

- มี Supabase project `anyang-staging` ใน org เดียวกับ `anyang-dev`
- `0001_init.sql` ขึ้น staging แล้ว (`migration list` ตรงกันทั้งสองฝั่ง) · ทุกตารางเปิด RLS · Custom Access Token hook เปิดแล้ว
- Vercel ชี้ `anyang-staging` (หรือจดไว้ใน Waiting on ว่ารอ Jam)
- `infra/README.md` และ `setup.md` ตรงกับที่ตั้งจริง · ติ๊ก checklist ข้อนี้

## Decisions

- 2026-10-19 · region Singapore · ให้อยู่ใกล้ Cloud Run `asia-southeast1` ที่จะใช้ทำ `api-staging`
- 2026-10-19 · `unlink` หลัง push เสร็จ · เครื่องนี้ไม่ได้ link กับ project ไหนอยู่ก่อน ถ้าปล่อย link ไว้ `db push` ครั้งหน้าจะลง staging

## Next step

ขั้น 1: Junior สร้าง project `anyang-staging` ใน Dashboard แล้วบอก Project ref

## Waiting on

ไม่มี

## Notes for next time

- free plan ของ Supabase เปิด project ที่ active ได้ 2 project ต่อเจ้าของ org ถ้าสร้างไม่ได้ ให้เช็คว่า org นั้นมี project อื่นที่ active อยู่ไหม
