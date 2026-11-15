# หน้า login + ส่ง token ทุก request (demo ขั้น 1 ฝั่งเว็บ)

| | |
|---|---|
| Owner | Jam (item of May · May ให้ทำได้เลย แล้วมา review ทีหลัง · 15 พ.ย.) |
| Branch | `feat/web-login` |
| Checklist item | ⭐ demo ขั้น 1: หน้า login (email + password ตาม D1) · เก็บ session · ส่ง `Authorization` ทุก request (UM-01) |
| Status | in progress · 2026-11-15 |

## Plan

API ฝั่ง token พร้อมแล้ว (#134: `anyang-dev` ออก token ที่มี `tenant_id` · `AUTH_REQUIRED=true` ตอบ 401 เมื่อไม่มี token) แต่หน้าเว็บยังไม่มีหน้า login และทุก request (`TutorRoom`, `ScopeReview`, `httpTransport`, `postSSE`) ยังไม่ส่ง `Authorization` · journey ที่ใช้ข้อมูลจริงจึงติดตั้งแต่หน้าแรก

- [x] 1. 🤖 (15 พ.ย. · Jam ok) `/spec-feature` → `specs/features/platform/web-login.md`: หน้า `/login` (email + password · `supabase.auth.signInWithPassword` · บัญชีใน `anyang-dev` ตาม D1) · login ผ่าน → ไปหน้าที่มาจาก (`?next=`) หรือ `/` · ผิด → ข้อความไทย · ทุก request ไป API แนบ `Authorization: Bearer <access_token>` จาก session ของ Supabase (ที่เดียว · `lib/`) · API ตอบ 401 → พาไปหน้า login พร้อม `next` · ไม่มี session + `AUTH_REQUIRED=false` (เครื่อง dev) → ไม่แนบ header ทำงานกับ stub แบบเดิม · ปุ่มออกจากระบบ · ไม่มีหน้าสมัคร (UM-01 สมัครเอง · S5) · 🙋 Jam review spec
- [x] 2. 🤖 (15 พ.ย. · Jam ok) `/spec-to-tests` (Vitest + Testing Library · Supabase client ปลอม) · 🙋 Jam review test
- [ ] 3. 🤖 `/implement-feature` จน green · `pnpm lint`, `typecheck`, `test`, `build`
- [ ] 4. 🙋 Jam ลองในเบราว์เซอร์: API ในเครื่อง `AUTH_REQUIRED=true` ชี้ `anyang-dev` + `pnpm dev` → login ด้วยบัญชีของตัวเอง → เปิดหน้า scope / ห้องติวของ prep ได้ข้อมูลจริง · (ขั้นละเอียดจะเขียนให้ตอนถึงขั้นนี้)
- [ ] 5. 🤖 อัปเดต docs + checklist แล้ว `/work-done`

## Definition of done

- มีหน้า `/login` (email + password) · login แล้วกลับไปหน้าที่ตั้งใจจะไป
- ทุก request ที่ไป API แนบ `Authorization` เมื่อมี session · 401 พาไปหน้า login
- ไม่มี session บนเครื่อง dev (`AUTH_REQUIRED=false`) ยังทำงานกับ stub เหมือนเดิม · test เดิมไม่ต้องแก้

## Decisions

- 2026-11-15 · May ให้ Jam ทำหน้า login ช่วง solo แล้วมา review หน้าตาและ flow ทีหลัง · ใช้แบบ Tailwind แบบหน้าที่มีอยู่

## Next step

ขั้น 3: implement

## Waiting on

- May: review หน้าตาและข้อความของหน้า login

## Notes for next time

- web test ของหน้าห้องติวพังในเครื่อง 66 ข้อ (หา label "พิมพ์ตอบ" ไม่เจอ · timeout) ตั้งแต่ก่อนงานนี้ · CI ผ่าน · ต้องดูตอนรัน `pnpm test`
