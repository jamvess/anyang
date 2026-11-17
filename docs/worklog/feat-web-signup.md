# หน้าสมัครสมาชิก (goal อาจารย์ข้อ 1)

| | |
|---|---|
| Owner | May |
| Branch | `feat/web-signup` |
| Checklist item | (ยังไม่มีใน checklist · goal อาจารย์ 17 พ.ย. ข้อ 1 "สมัครและ login ด้วย username / password" · `web-login.md` §9 เดิมเลื่อนหน้าสมัครไป S5) · จะเพิ่มข้อ ⭐ ใน May S4 ตอน `/work-done` |
| Status | in progress · 2026-11-17 |

## Plan

Requirement: UM-01 (สมัครด้วย email + password) · ต่อจาก `specs/features/platform/web-login.md` (#138) · Supabase `anyang-dev` (D2)

- [ ] 1. 🙋 May ถาม Junior: เปิด "Allow new users to sign up" ใน `anyang-dev` ไว้ถึงหลัง 23 พ.ย. ได้ไหม (D2 วางแผนจะปิด) · Confirm email ปิดอยู่แล้ว (D2 ค) สมัครแล้วเข้าได้ทันที
- [x] 2. 🤖 `/spec-feature` → `specs/features/platform/web-signup.md` · 🙋 May ตัดสินหน้าตาและ flow ผ่านตัวเลือก แล้ว ok spec · 17 พ.ย. ok (ช่องยืนยันรหัส · ไปหน้าหลัก · ลิงก์ทั้งสองทาง · กฎรหัสให้ Supabase)
- [ ] 3. 🤖 `/spec-to-tests` → 🙋 May review test
- [ ] 4. 🤖 `/implement-feature` จน test ผ่าน + lint + typecheck
- [ ] 5. 🙋 May ลองในเบราว์เซอร์กับ `anyang-dev`: สมัครบัญชีทดสอบใหม่ → เข้าหน้าหลัก → logout → login ด้วยบัญชีนั้น
- [ ] 6. 🤖 `/work-done`

## Definition of done

- สมัครด้วย email + password ได้จากหน้าเว็บ แล้วเข้าระบบทันที (UM-01) · มีลิงก์ระหว่างหน้า login กับหน้าสมัคร
- AC ของ spec มี test และผ่าน · ลองกับ `anyang-dev` ผ่าน

## Decisions

- 2026-11-17 · May เลือกทำหน้าสมัครเพราะ goal อาจารย์ข้อ 1 ยังขาดส่วนสมัคร (login เสร็จแล้ว #138)

## Next step

`/spec-to-tests` · ขั้น 1 ยังรอ Junior

## Waiting on

- Junior: เปิดการสมัครใน `anyang-dev` ไว้ (ขั้น 1)

## Notes for next time

- บัญชี demo ห้ามใช้ทดสอบ (D2 ก) · ทดสอบให้สมัครบัญชีของตัวเอง
