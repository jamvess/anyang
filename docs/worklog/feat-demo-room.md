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
- [x] 5. 🤖 `tutor_reply/v2` รู้โจทย์ (demo-room §2 C) · 🙋 Jam ดู prompt · smoke กับ Vertex
- [x] 5b. 🤖 (เพิ่ม 9 พ.ย. หลัง Jam ลองในเบราว์เซอร์) tutor จำบทสนทนา + จอไม่มีประวัติปลอมของ stub (demo-room §2 E) · test → Jam review → implement · smoke กับ Vertex
- [x] 5c. 🤖 (เพิ่ม 9 พ.ย. หลัง Jam ลองรอบ 2) tutor ทักก่อนจาก facts (`open_session`) + พิมพ์คำตอบแล้วตรวจ (`typed_answer`) (demo-room §2 F, G) · test → Jam review → implement · smoke กับ Vertex
- [ ] 6. 🙋 ลองครบ loop ในเบราว์เซอร์ (`pnpm dev` + `uv run fastapi dev` · Claude เขียนขั้นตอนให้) ด้วยรูปจากมือถือและจาก `evals/handwriting/raw/` · ซ้อม · อัดวิดีโอสำรอง
- [ ] 7. 🤖 `/work-done` + ข้อความกลุ่ม (แตะ upload ของ Junior · `config/ai.yaml` ขึ้น `tutor_reply` v2)

## Definition of done

- ในเครื่อง Jam: วน loop ข้างบนได้อย่างน้อย 4 ข้อติดกันในเบราว์เซอร์โดยไม่มี stub (ไม่มี `X-Stub` ใน response ของห้อง ยกเว้นเปิดห้อง/progress card)
- `APP_ENV` อื่นทำงานเหมือนเดิม (test เดิมผ่านทั้งหมด)
- การ์ดความคืบหน้าหลังแต่ละข้อแสดงระดับและความพร้อม % ที่คิดจาก BKT จริง
- มีวิดีโอสำรองของ loop

## Decisions

- 2026-11-09 · Jam ลองรอบ 2: (1) ห้องเปิดมาโล่ง ไม่มีคำทัก (2) พิมพ์คำตอบต้องตรวจ และ tutor ต้องมี reaction ทั้งถูกและผิด → ส่วน F, G · Jam เลือก (ก) call เดียว `typed_answer` แทน `route_intent` + `normalize_math` ชั่วคราว · `open_session` เป็น purpose ใหม่ (main · stream)
- 2026-11-09 · Jam ok แก้ test AC-25 1 บรรทัด: เทียบข้อความที่ต่อกันแล้ว เพราะ fake ส่ง string ทีละคำ (test ผิดเอง ไม่ใช่โค้ด)
- 2026-11-09 · Jam ลองในเบราว์เซอร์แล้วถามว่าทำไม tutor ไม่ตอบตรงคำถาม: ประวัติบนจอเป็นตัวอย่างของ stub (`room.json`) ที่ tutor ไม่เคยเห็น และ `tutor_reply` ได้แค่ข้อความล่าสุด → Jam ให้ทำทั้ง 2 อย่าง "ให้เสมือนจริงที่สุด": ซ่อนประวัติปลอมใน local + tutor จำ `session.context_recent_turns` turns ล่าสุด (layer 9 · ใน memory)
- 2026-11-09 · Jam ok: `test_ai_gateway_stream.py:205` อ่าน version ของ `tutor_reply` จาก config แทนการเขียน `"v1"` ไว้ตรงๆ (แก้ test ที่ review แล้ว 1 บรรทัด · test ยังเช็คเรื่องเดิม)
- 2026-11-09 · Jam เลือกข้อ 1: gateway รองรับ `defaults` ใน frontmatter แทนการแก้ test เดิม 22 ตัวที่เรียก `tutor_reply` ด้วย `{message}` อย่างเดียว · (ข้อ 2 purpose ใหม่ / ข้อ 3 ตัดส่วน C ไม่เลือก)
- 2026-11-09 · spec ok ทั้งหมด (Jam): ความพร้อมนับหัวข้อที่ยังไม่เริ่มเป็น 0 (learning-model v1.4) · mode normal · `tutor_reply/v2` ทุก env · ตอบผิดแล้วไปข้อต่อไป (เดโม่)
- 2026-11-09 · Jam ok ให้เพิ่ม BKT: mastery จริงในการ์ดความคืบหน้าของเดโม่ (spec แยก `bkt-mastery.md` · ไม่มี planner, spaced review, Park)
- 2026-11-09 · Jam ok: เดโม่ในเครื่อง (ไม่รอ staging) · เอาข้อ 4 (tutor รู้โจทย์) · โจทย์จาก `evals/` (MTH10101) · ไม่ต้องลงรายละเอียดความถูกต้องใน spec

## Next step

ขั้น 6 (🙋 Jam): เปิด API (`APP_ENV=local AI_PROVIDER=live AUTH_REQUIRED=false uv run fastapi dev app/main.py`) + เว็บ (`pnpm dev`) แล้วเปิด http://localhost:3000/preps/00000000-0000-4000-8000-000000000001/room · วน 4–5 ข้อด้วยรูปจาก `evals/handwriting/raw/` และจากมือถือ · อัดวิดีโอสำรอง

## Waiting on

ไม่มี (staging สำหรับให้อาจารย์เปิดลิงก์เอง: Junior env + Storage + auth, May หน้า login · ไม่ขวางงานนี้)

## Notes for next time

- ส่วน F, G: red → green 2 รอบ · (1) 3 แถวของ AC-25 ล้มเพราะ test เทียบ token ผิด (2) ตัวอย่างใน `typed_answer/v1` ใช้ `(x-7)(x+7)` ซึ่งเป็นเฉลยของ p1 · test "ไม่มีเฉลยใน prompt" จับได้ → เปลี่ยนตัวอย่างเป็น $x^2-9$
- ห้องเปิดมาโล่งหลังส่วน E: เว็บถาม `/sessions/active` ก่อน · stub บอกว่ามี session ค้าง เว็บจึงโหลดประวัติ (ว่าง) แทนเปิด session ใหม่ → local ตอบ 404 `no_active_session`
- smoke F, G กับ Vertex: เปิดห้อง 8.8 s · tutor ทัก "เหลือ 5 วัน · เริ่มที่การแยกตัวประกอบเพราะเป็นพื้นฐานของลิมิตและอนุพันธ์ · ลองข้อบนการ์ด" (ยาวกว่า 2–3 ประโยคที่สั่ง) · "ไม่แน่ใจ" → ไม่ตรวจ tutor ใบ้ · "7" → ไม่ตรวจ (ตัวแยกรู้ว่าตอบคำถามย่อย) tutor พาต่อ · "(x-7)(x+7)" → ✓ ชม → การ์ด 14% → ข้อ 2 · "ได้ 2" → ✗ อธิบายวิธีจนได้ 4 → ลิมิต weak → ข้อ 3 · "4" (สคริปต์ตั้งใจตอบข้อ 2 แต่ตอนนั้นเป็นข้อ 3 แล้ว) → ✗ อธิบาย product rule → อนุพันธ์ weak
- เวลาพิมพ์คำตอบ: ครั้งแรก 29.8 s (เปิด `typed_answer` + SymPy worker + classifier ครั้งแรก) · ต่อจากนั้น 5.9–9.2 s · ช้ากว่ายืนยันรูป (3.5 s) เพราะมี `typed_answer` เพิ่ม 1 call · **ก่อนเดโม่ต้อง warm-up 1 รอบ**

- ส่วน E: red → green 1 รอบ (8 test ใหม่เขียวในรอบแรก) · test AC-14 ที่ผมเขียนผิดเอง (อัปโหลดใต้ session หนึ่งแล้วส่งอีก session) แก้ก่อน commit test
- smoke บทสนทนากับ Vertex: จอไม่มีประวัติปลอม · "ฉันไม่แน่ใจ" → อธิบาย $x^2-49$ แล้วถาม "เลขอะไรคูณตัวเองได้ 49" · "7" → "ถูกต้อง $7^2$" แล้วพาต่อ (ก่อนแก้ tutor ไม่รู้ว่า 7 คืออะไร) · พิมพ์ "(x-7)(x+7) ใช่ไหม" → ชมและอธิบาย · "แล้ว x^2+49 ล่ะ" → แยกไม่ได้บนจำนวนจริง (ตอบตรง) · ข้อความแรก 17.2 s (เปิดครั้งแรก) ต่อจากนั้น 1.4–1.9 s
- ข้อจำกัดที่เห็นใน smoke: (1) พิมพ์คำตอบที่ถูกแล้ว tutor ชมและชวน "ลุยข้อถัดไป" แต่ไม่มีโจทย์ใหม่และไม่นับ mastery เพราะยังไม่ตรวจคำตอบที่พิมพ์ (`normalize_math` · นอก scope) · เดโม่ต้องส่งรูปเพื่อไปข้อต่อไป (2) model ใช้ `**ตัวหนา**` 1 ครั้งทั้งที่ prompt ห้าม Markdown

- smoke ครบ loop ผ่าน API กับ Vertex (สคริปต์ใน scratchpad · อัปโหลดลง temp ไม่ใช่ repo): เปิดห้อง → การ์ด 3 หัวข้อยังไม่เริ่ม 0% · ถาม "ข้อนี้เริ่มยังไงดี" → tutor รู้ว่าเป็น $x^2-49$ บอกสูตรผลต่างกำลังสองและขั้นแรก · "บอกคำตอบเลยได้ไหม" → ไม่เฉลย · รูป + แก้บรรทัดบนการ์ด → ถูก → การ์ด 14% → demo-2 · `hw_024` ถูก → 43% → demo-3 · `hw_007` ผิดบรรทัด 3 `sign` (ตรง label) → tutor ชี้เครื่องหมาย → อนุพันธ์ weak 50% → demo-4
- เวลา: ข้อความแรก 10.7 s (เปิดครั้งแรก) ต่อจากนั้น 1.1 s · ส่งรูป 1.5–1.7 s · ยืนยัน 3.5–6 s

- implement ขั้น 3–5: red → green 2 รอบ · (1) 17/18 test เดโม่เขียว (AC-8 รอ prompt v2) (2) ขึ้น `tutor_reply` v2 แล้ว test เดิม 22 ตัวล้ม `missing inputs: ['problem']` → เพิ่ม `defaults` ใน gateway (Jam ข้อ 1) เหลือ 1 ตัวที่ล้มเพราะเขียน `prompt_version == "v1"` ไว้ตรงๆ
- `/dev/uploads` เป็น `include_in_schema=False` จึงไม่อยู่ใน `/docs` และ `test_api_md_endpoints` ไม่เห็น

- demo-room test: เขียน test ของขั้น 3–5 รวมไฟล์เดียว ให้ Jam review รอบเดียว · หน้าตาโค้ดที่ test กำหนด: `app.services.dev_uploads` (`get_local_mode`, `get_local_upload_dir` เป็น dependency) · `app.services.demo_room` (`DEMO_PROBLEMS`, `DEMO_TOPICS`, `DemoRoomState`) · `PendingProblem` เพิ่ม `text_latex`, `difficulty`, `topic_id` · เปิดห้องใน local รีเซ็ต state ของ session (การ์ดเริ่มที่ยังไม่เริ่มทุกหัวข้อ · AC-10)

- bkt implement: red → green 1 รอบ (32 กรณีเขียวในรอบแรก) · ruff จับเครื่องหมาย `×` ใน docstring (RUF002) เปลี่ยนเป็น `*`

- bkt test: `ReadinessTopic` มี field `attempts` เพิ่มจาก spec §3 เพื่อให้ `readiness()` รู้ว่าหัวข้อยังไม่เริ่ม (AC-10b) · ทุกฟังก์ชันรับ `LearningConfig` ยกเว้น `update_mastery` ที่รับ `BktConfig` ตาม spec §3 · ใส่ mode `final` ใน AC-6 ด้วย (★★ final = `two_star_final_difficulty` ตาม §2 ข้อ 3)

- เว็บไม่ต้องแก้: `uploadPhoto` ใน `apps/web/lib/httpTransport.ts` จะ `PUT` ไฟล์เองเมื่อ response ของ `/uploads` ไม่มี `X-Stub` · CORS อนุญาต `PUT` + `Content-Type` แล้ว (`app/cors.py`)
