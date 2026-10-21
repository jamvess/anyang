# สร้าง Supabase project `anyang-staging`

| | |
|---|---|
| Owner | Junior |
| Branch | `chore/supabase-staging` |
| Checklist item | สร้าง Supabase project `anyang-staging` |
| Status | in progress · 2026-10-19 |

## Plan

- [x] 1. 🙋 `anyang-staging` สร้างแล้ว: ref `sfapuygntxuelsxsgkay` · region `ap-southeast-1` (Singapore) · org เดียวกับ `anyang-dev` · Junior เป็น Administrator · ตรวจด้วย `npx supabase projects list` 2026-10-21
- [ ] 2. 🙋 + 🤖 Junior รัน `npx supabase link --project-ref sfapuygntxuelsxsgkay` ใน Git Bash (พิมพ์ password เอง) → Claude ตรวจ `supabase/.temp/project-ref` → `npx supabase migration list` + `npx supabase db push --dry-run` · **ถ้า remote มีตารางอยู่แล้วแต่ไม่มี migration history ให้หยุด ห้าม push** (ใช้ `migration repair` หลังตรวจ) → Junior ตอบ ok → `npx supabase db push`
- [ ] 3. 🤖 ตรวจ: `migration list` ต้องเห็น `0001`, `0002` ทั้งฝั่ง Local และ Remote · ตารางมีครบ · CLI ยัง link กับ staging อยู่ ⚠️ กลับไปทำ dev ต้อง `npx supabase link --project-ref mnwwhkbizjioibjvpnxl` ใหม่
- [ ] 3b. 🙋 RLS isolation test กับ staging (`test_rls_isolation.py` อ่าน `SUPABASE_URL` / `SUPABASE_ANON_KEY` / `SUPABASE_SERVICE_ROLE_KEY` จาก env) · ต้องเปิด Custom Access Token hook (ขั้น 4) ก่อน · Junior รันเองเพราะต้องใช้ service role key ของ staging
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
- 2026-10-19 · Jam เป็นคนสร้าง project (ขั้น 1) · Jam เป็นเจ้าของ org ใน Supabase · ขั้นที่เหลือ Junior ทำต่อ
- ~~2026-10-19 · `unlink` หลัง push เสร็จ~~ → 2026-10-21 · (Junior) ไม่ unlink · ปล่อย link กับ staging ไว้ และ re-link `anyang-dev` เมื่อกลับไปทำ dev (Claude เตือนทุกครั้งก่อน `db push`)
- 2026-10-21 · project แรกที่ชื่อ `anyang-staging` (`xztfzskxusykuqtpomrf`, สร้าง 14 ต.ค.) อยู่ `ap-northeast-1` (Tokyo) ไม่ตรงกับการตัดสินใจ 19 ต.ค. · Supabase ย้าย region ไม่ได้ จึงสร้างใหม่ที่ `ap-southeast-1` (Singapore, `sfapuygntxuelsxsgkay`) ให้ใกล้ Cloud Run `asia-southeast1` (กระทบ TTFT ของ P4-lite) · ลบ project Tokyo แล้วโดย Jam ok · หมายเหตุ: `anyang-dev` อยู่ `ap-northeast-2` (Seoul)

## Next step

ขั้น 2: Junior รัน `npx supabase link --project-ref sfapuygntxuelsxsgkay` ใน Git Bash แล้ว Claude ตรวจ `project-ref` → `migration list` → `db push --dry-run`

## Waiting on

ไม่มี

## Notes for next time

- free plan ของ Supabase เปิด project ที่ active ได้ 2 project ต่อเจ้าของ org ถ้าสร้างไม่ได้ ให้เช็คว่า org นั้นมี project อื่นที่ active อยู่ไหม
