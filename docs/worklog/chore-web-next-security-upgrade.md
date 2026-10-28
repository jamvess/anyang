# อัปเกรด Next.js 16.4.0 → 16.4.3 (ช่องโหว่ความปลอดภัย)

| | |
|---|---|
| Owner | May |
| Branch | `chore/web-next-security-upgrade` |
| Checklist item | ไม่มีข้อตรงใน checklist · `pnpm audit`: next ≤16.4.0 มีช่องโหว่ critical (RCE) และ high (DoS) · แก้ใน ≥16.4.1 |
| Status | in progress · 2026-10-28 |

## Plan

- [x] 1. 🤖 อัปเกรด `next` และ `eslint-config-next` เป็น 16.4.3 (patch ล่าสุดของ 16.4, ออก 23 ต.ค.) · อัปเดต `pnpm-lock.yaml`
- [x] 2. 🤖 รัน `pnpm audit`, lint, typecheck, test, build · build ต้องไม่หยุดด้วย SecurityFatalError อีก
- [ ] 3. 🙋 May ลองเปิดห้องติวในเครื่อง: เปิด API (`cd apps/api` แล้ว `uv run fastapi dev app/main.py`) · เปิดเว็บ (`cd apps/web` แล้ว `pnpm dev`) · เข้า http://localhost:3000 แล้วเข้าห้องติว · พิมพ์ข้อความ 1 ข้อความ · ดูว่าการ์ดความคืบหน้า สมการ และข้อความที่ไหลออกมายังเหมือนเดิม
- [ ] 4. 🤖 ดู Vercel preview ของ PR ว่า build ผ่าน

## Definition of done

- `pnpm audit` ไม่เหลือช่องโหว่ของ `next` · lint, typecheck, test, build ผ่านโดยไม่ต้องรันซ้ำ · ห้องติวในเครื่องทำงานเหมือนเดิม · Vercel preview ผ่าน

## Decisions

- 2026-10-28 · ใช้ 16.4.3 ไม่ข้ามไป minor ใหม่ · แก้ช่องโหว่โดยเปลี่ยนน้อยที่สุดก่อน demo 30 ต.ค.
- 2026-10-28 · `pnpm audit` ยังเหลือ undici <8.12.2 ผ่าน `jsdom` (4 high, 4 moderate) · เป็น devDependency ที่ใช้แค่ตอนรัน test ไม่ถูกส่งไปกับเว็บ · ไม่แก้ใน PR นี้ เสนอแยก

## Next step

ขั้น 3: May ลองห้องติวในเครื่องตามขั้นในแผน

## Waiting on

ไม่มี

## Notes for next time

- Next.js หยุดคำสั่งครั้งแรกเพื่อแจ้ง advisory แล้วรันซ้ำผ่าน · อย่าเข้าใจว่า build พัง
