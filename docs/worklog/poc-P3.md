# PoC P3a · เอกสาร → หัวข้อ + ดาว (MTH10101)

| | |
|---|---|
| Owner | Jam |
| Branch | `poc/P3` |
| Checklist item | P3: ingest → A5 → A6 → A7 → `compute_importance` · เทียบกับ label · ลอง embedding 2–3 ตัวกับคำถาม 20 ข้อ |
| Status | in progress · 2026-10-19 |

รอบนี้ทำแค่ **P3a** (หัวข้อ + ดาว เทียบกับ label) ส่วน **P3b** (embedding กับคำถาม 20 ข้อ) แยกเป็น branch ใหม่ทีหลัง · spec: `specs/poc/README.md` P3, `specs/system/ai-orchestration.md` §2.3, §2.9–2.11 · label: `evals/topics/mth10101/labels.json` (May, 27 หัวข้อ, map ข้อสอบ 43 ข้อย่อย)

## Plan

- [x] 1. 🙋 Jam: ขอ Junior ในกลุ่มว่า Jam จะเขียน gateway lite ใน `apps/api/app/ai/` เอง (เป็นงาน S3 ของ Junior) และให้ Junior เป็นคน review
- [ ] 2. 🙋 Jam: สร้าง Gemini API key ใน AI Studio แล้วใส่ใน `.env` ที่ root ของ repo (Claude ห้ามอ่านไฟล์นี้)
- [ ] 3. 🤖 Gateway lite · test ก่อน: `ai.call(purpose, input, schema)` โหลด prompt ตาม `config/ai.yaml`, error ถ้ามี placeholder ที่ไม่ได้เติม, เลือก provider fake/gemini ตาม `AI_PROVIDER`, ตรวจ schema ด้วย Pydantic แล้ว retry 1 ครั้ง, เขียน log การเรียกลงไฟล์ (ยังไม่เขียน `ai_calls` ลง DB) → 🙋 Jam review test → implement
- [ ] 4. 🤖 Prompt v1 + Pydantic model ของ A2 `vision_extract`, A4 `split_past_exam`, A6 `merge_topics`, A7 `map_questions`
- [ ] 5. 🤖 `poc/P3/ingest.py`: ชีทอ่านด้วย PyMuPDF + เช็คคุณภาพข้อความ (% ตัวอักษรไทย) · ข้อสอบสแกนส่งรูปรายหน้าให้ A2 แล้วตัดรายข้อด้วย A4 · เก็บผลเป็นไฟล์ใน `poc/P3/out/` (ไม่ลง DB)
- [ ] 6. 🤖 `poc/P3/run.py`: A5 ทีละชีท → A6 → A7 → ดาว (สูตร §2.3.5 อ่านค่าจาก `config/learning.yaml` → `stars`) · จับเวลาและต้นทุนต่อไฟล์
- [ ] 7. 🤖 `poc/P3/score.py`: เทียบกับ `labels.json` → % หัวข้อตรง, % ★★★ ตรง, เวลาต่อไฟล์, ต้นทุนต่อไฟล์ · 🙋 Jam ตัดสินวิธีจับคู่หัวข้อก่อนเขียน
- [ ] 8. 🤖 รันจริง ดูผลกับ Jam แล้วร่าง `/poc-report P3` (ส่วน P3a)

## Definition of done

- รัน `poc/P3` ด้วยคำสั่งเดียวตามที่เขียนใน `poc/P3/README.md` และได้ผลซ้ำ
- มีตัวเลขเทียบเป้า: หัวข้อตรง ≥ 80% · ★★★ ตรง ≥ 80% · ≤ 3 นาที/ไฟล์ · พร้อมต้นทุนต่อไฟล์
- ทุก AI call ผ่าน `ai.call()` ใน `apps/api/app/ai/` · test ของ gateway ผ่านด้วย fake provider · CI เขียว
- report P3 (ส่วน P3a) ร่างแล้ว · checklist ยังไม่ติ๊กจนกว่า P3b เสร็จ (เขียน sub-bullet ว่า P3a เสร็จแล้ว)

## Decisions

- 2026-10-19 · gateway lite เขียนใน `apps/api/app/ai/` เลย ไม่ทำ wrapper ใน `poc/` (Jam เลือก) · เพราะ CLAUDE.md กฎข้อ 3 และ `specs/poc/README.md` บอกให้เขียนโค้ดที่จะใช้ต่อจริงใน `apps/api` ตั้งแต่แรก · ต้องได้ OK จาก Junior ก่อน เพราะ `apps/api` เป็นโฟลเดอร์ของ Junior
- 2026-10-19 · ใช้ Gemini API key จาก AI Studio ไม่ใช้ Vertex · เพราะยังไม่มี GCP project · เปลี่ยนเป็น Vertex ได้ทีหลังที่ provider
- 2026-10-19 · แยก P3a (หัวข้อ + ดาว) กับ P3b (embedding) · เพราะ P3b ต้องมีคำถาม 20 ข้อพร้อมเฉลยหน้า ซึ่งคนที่ไม่ใช่ Jam ต้องเป็นคนเขียน
- 2026-10-19 · merge `chore/prompt-extract-topics-local` (PR #13) เข้ามา เพื่อใช้ prompt A5 · ถ้า PR #13 ถูกแก้ระหว่าง review ต้อง merge ซ้ำ
- 2026-10-19 · prompt v1 ของ A2, A4, A6, A7 เขียนเสร็จ (ยังไม่มี Pydantic model ซึ่งจะทำพร้อม gateway หลังได้ OK จาก Junior) · ทุกตัว output เป็น object ที่มี `notes` แบบเดียวกับ A5 · ส่วนที่เพิ่มจาก §2.3.7: A6 มี `sources` (ช่วงหน้าของแต่ละหัวข้อ เพราะขั้น 5d ต้องใช้สร้าง `topic_chunks` และ SM-04 ต้องแสดงเลขหน้า แต่ schema ใน spec ไม่มีช่องนี้) + `excluded_by_note` · A4 มี `points` · A7 คืน `topic_id: null` ได้พร้อม `note` (ตรงกับ `unmapped` ใน label) · `q_no` ของ A4 ใช้รูปแบบเดียวกับ label (`ก1.2`)
- 2026-10-19 · A6 สร้าง skills และ common_mistakes จากชื่อหัวข้ออย่างเดียว ไม่ได้อ่านเนื้อหาชีท (ตาม spec ที่ส่งแค่ผลของ A5) · เสี่ยงว่า skill จะกว้างเกินไป · P3a ไม่ได้วัด skill โดยตรง แต่ A7 ต้องเลือก skill_id · บันทึกเป็นข้อจำกัดไว้ใน report
- 2026-10-19 · Junior OK ให้ Jam เขียน gateway lite ใน `apps/api/app/ai/` และ Junior เป็นคน review
- 2026-10-19 · gateway lite ไม่มี feature spec แยก · test อ้าง AI-01–AI-05 + ai-orchestration §2.10 + `prompts/README.md` · ฉบับเต็ม (fallback, circuit breaker, ai_calls) Junior จะเขียน spec ใน S3
- 2026-10-19 · ใช้ `AI_MODEL_OVERRIDE` (env) แทนการใส่ model id ลง `config/ai.yaml` ระหว่าง PoC · เพราะการเลือก model เป็นผลของ PoC ที่จะอัปเดต config ผ่าน PR ทีหลัง · ถ้าเป็น live mode แล้ว model id ยังเป็น `TODO-...` gateway จะ error

## Next step

ขั้น 3: test ของ gateway เขียนแล้ว (`apps/api/tests/unit/test_ai_gateway.py`, 22 test, ยัง red) รอ Jam review · หลัง review ให้ implement `app/ai/gateway.py`, `app/ai/providers/{base,fake,gemini}.py` จนเขียว · ขั้น 4 เหลือ Pydantic model

## Waiting on

Jam review test ของ gateway · Jam ใส่ `GEMINI_API_KEY` ใน `.env` (ขั้น 2)

## Notes for next time

- งานที่ค้าง: `chore/handwriting-photos` (PR #11) รอรูป · `chore/prompt-extract-topics-local` (PR #13) รอ Junior review
- PyMuPDF ทำ ∞ หาย และสมการ Equation Editor กระจายออกมาบรรทัดละตัว (ดู PR #13)
