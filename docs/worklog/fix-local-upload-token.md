# แก้: ส่งรูป / canvas ตอน login บนเครื่อง (PUT /dev/uploads ได้ 401)

| | |
|---|---|
| Owner | May |
| Branch | `fix/local-upload-token` |
| Checklist item | (ยังไม่มีใน checklist · บั๊กจากผลซ้อม 17 พ.ย. `docs/design/demo-video.md` "ผลซ้อม" · Jam ให้แก้ฝั่งหน้าเว็บ) · เพิ่มเป็นบรรทัดย่อยของ ⭐ demo ขั้น 7 ตอน `/work-done` |
| Status | in progress · 2026-11-17 |

## Plan

สาเหตุ: `APP_ENV=local` ให้ `upload_url` เป็น URL ของ API เอง (`/dev/uploads/…` · demo-room.md §2 A) · `AUTH_REQUIRED=true` ต้องมี token ทุก path · `lib/httpTransport.ts` `PUT` ไป `upload_url` ด้วย `fetch` เปล่า (ตั้งใจสำหรับ signed URL ของ Storage) → 401 · `web-login.md` §2.3 ข้อ 4 บอกว่า "ไม่แนบ กับ URL ที่ไม่ใช่ API" แปลว่า URL ของ API ต้องแนบ · โค้ดยังไม่ทำตาม

- [x] 1. 🤖 spec: `web-login.md` §2.3 ข้อ 4 ชัดขึ้น (`upload_url` ที่ขึ้นต้นด้วย URL ของ API → แนบ · อื่น → ไม่แนบ) + AC ใหม่ · (spec ของ Jam · Jam ให้แก้ฝั่งเว็บ) → 🙋 May ok
- [x] 2. 🤖 test (red) → 🙋 May review · 17 พ.ย. ok (1 red · 3 ผ่านตั้งแต่ต้น = พฤติกรรมเดิมที่ต้องคงไว้)
- [ ] 3. 🤖 แก้ `uploadPhoto` จน test ผ่าน + lint + typecheck
- [ ] 4. 🙋 ลองในเบราว์เซอร์: login → ห้องติว → วาด canvas → ส่งคำตอบ → การ์ด "อ่านได้แบบนี้ ถูกไหม" ขึ้น
- [ ] 5. 🤖 `/work-done`

## Definition of done

- ส่งรูป / canvas ในทางที่ login บนเครื่อง (`APP_ENV=local`, `AUTH_REQUIRED=true`) ได้การ์ดยืนยันลายมือ · `PUT` ไป Storage จริงยังไม่แนบ token · test ผ่าน

## Decisions

- 2026-11-17 · Jam: แก้ฝั่งหน้าเว็บ (ไม่ใช่ยกเว้น `/dev/uploads` ใน API)

## Next step

ขั้น 3: แก้ `uploadPhoto`

## Waiting on

ไม่มี

## Notes for next time

- `UploadPage.tsx` (หน้าอัปโหลดชีท) `PUT` ไป signed URL ของ Storage จริงเสมอ (#140) · ไม่เกี่ยว
