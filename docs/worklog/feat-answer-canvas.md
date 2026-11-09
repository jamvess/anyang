# Canvas ใต้การ์ดโจทย์ สำหรับเขียนคำตอบ

| | |
|---|---|
| Owner | Jam |
| Branch | `feat/answer-canvas` |
| Checklist item | เดโม่ห้องติวที่ใช้ได้จริงในเครื่อง ให้อาจารย์ดูก่อนทำต่อ (อาจารย์ขอ 9 พ.ย. · เพิ่มเอง) · ส่วน "canvas ใต้การ์ดโจทย์" และ "อัดวิดีโอสำรองหลังมี canvas" |
| Status | in progress · 2026-11-09 |

ตกลงกับ Jam (9 พ.ย.): โจทย์มาเมื่อไหร่ canvas ขึ้นใต้การ์ดโจทย์ทันที (ทั้งโจทย์เปิดห้องและข้อต่อไป) · แชทปกติไม่มี canvas · เขียนด้วยเมาส์ / Apple Pencil / นิ้ว (ถ้าใช้ปากกา ไม่วาดตามฝ่ามือ) · เครื่องมือ: ปากกา, ยางลบ, undo, ล้าง, ใส่รูป (เป็นพื้นหลังแล้วเขียนทับ), ส่งคำตอบ · ส่ง = PNG ผ่านทางเดิมของรูป (`/uploads` → `/messages` → การ์ดยืนยันลายมือ → ✓/✗) · พิมพ์และปุ่ม 📷 ยังใช้ได้ · API ไม่ต้องแก้

## Plan

- [ ] 1. 🤖 `/spec-feature` → `specs/features/tutor/answer-canvas.md` (TM-06 · ดีไซน์ชั่วคราว: หน้าตาและ flow ให้ May ตัดสินย้อนหลังใน §10) → 🙋 Jam ok
- [ ] 2. 🤖 `/spec-to-tests` (Vitest · ตรรกะของเส้นเป็น pure function · mock `getContext` และ `toBlob` เอง ไม่เพิ่ม dependency) → 🙋 Jam review test
- [ ] 3. 🤖 `/implement-feature` (`components/chat/AnswerCanvas.tsx` + `canvasStrokes.ts` · ข้อความไทยใน `strings.ts`)
- [ ] 4. 🙋 ลองบนคอม (เมาส์) และ iPad (Apple Pencil + นิ้ว) · Claude เขียนวิธีเปิดผ่าน Wi-Fi ให้ (API/เว็บฟังที่ IP ของโน้ตบุ๊ก + CORS)
- [ ] 5. 🙋 ซ้อม loop เดโม่ทั้งหมดแล้วอัดวิดีโอสำรอง
- [ ] 6. 🤖 `/work-done` + ข้อความกลุ่มถึง May (หน้าจอของ May · ดีไซน์ชั่วคราว)

## Definition of done

- โจทย์ทุกข้อมี canvas ใต้การ์ด · เขียนด้วยเมาส์และ Apple Pencil ได้ · ใส่รูปเป็นพื้นหลังได้ · ส่งแล้วได้การ์ดยืนยันลายมือและผลตรวจจริงในเดโม่
- test ของเว็บผ่าน (lint, typecheck, test, build) · test เดิมไม่เปลี่ยน
- มีวิดีโอสำรองของ loop เดโม่ที่ใช้ canvas

## Decisions

- 2026-11-09 · canvas ผูกกับโจทย์ ไม่ใช่ปุ่มใน composer (Jam) · PR แยกจากเดโม่ (#115 merge แล้ว)

## Next step

ขั้น 1: เขียน `specs/features/tutor/answer-canvas.md` ด้วย `/spec-feature`

## Waiting on

- May: ตัดสินหน้าตาและ flow ของ canvas ย้อนหลัง (`roles.md` "ตัดสินใจเรื่อง" · หน้าจอและ flow)

## Notes for next time

- canvas ส่ง `{text: null, image: File}` ผ่าน `send()` ของ `ChatRoom` แบบเดียวกับ Composer · `httpTransport.uploadPhoto` อัปโหลดเอง
