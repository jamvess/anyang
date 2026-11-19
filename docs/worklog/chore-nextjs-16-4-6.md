# อัปเกรด Next.js 16.4.3 → 16.4.6 ก่อนอัดวิดีโอ

| | |
|---|---|
| Owner | May |
| Branch | `chore/nextjs-16-4-6` |
| Checklist item | ⭐ ก่อนอัดวิดีโอ · อัปเกรด Next.js 16.4.3 → 16.4.6 (`next dev` แจ้ง upgrade policy `security` = มี advisory · PR แยก + CI · บอกกลุ่ม · พบใน #151) |
| Status | in progress · 2026-11-19 |

## Plan

- [ ] 1. 🤖 แก้ `next` และ `eslint-config-next` ใน `apps/web/package.json` เป็น 16.4.6 แล้ว `pnpm install` (อัปเดต `pnpm-lock.yaml`)
- [ ] 2. 🤖 `pnpm lint`, `pnpm typecheck`, `pnpm test`, `pnpm build` ต้องผ่าน
- [ ] 3. 🙋 May รัน `pnpm dev` ใหม่ แล้วเปิดเว็บ: login → รายการเตรียมสอบ → ห้องติว (การ์ดโจทย์ + canvas ขึ้น) · ดูว่า Terminal 2 ไม่มีข้อความเตือน security แล้ว
- [ ] 4. 🤖 ติ๊ก checklist: ข้อนี้ และข้อ ⭐ goal 4 (เสร็จแล้วใน #160 · ผ่านบนเครื่อง May 19 พ.ย. #163)
- [ ] 5. 🙋 May ส่งข้อความในกลุ่ม (ร่างให้) ก่อน merge

## Definition of done

- เว็บใช้ Next.js 16.4.6 · lint, typecheck, test, build ผ่านในเครื่องและ CI
- เดินหน้าหลักบนเครื่อง May ได้เหมือนเดิม และ `next dev` ไม่เตือน security
- แจ้งกลุ่มแล้ว

## Decisions

- 2026-11-19 · ทำก่อนซ้อมวิดีโอ · ถ้าพังยังมีเวลาแก้ก่อนอัด 21–22 พ.ย.

## Next step

ขั้น 1: แก้เวอร์ชันใน `apps/web/package.json` แล้ว `pnpm install`

## Waiting on

ไม่มี

## Notes for next time

- …
