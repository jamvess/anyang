# Canvas ใต้การ์ดโจทย์ สำหรับเขียนคำตอบ

| | |
|---|---|
| Owner | Jam |
| Branch | `feat/answer-canvas` |
| Checklist item | เดโม่ห้องติวที่ใช้ได้จริงในเครื่อง ให้อาจารย์ดูก่อนทำต่อ (อาจารย์ขอ 9 พ.ย. · เพิ่มเอง) · ส่วน "canvas ใต้การ์ดโจทย์" และ "อัดวิดีโอสำรองหลังมี canvas" |
| Status | in progress · 2026-11-09 |

ตกลงกับ Jam (9 พ.ย.): โจทย์มาเมื่อไหร่ canvas ขึ้นใต้การ์ดโจทย์ทันที (ทั้งโจทย์เปิดห้องและข้อต่อไป) · แชทปกติไม่มี canvas · เขียนด้วยเมาส์ / Apple Pencil / นิ้ว (ถ้าใช้ปากกา ไม่วาดตามฝ่ามือ) · เครื่องมือ: ปากกา, ยางลบ, undo, ล้าง, ใส่รูป (เป็นพื้นหลังแล้วเขียนทับ), ส่งคำตอบ · ส่ง = PNG ผ่านทางเดิมของรูป (`/uploads` → `/messages` → การ์ดยืนยันลายมือ → ✓/✗) · พิมพ์และปุ่ม 📷 ยังใช้ได้ · API ไม่ต้องแก้

## Plan

- [x] 1. 🤖 `/spec-feature` → `specs/features/tutor/answer-canvas.md` (TM-06 · ดีไซน์ชั่วคราว: หน้าตาและ flow ให้ May ตัดสินย้อนหลังใน §10) → 🙋 Jam ok
- [x] 2. 🤖 `/spec-to-tests` (Vitest · ตรรกะของเส้นเป็น pure function · mock `getContext` และ `toBlob` เอง ไม่เพิ่ม dependency) → 🙋 Jam review test
- [x] 3. 🤖 `/implement-feature` (`components/chat/AnswerCanvas.tsx` + `canvasStrokes.ts` · ข้อความไทยใน `strings.ts`)
- [ ] 4. 🙋 ลองบนคอม (เมาส์) · iPad ทีหลัง (Jam 9 พ.ย.: ตอนนี้ลองแค่คอม)
- [ ] 5. 🙋 ซ้อม loop เดโม่ทั้งหมดแล้วอัดวิดีโอสำรอง
- [ ] 6. 🤖 `/work-done` + ข้อความกลุ่มถึง May (หน้าจอของ May · ดีไซน์ชั่วคราว)

## Definition of done

- โจทย์ทุกข้อมี canvas ใต้การ์ด · เขียนด้วยเมาส์ได้ (ลองบนคอม) · Apple Pencil ผ่าน test ของตรรกะ (ยังไม่ได้ลองบน iPad) · ใส่รูปเป็นพื้นหลังได้ · ส่งแล้วได้การ์ดยืนยันลายมือและผลตรวจจริงในเดโม่
- test ของเว็บผ่าน (lint, typecheck, test, build) · test เดิมไม่เปลี่ยน
- มีวิดีโอสำรองของ loop เดโม่ที่ใช้ canvas

## Decisions

- 2026-11-09 · Jam ลองรอบ 2: คุยไปสักพัก canvas เลื่อนพ้นจอ และ tutor พิมพ์ `**` ดิบ → Jam ok: canvas อยู่ท้ายแชทพร้อมหัวโจทย์ สิ่งที่เขียนไม่หายจนกว่าจะเปลี่ยนโจทย์ (answer-canvas §2 B) · `MessageText` ตัดคู่ `**` (§2 C · โค้ดของ May) · แก้ test AC-16 ที่ review แล้ว 1 บรรทัด (`rac` หลุด backslash ตอนเขียนไฟล์ผ่าน shell)
- 2026-11-09 · Jam: ใช้กฎ 2 ขั้นไปก่อน · แนวคิด "ให้ LLM ตัดสินว่าวิธีทำพอหรือยัง เพราะแต่ละโจทย์ยาวไม่เท่ากัน" จดไว้ใน demo-room §10 ข้อ 3 และ learning-model §8 (ยังไม่ทำ)
- 2026-11-09 · Jam ลอง canvas บนคอม: เขียน `(x²−7²) = (x−7)(x+7)` บรรทัดเดียวแล้วโดนว่าขาดวิธีทำ และอยากได้ canvas ใหม่เมื่อ tutor ขอวิธีทำ → Jam ok: นับเป็นขั้น (บรรทัด + `=` กลางบรรทัด · `working_steps`) และส่งการ์ดโจทย์เดิมซ้ำเมื่อขาดวิธีทำ (demo-room §2 I ข้อ 5–6) · แก้ test AC-30 ที่ review แล้ว (มี `problem` ก่อน `done`) · ทำใน PR นี้ แตะ `apps/api/`
- 2026-11-09 · canvas เป็น `role="form"` ไม่ใช่ region (Jam เลือกข้อ 1): test ของการ์ดโจทย์ใน `ChatRoomStream.test.tsx` (ของ May) นับทุก region · แก้ test ของเรา 4 จุดและ AC-1 ใน spec
- 2026-11-09 · ลองแค่บนคอมก่อน ไม่ต้องลอง iPad ใน PR นี้ (Jam) · ตรรกะ Apple Pencil (pressure, ไม่วาดตามฝ่ามือ) ยังทำและ test ด้วย pure function
- 2026-11-09 · canvas ผูกกับโจทย์ ไม่ใช่ปุ่มใน composer (Jam) · PR แยกจากเดโม่ (#115 merge แล้ว)

## Next step

ขั้น 4 (🙋 Jam): ลองบนคอมด้วยเมาส์ตามขั้นตอนที่ Claude เขียนให้

## Waiting on

- May: ตัดสินหน้าตาและ flow ของ canvas ย้อนหลัง (`roles.md` "ตัดสินใจเรื่อง" · หน้าจอและ flow)

## Notes for next time

- web test suite ล้มแบบ flaky 2 ครั้ง (ครั้งละหลายตัว) ตอนเครื่องทำงานหนัก · รันซ้ำผ่านทุกครั้ง (4/4) · CI จะเป็นตัวยืนยัน

- implement: red → green 2 รอบ · (1) ตรรกะ 12/12 และ component 9/9 เขียวรอบแรก (2) ต่อเข้าห้องแล้ว test การ์ดโจทย์ของ May 2 ตัวล้มเพราะนับ region → เปลี่ยนเป็น `role="form"` · eslint จับการอ่าน ref ระหว่าง render (`react-hooks/refs`) แก้แล้ว · `ChatRoomOcr` ล้มครั้งเดียวตอนเครื่องช้า (timeout) รันซ้ำ 3 รอบผ่าน

- test: mock ของ canvas และ PointerEvent อยู่ใน `tests/helpers/fakeCanvas.ts` · หน้าตาโค้ดที่ test กำหนด: `canvasStrokes.ts` (emptyScene, accepts, strokeWidth, start/extend/endStroke, undo, clear, setBackground, isEmpty, canUndo, containRect, drawScene(base, layer, scene, size)) · `AnswerCanvas` props `onSend`, `disabled`, `maxImageMb`, `loadImage?` · ไม่มี prettier ในเครื่อง (ใช้ eslint)

- canvas ส่ง `{text: null, image: File}` ผ่าน `send()` ของ `ChatRoom` แบบเดียวกับ Composer · `httpTransport.uploadPhoto` อัปโหลดเอง
