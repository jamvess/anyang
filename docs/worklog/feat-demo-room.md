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
- [x] 2. 🤖 BKT ตาม spec flow: `/spec-to-tests` bkt-mastery → 🙋 Jam review test → `/implement-feature` (`app/domain/bkt.py`)
- [x] 3. 🤖 อัปโหลดรูปในเครื่อง (demo-room §2 A) + test
- [x] 4. 🤖 ชุดโจทย์ 5 ข้อ + โจทย์ถัดไป + การ์ดความคืบหน้าจาก BKT (demo-room §2 B, D) + test
- [ ] 5. 🤖 `tutor_reply/v2` รู้โจทย์ (demo-room §2 C) · 🙋 Jam ดู prompt · smoke กับ Vertex
- [ ] 6. 🙋 ลองครบ loop ในเบราว์เซอร์ (`pnpm dev` + `uv run fastapi dev` · Claude เขียนขั้นตอนให้) ด้วยรูปจากมือถือและจาก `evals/handwriting/raw/` · ซ้อม · อัดวิดีโอสำรอง
- [ ] 7. 🤖 `/work-done` + ข้อความกลุ่ม (แตะ upload ของ Junior · `config/ai.yaml` ขึ้น `tutor_reply` v2)

## Definition of done

- ในเครื่อง Jam: วน loop ข้างบนได้อย่างน้อย 4 ข้อติดกันในเบราว์เซอร์โดยไม่มี stub (ไม่มี `X-Stub` ใน response ของห้อง ยกเว้นเปิดห้อง/progress card)
- `APP_ENV` อื่นทำงานเหมือนเดิม (test เดิมผ่านทั้งหมด)
- การ์ดความคืบหน้าหลังแต่ละข้อแสดงระดับและความพร้อม % ที่คิดจาก BKT จริง
- มีวิดีโอสำรองของ loop

## Decisions

- 2026-11-09 · Jam เลือกข้อ 1: gateway รองรับ `defaults` ใน frontmatter แทนการแก้ test เดิม 22 ตัวที่เรียก `tutor_reply` ด้วย `{message}` อย่างเดียว · (ข้อ 2 purpose ใหม่ / ข้อ 3 ตัดส่วน C ไม่เลือก)
- 2026-11-09 · spec ok ทั้งหมด (Jam): ความพร้อมนับหัวข้อที่ยังไม่เริ่มเป็น 0 (learning-model v1.4) · mode normal · `tutor_reply/v2` ทุก env · ตอบผิดแล้วไปข้อต่อไป (เดโม่)
- 2026-11-09 · Jam ok ให้เพิ่ม BKT: mastery จริงในการ์ดความคืบหน้าของเดโม่ (spec แยก `bkt-mastery.md` · ไม่มี planner, spaced review, Park)
- 2026-11-09 · Jam ok: เดโม่ในเครื่อง (ไม่รอ staging) · เอาข้อ 4 (tutor รู้โจทย์) · โจทย์จาก `evals/` (MTH10101) · ไม่ต้องลงรายละเอียดความถูกต้องใน spec

## Next step

ขั้น 5 (ต่อ): Jam ตัดสินเรื่อง `test_ai_gateway_stream.py:205` (`prompt_version == "v1"` ล้มเพราะ `tutor_reply` ขึ้น v2) · ดู prompt `tutor_reply/v2` · แล้ว smoke 3–4 ข้อความกับ Vertex

## Waiting on

ไม่มี (staging สำหรับให้อาจารย์เปิดลิงก์เอง: Junior env + Storage + auth, May หน้า login · ไม่ขวางงานนี้)

## Notes for next time

- implement ขั้น 3–5: red → green 2 รอบ · (1) 17/18 test เดโม่เขียว (AC-8 รอ prompt v2) (2) ขึ้น `tutor_reply` v2 แล้ว test เดิม 22 ตัวล้ม `missing inputs: ['problem']` → เพิ่ม `defaults` ใน gateway (Jam ข้อ 1) เหลือ 1 ตัวที่ล้มเพราะเขียน `prompt_version == "v1"` ไว้ตรงๆ
- `/dev/uploads` เป็น `include_in_schema=False` จึงไม่อยู่ใน `/docs` และ `test_api_md_endpoints` ไม่เห็น

- demo-room test: เขียน test ของขั้น 3–5 รวมไฟล์เดียว ให้ Jam review รอบเดียว · หน้าตาโค้ดที่ test กำหนด: `app.services.dev_uploads` (`get_local_mode`, `get_local_upload_dir` เป็น dependency) · `app.services.demo_room` (`DEMO_PROBLEMS`, `DEMO_TOPICS`, `DemoRoomState`) · `PendingProblem` เพิ่ม `text_latex`, `difficulty`, `topic_id` · เปิดห้องใน local รีเซ็ต state ของ session (การ์ดเริ่มที่ยังไม่เริ่มทุกหัวข้อ · AC-10)

- bkt implement: red → green 1 รอบ (32 กรณีเขียวในรอบแรก) · ruff จับเครื่องหมาย `×` ใน docstring (RUF002) เปลี่ยนเป็น `*`

- bkt test: `ReadinessTopic` มี field `attempts` เพิ่มจาก spec §3 เพื่อให้ `readiness()` รู้ว่าหัวข้อยังไม่เริ่ม (AC-10b) · ทุกฟังก์ชันรับ `LearningConfig` ยกเว้น `update_mastery` ที่รับ `BktConfig` ตาม spec §3 · ใส่ mode `final` ใน AC-6 ด้วย (★★ final = `two_star_final_difficulty` ตาม §2 ข้อ 3)

- เว็บไม่ต้องแก้: `uploadPhoto` ใน `apps/web/lib/httpTransport.ts` จะ `PUT` ไฟล์เองเมื่อ response ของ `/uploads` ไม่มี `X-Stub` · CORS อนุญาต `PUT` + `Content-Type` แล้ว (`app/cors.py`)
