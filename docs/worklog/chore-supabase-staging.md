# สร้าง Supabase project `anyang-staging`

| | |
|---|---|
| Owner | Junior |
| Branch | `chore/supabase-staging` |
| Checklist item | สร้าง Supabase project `anyang-staging` |
| Status | in progress · 2026-10-19 |

## Plan

- [x] 1. 🙋 `anyang-staging` สร้างแล้ว: ref `sfapuygntxuelsxsgkay` · region `ap-southeast-1` (Singapore) · org เดียวกับ `anyang-dev` · Junior เป็น Administrator · ตรวจด้วย `npx supabase projects list` 2026-10-21
- [x] 2. 🙋 + 🤖 Junior รัน `npx supabase link --project-ref sfapuygntxuelsxsgkay` ใน Git Bash (พิมพ์ password เอง) → Claude ตรวจ `supabase/.temp/project-ref` → `npx supabase migration list` + `npx supabase db push --dry-run` · **ถ้า remote มีตารางอยู่แล้วแต่ไม่มี migration history ให้หยุด ห้าม push** (ใช้ `migration repair` หลังตรวจ) → Junior ตอบ ok → `npx supabase db push`
- [x] 3. 🤖 ตรวจแล้ว 2026-10-21: history ตรงกัน `0001`, `0002` · ตารางใน `public` 27 ตัว (เท่ากับ `create table` ใน 0001) RLS เปิดครบ 27 · มี `messages.attachment_name` และ function `custom_access_token_hook` · ก่อน push ไม่มีตาราง/function/user เลย (ไม่ต้อง `migration repair`) · link ไม่ต้องถาม password · `npx supabase unlink` แล้ว (`supabase/.temp/project-ref` ถูกลบ) · กลับไปทำ dev ต้อง `npx supabase link --project-ref mnwwhkbizjioibjvpnxl` ใหม่
- [x] 3b. 🙋 RLS isolation test กับ staging ผ่าน 2026-10-21: `test_SA06_tenant_isolation` 3 passed (`exam_preps`, `attempts`, `messages`) · Junior รันเองใน Git Bash ด้วย env vars ของ staging (`test_rls_isolation.py` อ่าน `SUPABASE_URL` / `SUPABASE_ANON_KEY` / `SUPABASE_SERVICE_ROLE_KEY`)
- [x] 4. 🙋 เปิด Custom Access Token hook (`public.custom_access_token_hook`) ใน Dashboard ของ staging แล้ว 2026-10-21 · RLS ครบ 27 ตาราง (ตรวจด้วย query ในขั้น 3)
- [x] 5. 🙋 ตั้ง Auth URL ของ staging แล้ว 2026-10-21: Site URL เปลี่ยนจากค่า default `http://localhost:3000` เป็น `https://anyang-amber.vercel.app` (`anyang-dev` ยังเป็น `http://localhost:3000` เพราะใช้ local อย่างเดียว) · Redirect URLs: `http://localhost:3000/**` และ `https://anyang-*-anyang4.vercel.app/**`
- [ ] 6. 🙋 Jam (เจ้าของ Vercel · ทีมยืนยัน 21 ต.ค.) (ก) เปลี่ยน env ของ **Preview** (`NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`) ให้ชี้ `anyang-staging` แล้ว redeploy · architecture.md: staging = Vercel preview · (ข) ตรวจ env ของ **Production**: README เดิมเขียนว่า Production + Preview ชี้ `anyang-staging` ซึ่งตอนนั้นคือ project Tokyo `xztfzskxusykuqtpomrf` ที่ลบไปแล้ว ถ้ายังชี้ตัวนั้น `anyang-amber.vercel.app` จะพัง (demo 30 ต.ค. น่าจะใช้ URL นี้) · เสนอชี้ `anyang-staging` ตัวใหม่จนกว่าจะมี `anyang-prod` · `infra/README.md` เขียนว่า "Env (Production + Preview) … ชี้ `anyang-staging`" ซึ่งไม่ตรงกับนี้ ต้องแก้ในขั้น 7
- [x] 7. 🤖 อัปเดต docs 2026-10-21: `infra/README.md` (staging ทำแล้ว 21 ต.ค. + ref + region + Redirect URLs · Env แยก Preview → staging / Production ยังไม่แตะ · เพิ่ม `unlink` ในขั้นตอน) · `setup.md` ตาราง "สิ่งที่มีอยู่แล้วใน repo" · checklist D3: ERD 27 ตาราง (+ `auth.users`) · `setup.md` ไม่มีบรรทัดไหนบอกว่า Vercel เป็นของ May จึงไม่ต้องแก้

## Definition of done

- มี Supabase project `anyang-staging` ใน org เดียวกับ `anyang-dev`
- `0001_init.sql` ขึ้น staging แล้ว (`migration list` ตรงกันทั้งสองฝั่ง) · ทุกตารางเปิด RLS · Custom Access Token hook เปิดแล้ว
- Vercel ชี้ `anyang-staging` (หรือจดไว้ใน Waiting on ว่ารอ Jam)
- `infra/README.md` และ `setup.md` ตรงกับที่ตั้งจริง · ติ๊ก checklist ข้อนี้

## Decisions

- 2026-10-19 · region Singapore · ให้อยู่ใกล้ Cloud Run `asia-southeast1` ที่จะใช้ทำ `api-staging`
- 2026-10-19 · Jam เป็นคนสร้าง project (ขั้น 1) · Jam เป็นเจ้าของ org ใน Supabase · ขั้นที่เหลือ Junior ทำต่อ
- 2026-10-19 · `unlink` หลัง push เสร็จ · ถ้าลืมว่ายัง link อยู่ `db push` ครั้งหน้าต้อง fail ให้เห็น ไม่ใช่ push ลง staging เงียบๆ (ยืนยันอีกครั้ง 2026-10-21)
- 2026-10-21 · project แรกที่ชื่อ `anyang-staging` (`xztfzskxusykuqtpomrf`, สร้าง 14 ต.ค.) อยู่ `ap-northeast-1` (Tokyo) ไม่ตรงกับการตัดสินใจ 19 ต.ค. · Supabase ย้าย region ไม่ได้ จึงสร้างใหม่ที่ `ap-southeast-1` (Singapore, `sfapuygntxuelsxsgkay`) ให้ใกล้ Cloud Run `asia-southeast1` (กระทบ TTFT ของ P4-lite) · ลบ project Tokyo แล้วโดย Jam ok · หมายเหตุ: `anyang-dev` อยู่ `ap-northeast-2` (Seoul)
- 2026-10-21 · Vercel เป็นของ Jam (ทีมยืนยัน) ไม่ใช่ May · ขั้น 6 จึงเป็นของ Jam
- 2026-10-21 · Redirect URLs ของ staging ใช้ glob `https://anyang-*-anyang4.vercel.app/**` · glob ของ Supabase ห้าม `-` แบบ CORS regex (`[a-z0-9]+`) ไม่ได้ จึงหลวมกว่า (เช่น `anyang-x-other-anyang4` ก็ผ่าน) · ยอมได้สำหรับ staging เพราะไม่มีข้อมูล user จริง · ต้องทบทวนตอนทำ `anyang-prod`

## Next step

`/work-done` · ขั้น 6 รอ Jam (ดู Waiting on)

## Waiting on

Jam (ขั้น 6 · Junior ถามแล้ว 21 ต.ค.): (ก) เปลี่ยน Vercel **Preview** env ให้ชี้ `anyang-staging` (ข) ตรวจ **Production** env ว่ายังชี้ project Tokyo ที่ลบแล้ว (`xztfzskxusykuqtpomrf`) ไหม ถ้าใช่ต้องเปลี่ยนก่อน demo 30 ต.ค.

## Notes for next time

- free plan ของ Supabase เปิด project ที่ active ได้ 2 project ต่อเจ้าของ org ถ้าสร้างไม่ได้ ให้เช็คว่า org นั้นมี project อื่นที่ active อยู่ไหม
