# ตอบด้วยเสียงในห้องติว (S18)

| | |
|---|---|
| Owner | May |
| Branch | `feat/voice-input` |
| Checklist item | ไม่มีข้อตรงใน checklist · TM-07 (Should), TM-06 · UC-03 A3, UC-04 A3 · wireframe S18 |
| Status | in progress · 2026-10-28 |

## Plan

- [ ] 1. 🤖 `/spec-feature` เขียน `specs/features/tutor/voice-input.md` จาก TM-07, UC-03 A3, UC-04 A3, ai-orchestration §2.2.5 (กดค้าง ≤ 60 วินาที, ไม่ auto-send), wireframe S18 (`VOICEDRAFT`), api.md (`/uploads`, `/transcribe`), `config/ai.yaml` → `guards.max_audio_seconds` · ใส่คำถามเรื่องที่ api.md ยังไม่กำหนด
- [ ] 2. 🙋 May review spec และตอบคำถามเรื่อง UI (ถามเป็นตัวเลือก)
- [ ] 3. 🤖 ถาม Junior เรื่อง api.md: `limits` ยังไม่มี `max_audio_seconds` · body/response ของ `/transcribe` · ข้อความที่มาจากเสียงส่ง `input_mode: voice` ยังไง
- [ ] 4. 🤖 `/spec-to-tests` · ต้องแดงก่อน · จำลองไมค์ด้วย fake `MediaRecorder` (jsdom ไม่มีไมค์)
- [ ] 5. 🙋 May review test
- [ ] 6. 🤖 `/implement-feature` จน test เขียว
- [ ] 7. 🙋 May ลองพูดจริงในเบราว์เซอร์ (Chrome ขอสิทธิ์ไมค์) บนหน้าทดลองชั่วคราวที่ไม่ commit

## Definition of done

- AC ทุกข้อใน `voice-input.md` มี test และผ่าน · lint, typecheck, test, build ผ่าน
- กดค้างปุ่มไมค์แล้วอัดได้ ปล่อยแล้วข้อความขึ้นในช่องพิมพ์ ไม่ส่งเอง · หยุดเองเมื่อครบเวลาจาก API · ไม่ให้สิทธิ์ไมค์แล้วมีข้อความบอก
- คำถาม api.md ส่งถึง Junior แล้ว

## Decisions

- 2026-10-28 · ไม่ทำ demo แล้ว (May) · เลือกงานนี้เพราะเป็น feature ใหญ่ที่เหลือของห้องติว

## Next step

ขั้น 1: รัน `/spec-feature` สำหรับ TM-07 (ตอบด้วยเสียง S18)

## Waiting on

ไม่มี

## Notes for next time

- `guards.max_audio_seconds: 60` อยู่ใน `config/ai.yaml` แต่ `Limits` ใน API มีแค่ `max_message_chars`, `max_image_mb`
- jsdom ไม่มี `MediaRecorder` และ `getUserMedia` · test ต้อง stub
