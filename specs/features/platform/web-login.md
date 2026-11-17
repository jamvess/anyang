# Feature: หน้า login + แนบ token ทุก request (demo ขั้น 1 ฝั่งเว็บ)

| | |
|---|---|
| Area | platform (หน้าเว็บ) |
| Requirements | UM-01 (เข้าสู่ระบบด้วย email + password ตาม D1 · ส่วนสมัครอยู่ S5), SA-06 |
| Owner | Jam (งานของ May · May ให้ทำได้เลย 15 พ.ย.) |
| Reviewer | May (หน้าตา ข้อความ flow · ดูย้อนหลัง) · Jam |
| Status | approved 2026-11-15 (Jam ok spec + test) · implemented 2026-11-15 (PR #138) · May review หน้าตาและข้อความแล้ว 17 พ.ย. (ไม่แก้) |
| Related system spec | `api-auth.md` (API ตรวจ token · 401 `missing_token` / `invalid_token`) · api.md "Auth" · `docs/team/sprint-checklists.md` D1 (email + password บน `anyang-dev`) · `room-http.md`, `scope-review.md` (หน้าที่เรียก API) · `apps/web/CLAUDE.md` |

## 1. Context

API ตรวจ token แล้ว (#134: token ของ `anyang-dev` มี `tenant_id` · `AUTH_REQUIRED=true` ตอบ `401` เมื่อไม่มี token) แต่หน้าเว็บยังไม่มีหน้า login และทุก request ไม่ส่ง `Authorization` · หน้า scope และห้องติวจึงใช้ข้อมูลจริงไม่ได้ · feature นี้เพิ่มหน้า login (email + password ตาม D1) · เก็บ session ด้วย `@supabase/ssr` (cookie) · แนบ token ทุก request ไป API จากที่เดียว · 401 พาไปหน้า login

## 2. Behavior

### 2.1 หน้า `/login` (`app/(auth)/login/page.tsx` + `components/auth/LoginForm.tsx`)

1. ช่อง **อีเมล** (`type="email"`, required) · **รหัสผ่าน** (`type="password"`, required) · ปุ่ม **เข้าสู่ระบบ** · ทุกช่องมี label (เข้าถึงด้วยคีย์บอร์ดได้ · `apps/web/CLAUDE.md`)
2. กดเข้าสู่ระบบ → `supabase.auth.signInWithPassword({email, password})` · ระหว่างรอ: ปุ่มกดไม่ได้และเขียนว่า "กำลังเข้าสู่ระบบ…"
3. ผ่าน → ไป `next` (query `?next=`) หรือ `/` ถ้าไม่มี
4. **`next` ที่ใช้ได้:** path ภายในเว็บเท่านั้น (ขึ้นต้นด้วย `/` แต่ไม่ใช่ `//` และไม่มี `\`) · ไม่มีตัวอักษรควบคุม (tab, CR, LF ฯลฯ ที่ URL parser ตัดทิ้งจน `/\t/evil` กลายเป็น `//evil`) · parse แล้วต้องเป็น origin เดียวกัน · ไม่งั้นใช้ `/` (กัน open redirect · self-review PR #138)
5. ผิด: อีเมลหรือรหัสผ่านไม่ถูก (Supabase code `invalid_credentials` เท่านั้น · 400 อื่น เช่นยังไม่ยืนยันอีเมล ใช้ข้อความ "ลองใหม่" · self-review PR #138) → "อีเมลหรือรหัสผ่านไม่ถูกต้อง" · อย่างอื่น (เครือข่าย, Supabase ล่ม) → "เข้าสู่ระบบไม่ได้ตอนนี้ ลองใหม่อีกครั้ง" · ข้อความอยู่ใน `role="alert"` · รหัสผ่านที่พิมพ์ไว้ถูกล้าง อีเมลคงไว้
6. มี session อยู่แล้วตอนเปิดหน้า → ไป `next` เลย
7. ~~ไม่มีลิงก์สมัคร~~ ใต้ปุ่มมี "ยังไม่มีบัญชี? สมัครสมาชิก" → `/signup` (`web-signup.md` §2.2 · May 17 พ.ย. · goal อาจารย์ข้อ 1)
8. ข้อความทั้งหมดอยู่ใน `components/auth/strings.ts` (ภาษาไทย · May แก้ที่เดียว)

### 2.2 ออกจากระบบ (`/logout`)

เปิด `/logout` → `supabase.auth.signOut({scope: "local"})` (เฉพาะเบราว์เซอร์นี้ · อุปกรณ์อื่นของผู้ใช้ยัง login อยู่ · self-review PR #138) → ไป `/login` · ล้มก็ไป `/login` (session ใน cookie ถูกล้างโดย client อยู่แล้ว) · หน้าอื่นลิงก์มาที่นี่ได้ (ปุ่มในหน้ารายการ prep ของ demo ขั้น 2)

### 2.3 แนบ token ทุก request (`lib/auth.ts`)

1. `authHeaders()` → `{Authorization: "Bearer <access_token>"}` จาก `supabase.auth.getSession()` · ไม่มี session หรืออ่านไม่ได้ (ไม่มี env ของ Supabase เช่นใน test หรือเครื่อง dev ที่ไม่ตั้ง) → `{}` (ไม่แนบ · API ที่ `AUTH_REQUIRED=false` ตอบ stub เหมือนเดิม)
2. `apiFetch(path, init)` = `fetch(apiUrl(path), init + authHeaders())` · ใช้แทน `fetch(apiUrl(…))` ทุกที่: `TutorRoom` (`getJSON`), `ScopeReview` (`getJSON`, confirm), `httpTransport` (ขอ URL อัปโหลด)
3. `postSSE` ที่ไป API (เปิดห้อง, ส่งข้อความ, ยืนยันลายมือ) ได้ `authHeaders()` ใน `headers` · `postSSE` เองไม่รู้เรื่อง auth (ใช้กับ URL ใดก็ได้)
4. **ไม่แนบ** กับ URL ที่ไม่ใช่ API: `PUT` รูปไป signed URL ของ Storage (มี test เดิมยืนยันแล้ว · room-photo-send AC-6)
5. **API ตอบ `401`** (token หมดอายุหรือไม่มี) ที่ `apiFetch` หรือ SSE ของ API → ล้าง session ของเบราว์เซอร์นี้ก่อน (`signOut({scope: "local"})` · ไม่งั้นหน้า login เห็น session เดิมแล้วส่งกลับมาวนไม่จบ · self-review PR #138) → พาไป `/login?next=<path ปัจจุบัน + query>` · หน้าที่เรียกยังได้ error ตามเดิม (ไม่ค้าง)
6. token หมดอายุ: `@supabase/ssr` ต่ออายุ session เองตอน `getSession()` · ต่อไม่ได้ → ไม่มี session → API ตอบ 401 → ข้อ 5

### 2.4 สิ่งที่ไม่เปลี่ยน

ไม่มี session บนเครื่อง dev (`AUTH_REQUIRED=false`) → ไม่มี header · ทุกหน้าใช้ stub เหมือนเดิม · ไม่บังคับ login ฝั่งเว็บ (ไม่มี middleware / proxy · API เป็นคนบอกด้วย 401) · test เดิมทั้งหมดผ่านโดยไม่แก้

## 3. Inputs and outputs

| | Type / schema | ตัวอย่าง |
|---|---|---|
| Input | อีเมล + รหัสผ่านของบัญชีใน `anyang-dev` · `?next=` | `/login?next=/preps/…/scope` |
| Output | session ของ Supabase ใน cookie · header `Authorization: Bearer …` ทุก request ไป API | |

## 4. Acceptance criteria

Vitest + Testing Library · Supabase client ปลอม (`vi.mock("@/lib/supabase")`) · `fetch` ปลอม

- **AC-1 (UM-01)** กรอกอีเมลและรหัสผ่าน กดเข้าสู่ระบบ → `signInWithPassword` ได้ค่าที่กรอก · ระหว่างรอปุ่มเป็น "กำลังเข้าสู่ระบบ…" และกดไม่ได้ · ผ่าน → `navigate(next)`
- **AC-2** `next` = `/preps/p1/scope` → ไปที่นั่น · ไม่มี `next` → `/` · `next` = `https://evil.example` หรือ `//evil.example` หรือ `/\evil` → `/`
- **AC-3** Supabase ตอบ invalid credentials → "อีเมลหรือรหัสผ่านไม่ถูกต้อง" ใน `role="alert"` · ไม่ navigate · ช่องรหัสผ่านว่าง · อีเมลคงไว้
- **AC-4** Supabase โยน error อื่น → "เข้าสู่ระบบไม่ได้ตอนนี้ ลองใหม่อีกครั้ง"
- **AC-5** มี session ตอนเปิดหน้า → `navigate(next)` โดยไม่ต้องกรอก
- **AC-6** ทุกช่องและปุ่มมี label ที่ Testing Library หาด้วย `getByLabelText` / `getByRole` ได้
- **AC-7 (SA-06)** มี session (`access_token` = `t-1`) → `apiFetch("/exam-preps")` ส่ง `Authorization: Bearer t-1` ไป `<API>/exam-preps` และคง header อื่นของ caller · ไม่มี session → ไม่มี `Authorization`
- **AC-8** ไม่มี env ของ Supabase (createClient โยน) → `authHeaders()` = `{}` · `apiFetch` ยังเรียก API ได้
- **AC-9** API ตอบ `401` → พาไป `/login?next=<path+query ปัจจุบัน>` (encode) · คืน response 401 ให้ caller
- **AC-10** ห้องติวและหน้า scope แนบ `Authorization` ทุก request ไป API เมื่อมี session (เปิดห้อง · ส่งข้อความ · ขอ URL อัปโหลด · ยืนยันลายมือ · อ่าน scope · ยืนยัน scope) · `PUT` ไป Storage ไม่มี
- **AC-11** `/logout` → `signOut()` แล้วไป `/login` · `signOut` ล้มก็ยังไป `/login`
- **AC-12** test เดิมทั้งหมดผ่านโดยไม่แก้ (ไม่มี session ใน test → ไม่มี header)

## 5. Data changes

ไม่มี

## 6. API / SSE changes

ไม่มี · ใช้ header `Authorization` ตาม api.md "Auth"

## 7. AI calls

ไม่มี

## 8. Test plan

| Test | ระดับ | ครอบคลุม AC |
|---|---|---|
| `tests/auth/LoginForm.test.tsx` (ใหม่) | component | AC-1 ถึง AC-6 |
| `tests/auth/apiAuth.test.ts` (ใหม่ · `lib/auth.ts`) | unit | AC-7 ถึง AC-9 |
| `tests/auth/pagesAuth.test.tsx` (ใหม่ · หน้า scope + ห้องติวกับ session ปลอม) และ `tests/auth/apiAuth.test.ts` (transport) | component / unit | AC-10 |
| `tests/auth/LoginForm.test.tsx` (describe `Logout`) | component | AC-11 |
| test เดิมทั้งหมด | | AC-12 |
| ลองในเบราว์เซอร์กับ `anyang-dev` (ขั้น 4 ของ worklog · Jam) | มือ | login → หน้า scope / ห้องติวได้ข้อมูลจริง |

**ผลลองในเบราว์เซอร์กับ `anyang-dev` (15 พ.ย. · ขั้น 4 ของ worklog · Jam · API ในเครื่อง `AUTH_REQUIRED=true` + `pnpm dev` · บัญชีของ Jam ที่สมัครผ่าน `/auth/v1/signup`):** ไม่มี session เปิดหน้า scope → API `401` → เด้งไป `/login?next=…` · login → กลับหน้าเดิม · prep id ที่ไม่มีอยู่ → "ไม่พบการเตรียมสอบนี้" (API ตอบ `404` · token ถึง API แล้ว) · รหัสผิด → "อีเมลหรือรหัสผ่านไม่ถูกต้อง" · อีเมลคงไว้ รหัสว่าง · login ไม่มี `next` → `/` · `/logout` → `/login` · เปิดหน้า scope อีกครั้ง → เด้งไป login · **ผ่านทุกข้อ (Jam)** · ยังไม่ได้ลองกับ prep ที่มีหัวข้อจริง (รอหน้ารายการ prep และหน้าอัปโหลด · demo ขั้น 2–3)

## 9. Out of scope

- ~~หน้าสมัคร~~ (ทำแล้วใน `web-signup.md` · 17 พ.ย.), ยืนยันอีเมล, ลืมรหัสผ่าน, Google (UM-02 · S5 พร้อม onboarding)
- บังคับ login ฝั่งเว็บก่อนเปิดหน้า (middleware / proxy ของ Next) · ตอนนี้ API เป็นคนบอกด้วย 401
- หน้ารายการ prep และปุ่มออกจากระบบในหน้านั้น (demo ขั้น 2)
- หน้าตาตามแบบ wireframe S02 (May ปรับทีหลัง)

## 10. Open questions

1. **(May) หน้าตาและข้อความ:** ใช้ Tailwind แบบหน้าที่มีอยู่ · ข้อความใน `strings.ts` · May ปรับทีหลังได้โดยไม่แตะ logic
2. **(May) หลัง login ไปไหน:** `next` หรือ `/` · ตอนนี้ `/` ยังเป็นหน้า template ของ Next จนกว่าหน้ารายการ prep (demo ขั้น 2) เสร็จ

## 11. Spec changes needed

ไม่มี (ไม่แตะไฟล์กลาง)
