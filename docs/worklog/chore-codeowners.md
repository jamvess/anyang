# แก้ CODEOWNERS เป็น GitHub username จริง

| | |
|---|---|
| Owner | Junior |
| Branch | `chore/codeowners` |
| Checklist item | แก้ `.github/CODEOWNERS` เป็น username จริง |
| Status | in progress · 2026-10-19 |

## Plan

- [x] 1. 🤖 แทน `@junior-handle` `@may-handle` `@jam-handle` ใน `.github/CODEOWNERS` ด้วย `@jnmonsicha2000` `@jantarat32443` `@jamvess` (จากตาราง GitHub ใน `roles.md`) · เพิ่มบรรทัด `/.github/ @jnmonsicha2000` ให้ตรงกับ `roles.md` · ลบ comment "Replace handles…"
- [x] 2. 🤖 อัปเดต docs: `setup.md` ขั้น A0 ข้อ 3 (บอกว่าแก้แล้ว) · ติ๊ก checklist ข้อนี้ใน `sprint-checklists.md`
- [ ] 3. 🙋 หลัง merge: เปิด PR ใดก็ได้ แล้วดูช่อง Reviewers ด้านขวาว่า GitHub ขอ review จากคนที่ถูกต้องเอง · บอกในแชทกลุ่มว่า CODEOWNERS ใช้งานได้แล้ว

## Definition of done

- `.github/CODEOWNERS` ไม่มี handle ปลอมเหลือ · ทุก handle เป็น collaborator ที่มีสิทธิ์ write (เช็คแล้ว 19 ต.ค.: jamvess admin, jnmonsicha2000 write, jantarat32443 write)
- หน้า PR บน GitHub ไม่ขึ้นคำเตือน "CODEOWNERS has errors"
- ติ๊ก checklist ข้อนี้แล้ว

## Decisions

- 2026-10-19 · เพิ่ม `/.github/` ให้ Junior · `roles.md` บอกว่า Junior เป็นเจ้าของ `.github/` แต่ CODEOWNERS เดิมไม่มีบรรทัดนี้

## Next step

ขั้น 3 (🙋 หลัง merge): เปิด PR ใดก็ได้ ดูช่อง Reviewers ว่า GitHub ขอ review ถูกคน แล้วบอกในแชทกลุ่ม

## Waiting on

ไม่มี

## Notes for next time

- 2026-10-19 · เช็ค ruleset แล้ว: ruleset 25137368 ที่ checklist อ้างถึงไม่มีอยู่แล้ว (404) · ruleset ที่มีคือ `main` id 25374094 (สร้าง 19 ต.ค. 12:38) มี `require_code_owner_review: false` · **ไม่ได้บังคับ code-owner review** CODEOWNERS แค่ขอ reviewer ให้อัตโนมัติ · บรรทัดที่มีเจ้าของคนเดียว (เช่น `/.github/`) จึงไม่ทำให้ PR ติด ไม่ต้องเพิ่มคนที่สอง
- 2026-10-19 · ⚠️ ruleset 25374094 มี `enforcement: disabled` และ API บอกว่า `main` เป็น `protected: false` · ตอนนี้ไม่มีกฎ PR + 1 approval + CI 3 job บังคับบน `main` เลย ไม่ตรงกับ checklist S1 ข้อแรก · Jam (admin) ต้องเปิดเป็น Active ที่ Settings → Rules → Rulesets → `main` · ไม่ได้แก้ใน PR นี้
- 2026-10-19 · Jam ขอให้ข้ามเรื่องเปิด ruleset ไปก่อน · ระหว่างนี้ทุกคนต้องทำตามกติกาเอง: ไม่ push ตรงเข้า `main` · รอ approve 1 คน + CI เขียวก่อน merge
