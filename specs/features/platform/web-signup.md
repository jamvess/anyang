# Feature: หน้าสมัครสมาชิก (email + password · goal อาจารย์ข้อ 1)

| | |
|---|---|
| Area | platform (หน้าเว็บ) |
| Requirements | UM-01 (ส่วนสมัคร), SA-02 (tenant + profile ตอนสมัคร · trigger ใน DB มีแล้ว) |
| Owner | May |
| Reviewer | May (spec + test) · Jam ดูย้อนหลัง (เจ้าของ `web-login.md`) · Junior ดูเรื่องการเปิดรับสมัครใน `anyang-dev` |
| Status | approved 2026-11-17 (May ok spec) |
| Related system spec | `web-login.md` (#138 · หน้า login, `safeNext`, `strings.ts`) · `docs/team/sprint-checklists.md` D1 (email + password), D2 (`anyang-dev` · ปิด Confirm email · แผนปิด "Allow new users to sign up") · `use-cases.md` UC-01 (S02 สมัคร · S28 เช็คอีเมล · S29 อีเมลซ้ำ · คำถามเปิดข้อ 1 กฎรหัสผ่าน) · migration `0001` (trigger สร้าง tenant + profile) · goal อาจารย์ 17 พ.ย. ข้อ 1 |

## 1. Context

login ทำแล้ว (#138) แต่สมัครได้ทางเดียวคือสร้างบัญชีใน Dashboard ของ Supabase · goal ของอาจารย์ข้อ 1 คือ "สมัครและ login ด้วย username / password" (ใช้อีเมลเป็น username ตาม D1) · feature นี้เพิ่มหน้า `/signup` ที่สมัครด้วยอีเมล + รหัสผ่านผ่าน Supabase แล้วเข้าระบบทันที (Confirm email ปิดใน `anyang-dev` · D2 ค) และเพิ่มลิงก์ไปมาระหว่างหน้า login กับหน้าสมัคร · การสร้าง tenant + profile ทำโดย trigger ใน DB อยู่แล้ว (SA-02) หน้าเว็บไม่ต้องทำ

## 2. Behavior

### 2.1 หน้า `/signup` (`app/(auth)/signup/page.tsx` + `components/auth/SignupForm.tsx`)

1. ช่อง **อีเมล** (`type="email"`, required, `autoComplete="email"`) · **รหัสผ่าน** (`type="password"`, required, `autoComplete="new-password"`) · **ยืนยันรหัสผ่าน** (`type="password"`, required, `autoComplete="new-password"`) · ปุ่ม **สมัครสมาชิก** · ทุกช่องมี label (May 17 พ.ย.: มีช่องยืนยัน เพราะยังไม่มีลืมรหัสผ่าน พิมพ์ผิดแล้วเข้าบัญชีไม่ได้อีก)
2. กดสมัคร:
   1. รหัสผ่านสองช่องไม่ตรงกัน → "รหัสผ่านทั้งสองช่องไม่ตรงกัน" · **ไม่เรียก Supabase**
   2. ตรงกัน → `supabase.auth.signUp({email, password})` · ระหว่างรอ: ปุ่มกดไม่ได้และเขียนว่า "กำลังสมัคร…"
3. ผ่านและได้ session (Confirm email ปิด) → ไป `next` (ปุ่มยังกดไม่ได้ระหว่างโหลดหน้าถัดไป · กันสมัครซ้ำ · self-review PR #144) (query `?next=` · กฎเดียวกับหน้า login ผ่าน `safeNext` · `web-login.md` §2.1 ข้อ 4) หรือ `/` ถ้าไม่มี (May 17 พ.ย.: หน้าหลัก · onboarding อยู่ S5)
4. ผ่านแต่ไม่มี session (Confirm email เปิด · ไม่ใช่ค่าของ `anyang-dev` ตอนนี้) · ถ้า `user.identities` ว่าง = อีเมลนี้มีบัญชีแล้ว (Supabase ซ่อนอีเมลซ้ำแบบนี้เมื่อเปิด Confirm email) → ทำแบบอีเมลซ้ำของข้อ 5 · ไม่งั้น → ซ่อนฟอร์ม แสดง "สมัครแล้ว เปิดอีเมลเพื่อยืนยันก่อนเข้าสู่ระบบ" (`role="status"`) + ลิงก์ "เข้าสู่ระบบ" · ไม่ navigate (wireframe S28 แบบย่อ)
5. ไม่ผ่าน (`error.code` ของ Supabase) → ข้อความใน `role="alert"`:

   | กรณี | ข้อความ |
   |---|---|
   | `user_already_exists` หรือ `email_exists` | อีเมลนี้มีบัญชีแล้ว + ลิงก์ "เข้าสู่ระบบ" (S29) |
   | `weak_password` | รหัสผ่านสั้นหรือง่ายเกินไป ลองตั้งใหม่ |
   | `email_address_invalid` | อีเมลนี้ใช้สมัครไม่ได้ |
   | `signup_disabled` หรือ `email_provider_disabled` (ปิดผู้ให้บริการ Email ทั้งหมด · self-review PR #144) | ตอนนี้ปิดรับสมัครอยู่ |
   | อื่นๆ หรือ throw (เครือข่าย, Supabase ล่ม, rate limit) | สมัครไม่ได้ตอนนี้ ลองใหม่อีกครั้ง |

   หลังผิดพลาด (รวมข้อ 2.1): ช่องรหัสผ่านทั้งสองถูกล้าง อีเมลคงไว้ · ปุ่มกดได้อีก
6. **กฎรหัสผ่าน: Supabase ตัดสิน** (May 17 พ.ย.) · หน้าเว็บไม่ตั้งความยาวขั้นต่ำเอง (ไม่มี magic number · ค่าอยู่ที่ Supabase · local `supabase/config.toml` `minimum_password_length = 6`) · ผิดกฎ → `weak_password` → ข้อ 5 · กฎจริงยังเป็นคำถามเปิดของ Junior (UC-01 ข้อ 1)
7. มี session อยู่แล้วตอนเปิดหน้า → ไป `next` เลย (แบบหน้า login)
8. ใต้ปุ่มมี "มีบัญชีแล้ว?" + ลิงก์ "เข้าสู่ระบบ" → `/login` (คง `?next=` เดิมถ้ามี)
9. ข้อความทั้งหมดอยู่ใน `components/auth/strings.ts`

### 2.2 หน้า `/login` (แก้ `web-login.md` §2.1 ข้อ 7)

ใต้ปุ่มเข้าสู่ระบบมี "ยังไม่มีบัญชี?" + ลิงก์ "สมัครสมาชิก" → `/signup` (คง `?next=` เดิมถ้ามี) · ไม่เปลี่ยนอย่างอื่น (May 17 พ.ย.: ลิงก์ทั้งสองทาง)

### 2.3 การส่ง `next` ต่อระหว่างสองหน้า

ลิงก์ส่ง `next` ต่อเฉพาะค่าที่ผ่าน `safeNext` และไม่ใช่ `/` · encode ด้วย `encodeURIComponent` · ไม่มี → ลิงก์ไม่มี query

### 2.4 Accessibility (NFR-A1)

ทุกช่องมี label · ปุ่มและลิงก์ใช้คีย์บอร์ดได้ · ข้อผิดพลาดอยู่ใน `role="alert"`

### 2.5 ข้อความ (`components/auth/strings.ts` · เพิ่ม)

| key | ข้อความ |
|---|---|
| `signupTitle` | สมัครสมาชิก |
| `confirmPassword` | ยืนยันรหัสผ่าน |
| `signupSubmit` | สมัครสมาชิก |
| `signupSubmitting` | กำลังสมัคร… |
| `passwordMismatch` | รหัสผ่านทั้งสองช่องไม่ตรงกัน |
| `emailTaken` | อีเมลนี้มีบัญชีแล้ว |
| `weakPassword` | รหัสผ่านสั้นหรือง่ายเกินไป ลองตั้งใหม่ |
| `emailInvalid` | อีเมลนี้ใช้สมัครไม่ได้ |
| `signupDisabled` | ตอนนี้ปิดรับสมัครอยู่ |
| `signupFailed` | สมัครไม่ได้ตอนนี้ ลองใหม่อีกครั้ง |
| `checkEmail` | สมัครแล้ว เปิดอีเมลเพื่อยืนยันก่อนเข้าสู่ระบบ |
| `haveAccount` | มีบัญชีแล้ว? |
| `toLogin` | เข้าสู่ระบบ |
| `noAccount` | ยังไม่มีบัญชี? |
| `toSignup` | สมัครสมาชิก |

## 3. Inputs and outputs

| | Type / schema | ตัวอย่าง |
|---|---|---|
| Input | อีเมล + รหัสผ่าน + ยืนยันรหัสผ่าน · `?next=` | `/signup?next=/preps/new` |
| Call | `supabase.auth.signUp({email, password})` | |
| Output | session ใน cookie (แบบหน้า login) · บัญชี + tenant + profile ใน `anyang-dev` (trigger `0001`) | |

## 4. Acceptance criteria

Vitest + Testing Library · Supabase client ปลอม (`vi.mock("@/lib/supabase")` แบบ `LoginForm.test.tsx`) · ไม่มี network

- **AC-1 (UM-01)** Given กรอกอีเมล รหัสผ่าน และยืนยันรหัสผ่านที่ตรงกัน When กดสมัคร Then `signUp` ได้ `{email, password}` ที่กรอก 1 ครั้ง · ระหว่างรอปุ่มเป็น "กำลังสมัคร…" และกดไม่ได้ · ได้ session → `navigate("/")`
- **AC-2 (UM-01)** Given `next` = `/preps/new` When สมัครผ่าน Then `navigate("/preps/new")` · Given `next` = `//evil.example` Then `navigate("/")`
- **AC-3 (UM-01)** Given รหัสผ่านสองช่องไม่ตรงกัน When กดสมัคร Then `signUp` ไม่ถูกเรียก · `role="alert"` "รหัสผ่านทั้งสองช่องไม่ตรงกัน" · ช่องรหัสผ่านทั้งสองว่าง · อีเมลคงไว้
- **AC-4 (UM-01)** Given `signUp` ตอบ error code ตามตาราง §2.1 ข้อ 5 (`user_already_exists`, `email_exists`, `weak_password`, `email_address_invalid`, `signup_disabled`, code อื่น) และกรณี `signUp` throw When กดสมัคร Then ข้อความตามตารางใน `role="alert"` · ไม่ navigate · ช่องรหัสผ่านทั้งสองว่าง · อีเมลคงไว้ · ปุ่มกดได้
- **AC-5 (UM-01)** Given `user_already_exists` Then ใน alert มีลิงก์ "เข้าสู่ระบบ" ไป `/login`
- **AC-6 (UM-01)** Given `signUp` ผ่านแต่ `session` เป็น null Then ไม่ navigate · `role="status"` "สมัครแล้ว เปิดอีเมลเพื่อยืนยันก่อนเข้าสู่ระบบ" · มีลิงก์ "เข้าสู่ระบบ" · ไม่มีฟอร์ม (ไม่มีปุ่มสมัคร)
- **AC-7 (UM-01)** Given มี session ตอนเปิดหน้า Then `navigate(next)` โดยไม่ต้องกรอก · Given ไม่มี env ของ Supabase (`createClient` throw) Then ฟอร์มยังแสดง
- **AC-8 (NFR-A1)** ช่องอีเมล รหัสผ่าน ยืนยันรหัสผ่าน หาได้ด้วย `getByLabelText` · ปุ่ม "สมัครสมาชิก" หาได้ด้วย `getByRole("button")` · ช่องรหัสผ่านทั้งสองเป็น `type="password"` และ `autoComplete="new-password"`
- **AC-9 (UM-01)** หน้าสมัคร: ลิงก์ "เข้าสู่ระบบ" ไป `/login` · มี `next=/preps/new` → `/login?next=%2Fpreps%2Fnew` · `next` ไม่ปลอดภัย → `/login`
- **AC-10 (UM-01)** หน้า login: ลิงก์ "สมัครสมาชิก" ไป `/signup` · มี `next=/preps/new` → `/signup?next=%2Fpreps%2Fnew` · test เดิมของ `LoginForm.test.tsx` ผ่านโดยไม่แก้

ไม่มี threshold ในหน้าเว็บ (กฎรหัสผ่านอยู่ที่ Supabase · §2.1 ข้อ 6) · การแยก tenant ของบัญชีใหม่ทำโดย trigger `0001` (มี test isolation ของ DB แล้ว) · หน้าเว็บไม่อ่านหรือเขียนตารางเอง จึงไม่มี AC-tenant

## 5. Data changes

ไม่มี (trigger `0001` สร้าง tenant + membership + profile เมื่อมี `auth.users` ใหม่)

## 6. API / SSE changes

ไม่มี · ใช้ Supabase Auth (`signUp`) จากเบราว์เซอร์แบบเดียวกับ `signInWithPassword`

## 7. AI calls

ไม่มี

## 8. Test plan

| Test | ระดับ | ครอบคลุม AC |
|---|---|---|
| `apps/web/tests/auth/SignupForm.test.tsx` (ใหม่) | component | AC-1 ถึง AC-9 |
| `apps/web/tests/auth/LoginSignupLink.test.tsx` (ใหม่ · ไม่แก้ `LoginForm.test.tsx`) | component | AC-10 |
| test เดิมทั้งหมด | | AC-10 |
| ลองในเบราว์เซอร์กับ `anyang-dev` (May) | มือ | สมัครบัญชีทดสอบใหม่ → หน้าหลัก (API ตอบด้วย token ของบัญชีใหม่ · มี tenant) → logout → login ด้วยบัญชีนั้น · สมัครซ้ำ → "อีเมลนี้มีบัญชีแล้ว" |

## 9. Out of scope

- Google (UM-02), ยืนยันอีเมลเต็มรูปแบบ (S28 ส่งใหม่, หมดอายุ), ลืมรหัสผ่าน · S5
- onboarding: เลือก tutor + buddy, ชื่อเล่น ระดับ ภาษา (S04–S06 · S5) · บัญชีใหม่ใช้ค่าเริ่มต้นของ profile ใน DB
- กันบอท / captcha · การปิดรับสมัครหลัง demo (Junior · D2)
- หน้าแรก landing (S01)

## 10. Open questions

1. **(Junior) เปิดรับสมัครใน `anyang-dev`:** D2 วางแผนปิด "Allow new users to sign up" หลังทีมสร้างบัญชีครบ · หน้านี้ต้องเปิดไว้อย่างน้อยถึงวิดีโอ 23 พ.ย. · ถ้าปิด หน้าแสดง "ตอนนี้ปิดรับสมัครอยู่" (ไม่พัง) · ความเสี่ยงเดิมของ D2: ใครที่รู้ URL + publishable key สมัครแล้วใช้ AI จริงได้ (มี rate limit)
2. **(Junior) กฎรหัสผ่าน** (UC-01 ข้อ 1): ยาวขั้นต่ำและต้องมีตัวเลขไหม · หน้าเว็บไม่เปลี่ยนตาม (§2.1 ข้อ 6)
3. **code ของ Supabase:** อีเมลซ้ำมีได้ทั้ง `user_already_exists` และ `email_exists` (ขึ้นกับรุ่นของ Auth) จึงรับทั้งคู่ · ยืนยันตอนลองกับ `anyang-dev`

## 11. Spec changes needed

| ไฟล์ | แก้อะไร | ใคร |
|---|---|---|
| `specs/features/platform/web-login.md` §2.1 ข้อ 7, §9 | มีลิงก์ "สมัครสมาชิก" แล้ว (§2.2 ของ spec นี้) · หน้าสมัครย้ายออกจาก out of scope | May · PR นี้ (spec ของ Jam · บอก Jam) |
| `docs/design/use-cases.md` UC-01 | หมายเหตุ: demo สมัครด้วยอีเมล (UM-01) ก่อน Google · หลังสมัครไปหน้าหลัก (onboarding S5) | May · PR นี้ |
