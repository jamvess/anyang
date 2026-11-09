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

- [ ] 1. 🤖 spec สั้น `specs/features/tutor/demo-room.md` (checklist ของ loop + ขอบเขต `APP_ENV=local`) → 🙋 Jam ok
- [ ] 2. 🤖 อัปโหลดรูปในเครื่อง: `APP_ENV=local` → `/uploads` คืน URL ของ API เอง (`PUT /dev/uploads/{path}`) ไม่มี `X-Stub` · เก็บไฟล์ในโฟลเดอร์ local (gitignore) · `ImageStore` อ่านจากโฟลเดอร์นั้น · test สั้น
- [ ] 3. 🤖 ชุดโจทย์เดโม่ 5 ข้อ (ข้อแรก = `p1` ของ session_start) · ตรวจเสร็จแล้ว stream event `problem` ข้อถัดไปต่อท้ายคำอธิบาย · ครบแล้ววนกลับ · 🙋 Jam เลือกโจทย์จาก `evals/answers/labels.jsonl`
- [ ] 4. 🤖 tutor รู้โจทย์ปัจจุบัน: `tutor_reply/v2` + input `problem` (โจทย์ ไม่มีเฉลย · AM-13) · 🙋 Jam ดู prompt · smoke 3–4 ข้อความ
- [ ] 5. 🙋 ลองครบ loop ในเบราว์เซอร์ (`pnpm dev` + `uv run fastapi dev` · Claude เขียนขั้นตอนให้) ด้วยรูปจากมือถือและจาก `evals/handwriting/raw/` · ซ้อม · อัดวิดีโอสำรอง
- [ ] 6. 🤖 `/work-done` + ข้อความกลุ่ม (แตะ upload ของ Junior และ `config/ai.yaml` ถ้าขึ้น `tutor_reply` v2)

## Definition of done

- ในเครื่อง Jam: วน loop ข้างบนได้อย่างน้อย 4 ข้อติดกันในเบราว์เซอร์โดยไม่มี stub (ไม่มี `X-Stub` ใน response ของห้อง ยกเว้นเปิดห้อง/progress card)
- `APP_ENV` อื่นทำงานเหมือนเดิม (test เดิมผ่านทั้งหมด)
- มีวิดีโอสำรองของ loop

## Decisions

- 2026-11-09 · Jam ok: เดโม่ในเครื่อง (ไม่รอ staging) · เอาข้อ 4 (tutor รู้โจทย์) · โจทย์จาก `evals/` (MTH10101) · ไม่ต้องลงรายละเอียดความถูกต้องใน spec

## Next step

ขั้น 1: เขียน `specs/features/tutor/demo-room.md` แล้วให้ Jam ok

## Waiting on

ไม่มี (staging สำหรับให้อาจารย์เปิดลิงก์เอง: Junior env + Storage + auth, May หน้า login · ไม่ขวางงานนี้)

## Notes for next time

- เว็บไม่ต้องแก้: `uploadPhoto` ใน `apps/web/lib/httpTransport.ts` จะ `PUT` ไฟล์เองเมื่อ response ของ `/uploads` ไม่มี `X-Stub` · CORS อนุญาต `PUT` + `Content-Type` แล้ว (`app/cors.py`)
