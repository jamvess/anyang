# แก้ CODEOWNERS เป็น GitHub username จริง

| | |
|---|---|
| Owner | Junior |
| Branch | `chore/codeowners` |
| Checklist item | แก้ `.github/CODEOWNERS` เป็น username จริง |
| Status | in progress · 2026-10-19 |

## Plan

- [ ] 1. 🤖 แทน `@junior-handle` `@may-handle` `@jam-handle` ใน `.github/CODEOWNERS` ด้วย `@jnmonsicha2000` `@jantarat32443` `@jamvess` (จากตาราง GitHub ใน `roles.md`) · เพิ่มบรรทัด `/.github/ @jnmonsicha2000` ให้ตรงกับ `roles.md` · ลบ comment "Replace handles…"
- [ ] 2. 🤖 อัปเดต docs: `setup.md` ขั้น A0 ข้อ 3 (บอกว่าแก้แล้ว) · ติ๊ก checklist ข้อนี้ใน `sprint-checklists.md`
- [ ] 3. 🙋 หลัง merge: เปิด PR ใดก็ได้ แล้วดูช่อง Reviewers ด้านขวาว่า GitHub ขอ review จากคนที่ถูกต้องเอง · บอกในแชทกลุ่มว่า CODEOWNERS ใช้งานได้แล้ว

## Definition of done

- `.github/CODEOWNERS` ไม่มี handle ปลอมเหลือ · ทุก handle เป็น collaborator ที่มีสิทธิ์ write (เช็คแล้ว 19 ต.ค.: jamvess admin, jnmonsicha2000 write, jantarat32443 write)
- หน้า PR บน GitHub ไม่ขึ้นคำเตือน "CODEOWNERS has errors"
- ติ๊ก checklist ข้อนี้แล้ว

## Decisions

- 2026-10-19 · เพิ่ม `/.github/` ให้ Junior · `roles.md` บอกว่า Junior เป็นเจ้าของ `.github/` แต่ CODEOWNERS เดิมไม่มีบรรทัดนี้

## Next step

ขั้น 1: แก้ `.github/CODEOWNERS`

## Waiting on

ไม่มี

## Notes for next time

- อ่าน ruleset ของ `main` ผ่าน API ไม่ได้ (สิทธิ์ write ได้ `[]`) · ถ้าอยากรู้ว่าเปิด "Require review from Code Owners" ไหม ต้องถาม Jam (admin)
