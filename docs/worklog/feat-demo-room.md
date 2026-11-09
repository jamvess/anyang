# เดโม่ห้องติวที่ใช้ได้จริงในเครื่อง (ให้อาจารย์ดู)

| | |
|---|---|
| Owner | Jam |
| Branch | `feat/demo-room` |
| Checklist item | ไม่มีในรายการ · อาจารย์ขอดูห้องติวที่ใช้ได้จริงก่อนทำต่อ (9 พ.ย.) · เกี่ยวกับ "เตรียมลำดับหน้าจอสำหรับ demo รวม" (May) และ "เตรียม staging สำหรับ demo รวม" (Junior) · เสนอเพิ่มเป็นข้อใหม่ของ Jam ตอน `/work-done` |
| Status | in progress · 2026-11-09 |

Loop ที่อาจารย์จะเห็น (รันในเครื่อง Jam · AI จริงบน Vertex): เปิดห้อง → tutor ให้โจทย์ → ถามในแชทได้ (tutor รู้โจทย์) → ถ่ายรูปวิธีทำส่ง → การ์ด "อ่านได้แบบนี้ ถูกไหม" → ยืนยัน → ✓/✗ + tutor อธิบายทันที → โจทย์ข้อถัดไป → วน 4–5 ข้อ

ทุกอย่างใหม่เปิดเฉพาะ `APP_ENV=local` · staging และพฤติกรรมเดิมไม่เปลี่ยน · ไม่ทำ: เสียง, TTS, buddy, login, persona, ตรวจคำตอบที่พิมพ์

## Plan

- [x] 1. 🤖 spec 2 ไฟล์: `specs/features/tutor/demo-room.md` (loop + ขอบเขต `APP_ENV=local` + ส่วน D การ์ดความคืบหน้า) และ `specs/features/planner/bkt-mastery.md` (BKT, ระดับ, ความพร้อม) → 🙋 Jam ok + ตอบ open questions
- [ ] 2. 🤖 BKT ตาม spec flow: `/spec-to-tests` bkt-mastery → 🙋 Jam review test → `/implement-feature` (`app/domain/bkt.py`)
- [ ] 3. 🤖 อัปโหลดรูปในเครื่อง (demo-room §2 A) + test
- [ ] 4. 🤖 ชุดโจทย์ 5 ข้อ + โจทย์ถัดไป + การ์ดความคืบหน้าจาก BKT (demo-room §2 B, D) + test
- [ ] 5. 🤖 `tutor_reply/v2` รู้โจทย์ (demo-room §2 C) · 🙋 Jam ดู prompt · smoke กับ Vertex
- [ ] 6. 🙋 ลองครบ loop ในเบราว์เซอร์ (`pnpm dev` + `uv run fastapi dev` · Claude เขียนขั้นตอนให้) ด้วยรูปจากมือถือและจาก `evals/handwriting/raw/` · ซ้อม · อัดวิดีโอสำรอง
- [ ] 7. 🤖 `/work-done` + ข้อความกลุ่ม (แตะ upload ของ Junior · `config/ai.yaml` ขึ้น `tutor_reply` v2)

## Definition of done

- ในเครื่อง Jam: วน loop ข้างบนได้อย่างน้อย 4 ข้อติดกันในเบราว์เซอร์โดยไม่มี stub (ไม่มี `X-Stub` ใน response ของห้อง ยกเว้นเปิดห้อง/progress card)
- `APP_ENV` อื่นทำงานเหมือนเดิม (test เดิมผ่านทั้งหมด)
- การ์ดความคืบหน้าหลังแต่ละข้อแสดงระดับและความพร้อม % ที่คิดจาก BKT จริง
- มีวิดีโอสำรองของ loop

## Decisions

- 2026-11-09 · spec ok ทั้งหมด (Jam): ความพร้อมนับหัวข้อที่ยังไม่เริ่มเป็น 0 (learning-model v1.4) · mode normal · `tutor_reply/v2` ทุก env · ตอบผิดแล้วไปข้อต่อไป (เดโม่)
- 2026-11-09 · Jam ok ให้เพิ่ม BKT: mastery จริงในการ์ดความคืบหน้าของเดโม่ (spec แยก `bkt-mastery.md` · ไม่มี planner, spaced review, Park)
- 2026-11-09 · Jam ok: เดโม่ในเครื่อง (ไม่รอ staging) · เอาข้อ 4 (tutor รู้โจทย์) · โจทย์จาก `evals/` (MTH10101) · ไม่ต้องลงรายละเอียดความถูกต้องใน spec

## Next step

ขั้น 2: `/spec-to-tests specs/features/planner/bkt-mastery.md` → `apps/api/tests/unit/test_bkt.py`

## Waiting on

ไม่มี (staging สำหรับให้อาจารย์เปิดลิงก์เอง: Junior env + Storage + auth, May หน้า login · ไม่ขวางงานนี้)

## Notes for next time

- เว็บไม่ต้องแก้: `uploadPhoto` ใน `apps/web/lib/httpTransport.ts` จะ `PUT` ไฟล์เองเมื่อ response ของ `/uploads` ไม่มี `X-Stub` · CORS อนุญาต `PUT` + `Content-Type` แล้ว (`app/cors.py`)
