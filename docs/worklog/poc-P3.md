# PoC P3a · เอกสาร → หัวข้อ + ดาว (MTH10101)

| | |
|---|---|
| Owner | Jam |
| Branch | `poc/P3` |
| Checklist item | P3: ingest → A5 → A6 → A7 → `compute_importance` · เทียบกับ label · ลอง embedding 2–3 ตัวกับคำถาม 20 ข้อ |
| Status | paused · 2026-10-20 |

## Done today (2026-10-20)

- แก้ gateway ให้ซ่อม LaTeX ที่ model ลืม escape · รอบแรกซ่อมทุก string ใน `_parse` แล้ว Junior review ว่าไปแก้ข้อความธรรมดาด้วย · รอบสองเปลี่ยนเป็น opt-in: `LatexStr` / `MathTextStr` ใน `apps/api/app/ai/latex.py`
- ตรวจ cache ของ P3 แล้วไม่มีจุดเสีย จึงรัน A7 ได้เลยโดยไม่ต้องซ่อม
- ขอ Junior review ล่วงหน้าเฉพาะส่วน `apps/api/` + `config/ai.yaml` · Junior ขอแก้ 2 จุด (backoff, LaTeX opt-in) · แก้ครบแล้ว (`b39587f` test, `aa51819` แก้) · ตอบใน PR #15 และขอ review รอบสองแล้ว
- merge `poc/P3` เข้า `poc/P1` แล้ว 2 รอบ (รอบล่าสุดหลังแก้ตาม review)

## Done (2026-10-19)

- Junior OK ให้ Jam เขียน gateway lite · ได้ `ai.call()` + fake/Gemini provider + thinking level + รับ input เป็น list ของรูป · test ของ api เขียว 78 ตัว (รวม model ของ output flow 2.3 ทั้งหมด)
- prompt v1: vision_extract, vision_extract_pages, split_past_exam, merge_topics, map_questions · โค้ด PoC ครบ: `poc/P3/{common,ingest,run,stars,score}.py` + README · test ของ PoC 12 ตัว · ทดสอบครบวงจรด้วย fake provider ผ่าน
- รันจริงยังไม่สำเร็จ: thinking token ทำให้คำตอบถูกตัด (แก้แล้วด้วย thinking low) → bug ของตัวเว้นช่วง (แก้แล้ว) → โควตา free tier 20 ครั้งต่อวันหมด · ผลแรกที่ไม่ใช้ AI: สูตรดาวกับ map ข้อสอบของ May ได้ ★★★ ตรง 83%
- (session 4, 14:00) รันจริง: ingest ผ่าน (ตัดข้อตรง 43/43) · A5 ครบ 4 ชีท · A6 ไม่ผ่าน schema แล้วโควตาวันหมด · ผล A5 เทียบ label 56% (AI แบ่งหัวข้อหยาบกว่า) · เพิ่ม `SaveRaw` + ปิด retry ของ gateway ใน PoC · ร่าง `extract_topics_local/v2` + `--a5-prompt`
- (session 3) merge `main` (PR #13, #14, #17, #18) เข้ามาแล้ว ไม่มี conflict · แก้ `ai-orchestration.md` §2.3.3, §2.3.7, §3.1 ให้ตรงกับ prompt/model และสิ่งที่เจอใน ingest แล้ว

รอบนี้ทำแค่ **P3a** (หัวข้อ + ดาว เทียบกับ label) ส่วน **P3b** (embedding กับคำถาม 20 ข้อ) แยกเป็น branch ใหม่ทีหลัง · spec: `specs/poc/README.md` P3, `specs/system/ai-orchestration.md` §2.3, §2.9–2.11 · label: `evals/topics/mth10101/labels.json` (May, 27 หัวข้อ, map ข้อสอบ 43 ข้อย่อย)

## Plan

- [x] 1. 🙋 Jam: ขอ Junior ในกลุ่มว่า Jam จะเขียน gateway lite ใน `apps/api/app/ai/` เอง (เป็นงาน S3 ของ Junior) และให้ Junior เป็นคน review
- [x] 2. 🙋 Jam: สร้าง Gemini API key ใน AI Studio แล้วใส่ใน `.env` ที่ root ของ repo (Claude ห้ามอ่านไฟล์นี้)
- [x] 3. 🤖 Gateway lite · test ก่อน: `ai.call(purpose, input, schema)` โหลด prompt ตาม `config/ai.yaml`, error ถ้ามี placeholder ที่ไม่ได้เติม, เลือก provider fake/gemini ตาม `AI_PROVIDER`, ตรวจ schema ด้วย Pydantic แล้ว retry 1 ครั้ง, เขียน log การเรียกลงไฟล์ (ยังไม่เขียน `ai_calls` ลง DB) → 🙋 Jam review test → implement
- [x] 4. 🤖 Prompt v1 + Pydantic model ของ A2 `vision_extract`, A4 `split_past_exam`, A6 `merge_topics`, A7 `map_questions`
- [x] 5. 🤖 `poc/P3/ingest.py`: ชีทอ่านด้วย PyMuPDF + เช็คคุณภาพข้อความ (% ตัวอักษรไทย) · ข้อสอบสแกนส่งรูปรายหน้าให้ A2 แล้วตัดรายข้อด้วย A4 · เก็บผลเป็นไฟล์ใน `poc/P3/out/` (ไม่ลง DB)
- [x] 6. 🤖 `poc/P3/run.py`: A5 ทีละชีท → A6 → A7 → ดาว (สูตร §2.3.5 อ่านค่าจาก `config/learning.yaml` → `stars`) · จับเวลาและต้นทุนต่อไฟล์
- [x] 7. 🤖 `poc/P3/score.py`: เทียบกับ `labels.json` → % หัวข้อตรง, % ★★★ ตรง, เวลาต่อไฟล์, ต้นทุนต่อไฟล์ · 🙋 Jam ตัดสินวิธีจับคู่หัวข้อก่อนเขียน
- [x] 8a. 🤖 แก้ตาม review ของ Junior ใน PR #15 · test ก่อน: retry backoff (ใช้ `retryDelay` ของ provider ถ้ามี ไม่งั้นรอตาม config · เกินเพดานไม่ retry) + ซ่อม LaTeX แบบ opt-in (`LatexStr`, `MathTextStr`) → 🙋 Jam review test
- [x] 8b. 🤖 แก้โค้ด + 2 key ใน `config/ai.yaml` + `ai-orchestration.md` §2.9 → merge `poc/P3` เข้า `poc/P1` → ตอบ Junior ใน PR #15
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
- 2026-10-19 · gateway lite เขียว (22 test ใหม่ + 6 test เดิม) · ไฟล์: `app/ai/gateway.py`, `app/ai/providers/{base,fake,gemini}.py` · env ใหม่ `GEMINI_API_KEY`, `AI_MODEL_OVERRIDE` (เพิ่มใน `.env.example`, `settings.py`, `setup.md` A5) · script ของ PoC สร้าง `Gateway.live` เอง จึงไม่ต้องเปลี่ยน `AI_PROVIDER` ใน `.env` · red → green 1 รอบ
- 2026-10-19 · Gemini 3 นับ thinking token รวมใน `max_output_tokens` · `max_tokens` ใน `ai.yaml` จึงอาจทำให้คำตอบถูกตัดกลางทาง ให้ดูตอนรันจริง
- 2026-10-19 · ใช้ `gemini-3.5-flash` ระหว่าง PoC (Jam เลือก) · เพราะ `gemini-3.8-flash` ตอบข้อความทดสอบสั้นๆ ใช้เวลา 35 วินาที และเคย 504 DEADLINE_EXCEEDED 2 ครั้ง ส่วน 3.5-flash ใช้ 1.7 วินาที (free tier, 2026-10-19) · ตอนรันจริงให้รัน 3.8 เทียบ 1 รอบ แล้วใส่ทั้งความแม่นและความเร็วลงใน report · key ของ AI Studio ไม่ได้ขึ้นต้นด้วย `AIza` แต่ใช้ได้ปกติ
- 2026-10-19 · model ของ A2, A4, A5, A6, A7 + extract_answer อยู่ใน `apps/api/app/models/scope_ai.py` · test 37 case เขียว (รวมทั้งหมด 65) · red → green 1 รอบ · model ตรวจกฎของ prompt ด้วย (ช่วงหน้า, เลขข้อ, กราฟ prerequisite ห้ามวน, skill ต้องเป็นของหัวข้อตัวเอง) ถ้า AI ตอบผิดกฎ จะถูกส่งกลับไปแก้ผ่าน schema retry
- 2026-10-19 · ingest รอบแรก: เช็คคุณภาพข้อความได้ผลชัด (ตัวอักษรไทยในข้อสอบสแกน 0%, ในชีท 48–85%, เกณฑ์ `MIN_THAI_SHARE = 0.3`) · แต่ midterm-2559-1 หน้า 12 ได้ schema error เพราะ thinking token ใช้จนชนเพดาน `max_tokens: 4000` (ทั้ง 2 รอบได้ ~3,993 token) · ทดลองตั้ง thinking low กับหน้าเดียวกัน: 396 token, 4.9 วินาที, JSON ถูก · และ free tier ให้แค่ 5 ครั้งต่อนาที (`gemini-3.5-flash` ถูกส่งไปที่ `gemini-3.6-flash`) ทำให้ 10 จาก 23 call โดน 429
- 2026-10-19 · (Jam เลือกตามคำแนะนำ) A: เพิ่ม `thinking: low|medium|high` ที่ระดับ purpose ใน `config/ai.yaml` + `PurposeConfig` · ตั้ง low ให้ vision_extract, split_past_exam, extract_topics_local, map_questions และ medium ให้ merge_topics · B: ~~เปิด billing~~ → Jam ยังไม่อยากจ่ายเงินช่วง develop จึงใช้ free tier ต่อ · `poc/P3/common.py` ห่อ provider ด้วย `Spaced` ให้ทุก request ห่างกัน 13 วินาที (ครอบคลุม retry ของ gateway ด้วย) · ใน report เวลาต่อไฟล์จะนับแค่ `latency_ms` ไม่นับเวลารอโควตา และต้องเขียนไว้ว่าวัดบน free tier · ⚠️ ก่อนทำ P1 ต้องแก้เรื่อง AI-07: ห้ามส่งรูปลายมือเพื่อนผ่าน free tier ให้เปิด billing ช่วงนั้น หรือขอ consent ใหม่ที่บอกเรื่องนี้
- 2026-10-19 · test ใหม่ `test_AI02_thinking_level_*` (5 case) เพิ่มต่อท้าย ไม่ได้แก้ test เดิม · รอ Jam review
- 2026-10-19 · รอบ 2 พังเพราะ bug ของ PoC: ตัวเว้นช่วงอยู่ใน timeout ของ gateway หน้าที่รอคิวจึง timeout ทั้งหมด (แก้แล้ว: เว้นช่วงก่อนเรียก gateway และเรียกทีละ call) · รอบ 3 เจอว่า free tier ของ `gemini-3.5-flash` ให้แค่ **20 request ต่อวัน** (`GenerateRequestsPerDayPerProjectPerModel-FreeTier`) และวันนี้ใช้หมดแล้ว (รีเซ็ตเที่ยงคืนเวลาแปซิฟิก ≈ 14:00–15:00 น. เวลาไทย)
- 2026-10-19 · (Jam เลือก) ลดจำนวน call โดยเพิ่ม purpose ใหม่ `vision_extract_pages` อ่านทุกหน้าของไฟล์ใน call เดียว (ข้อสอบ 1 ฉบับ = 1 call) · ingest เหลือ 4 call แทน 28 · ไม่ได้แก้ `vision_extract` v1 ที่ยังใช้กับรูปหน้าเดียว · gateway รับ input เป็น `list[Image]` ได้ · ต่างจาก spec §2.3.7 ที่กำหนด A2 ให้อ่านทีละหน้า จะบันทึกเป็นผลของ PoC (คุณภาพและเวลาเทียบกับแบบทีละหน้าเท่าที่วัดได้)
- 2026-10-19 · test ใหม่: `test_AI01_list_of_images_*` (2 ตัว ต่อท้าย test_ai_gateway.py) + `test_vision_extract_pages_model.py` (6 case) · รอ Jam review
- 2026-10-19 · ขั้น 5 โค้ดเสร็จ: gateway รับ `list[Image]`, `VisionExtractPagesResult`, purpose `vision_extract_pages` ใน `ai.yaml`, `ingest.py` ส่งทุกหน้าใน call เดียว · test 78 ตัวเขียว · แก้ test `test_AI01_list_of_images_is_sent_as_attachments_in_order` 1 จุด (ใช้ schema `NotesOnly` แทน `BaseModel` เปล่า เพราะ Pydantic ไม่ให้ parse ด้วย BaseModel) โดย Jam อนุมัติแล้ว · assert เหมือนเดิม
- 2026-10-19 · (Jam เลือก) จับคู่หัวข้อด้วยหน้าที่ทับกัน: IoU ของเซตหน้า (ไฟล์, หน้า) ≥ 0.5 จับคู่แบบ 1:1 เลือกคู่ที่ IoU สูงสุดก่อน · คู่ที่จับไม่ได้ให้ Junior ดูด้วยตา · ดาว ★★★ วัด 2 แบบ: (ก) สูตรดาวกับ map ข้อสอบของ May (ข) สูตรดาวกับ map ของ A7
- 2026-10-19 · สูตรดาวเขียนเป็นโค้ด PoC ใช้แล้วทิ้งใน `poc/P3/stars.py` ไม่ใส่ใน `apps/api/app/domain/` · เพราะ `compute_importance` ตัวจริงเป็นงาน P8-lite (S4) ที่ทีมจะทำร่วมกัน · test ใน `poc/P3/test_p3.py` (12 case) อ้าง AC ของ `compute-importance.md` · รอ Jam review
- 2026-10-19 · โค้ดขั้น 5–7 เสร็จ: `stars.py`, `score.py`, `run.py`, `README.md` · test ของ PoC 12 ตัวเขียว · ทดสอบครบวงจรด้วย fake provider ผ่าน (`run.py` → `score.py`) · ขั้น 5–6 ติ๊กแล้วสำหรับส่วนโค้ด ส่วนรันจริงอยู่ในขั้น 8
- 2026-10-19 · **ผลแรก (ไม่ใช้ AI):** สูตรดาวกับ map ข้อสอบของ May ได้ ★★★ ตรง 10/12 = 83% (precision 83%, ดาวตรงทุกระดับ 74%) · ผ่านเป้า 80% · ไม่ตรง: t24, t25 (L'Hôpital, May ให้ 3 สูตรให้ 2 เพราะออกแค่ 1 ใน 2 ชุด) และ t02, t09 (May ให้ 2 สูตรให้ 3) · **มีข้อสอบแค่ 2 ชุด ค่า r จึงเป็นได้แค่ 0, 0.5, 1** ทุกเกณฑ์ในช่วง (0.5, 1] ให้ผลเท่ากัน P3 จึงยืนยันได้แค่ว่า `three_star_min_r` ต้องมากกว่า 0.5 แต่ปรับค่า 0.6 ให้ละเอียดกว่านี้ไม่ได้
- 2026-10-19 · (Jam เลือกตามคำแนะนำ) เพิ่ม max_tokens / timeout_s ใน `ai.yaml` ก่อนรันจริง: split_past_exam 16000/120, extract_topics_local 8000/120, merge_topics 16000/180, map_questions 8000/120 · เพราะโควตา 20 ครั้งต่อวัน ถ้าคำตอบถูกตัดแล้วต้อง retry จะเสียโควตา · เพิ่มเพดานไม่ทำให้เสีย token เพิ่ม · ค่าจริงยืนยันจาก log ของ P3 ใน PR config
- 2026-10-19 14:00 · **รันจริงรอบที่ 4 (gemini-3.5-flash):** ingest ผ่าน · `vision_extract_pages` อ่านข้อสอบ 14 หน้าใน 40.5 วินาที (ต้อง schema retry 1 ครั้ง) และ 12 หน้าใน 21.6 วินาที · `split_past_exam` ได้ 23 + 20 ข้อย่อย **ตรงกับ label ครบ 43/43** · A5 เสร็จครบ 4 ชีท (14/5/5/12 หัวข้อ, sheet-01 ใช้ 13.8 วินาที, output 2,572 token) · A6 ล้ม: ได้ 503 ×2 แล้วรอบที่ 3 ได้คำตอบยาว 11,242 token ซึ่งไม่ผ่าน schema แล้วโควตาวันหมดตอนกำลัง retry · **503 ก็นับเป็น request** และ gateway retry ทันทีอีก 1 ครั้ง ทำให้เสียโควตา 2 เท่า
- 2026-10-19 · **ผล A5 เทียบกับ label (ยังไม่ merge):** จับคู่ IoU ≥ 0.5 ได้ 15/27 (56%), ≥ 0.3 ได้ 18/27 · AI แบ่งหยาบกว่า May: sheet-01 ได้ 14 หัวข้อ ส่วน label มีประมาณ 22 · รวมหัวข้อของ May เข้าด้วยกัน (อนุพันธ์ฟังก์ชันอดิศัย = t08+t09+t10, ลิมิต = t01+t02, เพิ่ม/ลด+เว้า = t16+t17, L'Hôpital = t24+t25) และนับหน้าแบบฝึกหัดท้ายบทรวมเข้าไปด้วย (เช่น 117-119) · A6 แยกหัวข้อไม่ได้ จึงคาดว่า v1 จะไม่ผ่านเป้า ≥ 80%
- 2026-10-19 · (Jam เลือกตามคำแนะนำ) รัน v1 ให้ครบก่อนเพื่อได้ baseline แล้วค่อยทำ `extract_topics_local/v2` (แยกหัวข้อย่อยที่มีตัวอย่างของตัวเอง + ไม่นับหน้าแบบฝึกหัดท้ายบท) แล้วรันเทียบวันถัดไป · ตามกฎใน prompts/README ที่ต้องเทียบ eval กับ version เดิม (v1 มีผล eval แล้ว จึงห้ามแก้ v1 อีก)
- 2026-10-19 · PoC: `common.py` ห่อ provider ด้วย `SaveRaw` (เก็บคำตอบดิบทุกครั้งลง `out/raw/<tag>-<n>.txt`) และตั้ง gateway `retries: 0` เฉพาะใน PoC (ไม่ได้แก้ `ai.yaml`) ให้ `Run.call` รอแล้วค่อยลองใหม่เอง

- 2026-10-19 · ร่าง `prompts/extract_topics_local/v2.md`: 1 หัวข้อ = 1 section ที่มีหัวข้อของตัวเองพร้อมคำอธิบายหรือตัวอย่าง (ตามโครงสร้างของไฟล์) · ชื่อบทหรือ part ไม่นับเป็นหัวข้อ · ห้ามรวม section ที่มีหัวข้อต่างกัน · ไม่นับหน้าแบบฝึกหัดท้าย section/บท/ไฟล์และหน้าเฉลยเข้าไปในช่วงหน้า (ยกเว้นไฟล์ที่เป็นแบบฝึกหัดทั้งไฟล์) · ไม่ใส่ตัวเลขหรือตัวอย่างจาก label ของ MTH10101 · v2 ถูกปรับโดยดูผลของชุดที่ใช้วัดผล ตัวเลขของ v2 จึงดีเกินจริงไปบ้าง ต้องเขียนเป็นข้อจำกัดใน report (ควรทดสอบกับวิชาอื่น)
- 2026-10-19 · PoC: `run.py --a5-prompt v2` / `score.py --a5-prompt v2` override prompt เฉพาะรอบนั้น (ไม่แก้ `ai.yaml`) · cache A5 แยกตาม version (`out/a5/<model>/<version>/` · ย้ายของ v1 ไปไว้ใน `v1/` แล้ว) · ผลอยู่ใน `results/<model>-a5<version>/` · dry run ด้วย fake provider ผ่าน
- 2026-10-19 · ข้อสังเกตเรื่องการให้คะแนน: label ของ May มีแค่หน้าใน sheet-01/02 (ไม่มีหน้าใน sheet-03/04) แต่ A6 อาจรวมหน้าแบบฝึกหัดจาก sheet-03/04 เข้าไปใน `sources` ทำให้ IoU ลดลง ถึงหัวข้อจะตรงก็ตาม · หลังได้ผลของ v1 ให้ดูว่ากระทบมากแค่ไหน แล้วให้ Jam ตัดสินว่าจะคิด IoU เฉพาะไฟล์ที่ label มีหรือไม่
- 2026-10-20 · (Jam เลือกตามคำแนะนำ) แก้ bug escape บน branch นี้ แล้ว merge `poc/P3` เข้า `poc/P1` (รายละเอียดอยู่ใน `docs/worklog/poc-P1.md`) · test 5 ตัวต่อท้าย `test_ai_gateway.py`: 3 ตัว fail ตามที่ควร (form feed/backspace, tab/CR, newline + ชื่อคำสั่ง) · 2 ตัวผ่านแล้วตั้งแต่ตอนนี้ เพราะเป็นตัวกันไม่ให้การซ่อมไปทำของเดิมพัง (newline ปกติ, LaTeX ที่ escape ถูกแล้ว) · newline ซ่อมเฉพาะเมื่อตามด้วยชื่อคำสั่งเต็มคำ (`neq` `nabla` `notin` ...) เพื่อไม่ให้ `\nother` ใน notes กลายเป็น `\not`+`her`
- 2026-10-20 · **ตรวจผลกระทบของ bug escape ใหม่: P3 ไม่โดน** · `out/pages/midterm-*.json` และ `out/questions/*.json` ไม่มีตัวอักษรควบคุมเลย (`\frac` 88 จุดถูกต้องทั้งหมด) · ตัวเลข 88/92 และ 23/30 ที่เขียนไว้วันที่ 19 นับผิด · ใน P1 โดนแค่ hw_004 (form feed 9 จุด) · ลองใช้กฎซ่อมกับ cache แบบไม่เขียนทับ พบว่ากฎ newline ไปโดนข้อความชีทของ PyMuPDF 296 จุด (`\ne\n` `\nu =`) · (Jam เลือกตามคำแนะนำ) ตัด `\ne` `\ni` `\nu` `\not` ออกจากกฎ เพราะถ้าซ่อมผิด `e^{x}` จะกลายเป็น `≠` แบบเงียบๆ · เพิ่ม test 1 ตัว · หลังแก้ กฎตรงแค่ hw_004 ใน cache ทั้งหมด
- 2026-10-20 · **Junior review PR #15: ขอแก้ 2 จุด** (1) retry ไม่มี backoff ทั้งที่ §2.10 เขียนว่า backoff (2) `repair_unescaped_latex` ซ่อมทุก string ของทุก purpose เช่น newline ก่อน `mid-term` ในข้อความไทยกลายเป็น `\n` ตัวอักษร และ tab ก่อนตัวอังกฤษถูกแก้ · Junior พูดถูก (test เดิมเช็คแค่ newline ก่อน `other` และ tab ก่อนภาษาไทย) · ไม่ block: JSON mode กับ stream (Junior ทำใน S3), schema retry เมื่อชน max_tokens, license PyMuPDF (AGPL) ให้ทีมคุย
- 2026-10-20 · (Jam เลือกตามคำแนะนำ) (1) backoff: ใช้ `retryDelay` จาก provider ถ้ามี ไม่งั้นรอ `gateway.retry_backoff_seconds` · ถ้าต้องรอเกิน `gateway.max_retry_wait_seconds` ไม่ retry (ห้องติวมีเป้า TTFT 2 วินาที · PoC รอเองใน `Run`) · เพิ่ม 2 key ใน `config/ai.yaml` (ไฟล์กลาง · แจ้งกลุ่ม) (2) LaTeX: เลิกซ่อมทุก string ใน `_parse` · ใช้ `LatexStr` กับ field ที่เป็น LaTeX ล้วน (`AnswerLine.latex`, `latex_blocks`) และ `MathTextStr` ซ่อมเฉพาะใน `$...$` กับข้อความไทยปนสูตร (`text` ของ A2/A2b/A4) · Jam อนุญาตแก้ test escape 6 ตัวที่ review แล้วให้ model ใน test ใช้ `LatexStr` (สิ่งที่ตรวจเหมือนเดิม)
- 2026-10-20 · ขั้น 8b แก้แล้ว: `app/ai/latex.py` (LatexStr, MathTextStr ซ่อมใน `$...$` และ `$$...$$`) · `_parse` กลับไปใช้ `model_validate_json` ตรงๆ · backoff ใน `_generate` · `gemini.py` แปลง 429 เป็น `ProviderRateLimited` พร้อม `retryDelay` · test 98 ผ่าน · ลองกับ cache จริง: P3 248 ข้อความไม่เปลี่ยน · P1 ไฟล์ hw_004 เดิม (.bak) ซ่อมได้ ไฟล์ที่ซ่อมแล้วไม่เปลี่ยน
- 2026-10-20 · merge `poc/P3` เข้า `poc/P1` แล้ว (test P1 ผ่าน) · ตอบ Junior ใน PR #15 และขอ review อีกรอบแล้ว · license PyMuPDF รับว่าจะยกไปคุยในกลุ่ม
- 2026-10-20 · **รัน A6 ไม่ได้:** `gemini-3.5-flash` ได้ 503 UNAVAILABLE ("high demand") ทั้ง 2 รอบ (14:05 และ 14:30 · รอบละ 4 ครั้ง รอ 30/60/90 วินาที) · ไม่ใช่ bug ของเรา · ไม่แน่ใจว่า 503 นับเข้าโควตาไหม · (Jam ตัดสิน) ลอง `gemini-3.8-flash` ทั้งชุด: A5 ของ sheet-01 timeout 120 วินาทีตั้งแต่ call แรก → ข้อมูลสำหรับ report: 3.8-flash ช้าเกินสำหรับ A5 กับชีทใหญ่ · (Jam เลือก) เลื่อนไปรันพรุ่งนี้เช้าด้วย 3.5-flash (cache A5 เดิม)

## Next step

ขั้น 8: เช้า 21 ต.ค. (ช่วงคนใช้น้อย) รัน `cd apps/api && uv run python ../../poc/P3/run.py --a5-prompt v1` ด้วย gemini-3.5-flash (ใช้ cache A5 · A6 + A7 ×2 = 3 call) → `score.py --a5-prompt v1` · ถ้ายังได้ 503 ทั้งเช้า ให้ถาม Jam ว่าจะเปลี่ยน A6 เป็น tier อื่นไหม · ดู log ว่ามี MAX_TOKENS ไหม (Junior ถาม)

หลัง 14:00 น. ของ 2026-10-20 (เช็คโควตาด้วย request เดียวก่อน): `cd apps/api && uv run python ../../poc/P3/run.py --a5-prompt v1` (ใช้ cache A5 v1 · เหลือ A6 + A7 ×2 = 3 call) → `uv run python ../../poc/P3/score.py --a5-prompt v1` → ถ้า A6 ไม่ผ่าน schema ให้ดู `out/raw/run_merge-*.txt` · จากนั้นถ้าโควตาเหลือ: `run.py --a5-prompt v2` (A5 ×4 + A6 + A7 ×2 = 7 call) → `score.py --a5-prompt v2` → สรุปเทียบ v1/v2 ให้ Jam

## Waiting on

โควตา free tier ของ gemini-3.5-flash รีเซ็ต 2026-10-20 ≈ 14:00 น. · Junior review รอบสองใน PR #15 (แก้ 2 จุดแล้ว)

## Notes for next time

- งานที่ค้าง: `chore/prompt-extract-topics-local` (PR #13) รอ Junior review · `chore/handwriting-photos` merge แล้ว
- บน branch นี้ `poc/P1/` จะโผล่เป็น untracked (คือ `out/` กับ `results/` ของ P1 ซึ่ง gitignore อยู่แค่บน `poc/P1`) · ห้าม commit บน branch นี้
- PyMuPDF ทำ ∞ หาย และสมการ Equation Editor กระจายออกมาบรรทัดละตัว (ดู PR #13)
- `poc/P3/out/` gitignored (มี log รอบที่ล้ม: `calls-run1-failed.jsonl` = thinking ชนเพดาน + 429 รายนาที, `calls-run2-queue-timeout.jsonl` = bug ตัวเว้นช่วง) · ใช้ใน report P3 ได้
- โควตาของ `gemini-3.5-flash` free tier: 5 ครั้งต่อนาที + 20 ครั้งต่อวันต่อ model (ใน error ชื่อ `gemini-3.6-flash`) · `gemini-3.5-flash-lite` มีโควตาแยก · `gemini-3.8-flash` ช้ามาก (35 วินาทีกับข้อความทดสอบสั้นๆ)
- dry run แบบไม่ใช้โควตา: script `dry_run.py` อยู่ใน scratchpad ของ session 2026-10-19 (ไม่ได้ commit) · ใช้ FakeProvider + label มาปลอมเป็นคำตอบของ A5/A6/A7
- python ใน Git Bash heredoc ที่มีภาษาไทยบางทีขึ้น `SyntaxError: Non-UTF-8` · สาเหตุคือ `python` ของเครื่องเป็น 3.9 ซึ่งอ่านบรรทัดยาวที่มีภาษาไทยไม่ได้ · ให้ใช้ Edit tool หรือ `uv run --project apps/api python` (3.12) แทน
- 2026-10-19 (session 3) แก้ §2.3.3 + §2.3.7 + §3.1 ของ `ai-orchestration.md` ให้ตรงกับ prompt และ model แล้ว (A2b, schema แบบ object, เช็คคุณภาพข้อความ, ข้อจำกัดของ PyMuPDF) · ก่อนทำ P1 ต้องแก้เรื่อง AI-07 (รูปลายมือห้ามส่งผ่าน free tier)
- test ของ gateway มี fixture `sleeps` (autouse) ที่แทน `app.ai.gateway._sleep` · ถ้าเขียน test ใหม่ที่ retry ไม่ต้องกลัวรอจริง · ใช้ `sleeps` เป็น argument เพื่อตรวจเวลาที่รอ
- field ใหม่ของ output model ที่เป็น LaTeX ต้องใช้ `LatexStr` (ทั้ง string) หรือ `MathTextStr` (ไทยปนสูตรใน `$...$`) · `str` ธรรมดาจะไม่ถูกซ่อม
- PoC ตั้ง gateway `retries: 0` ใน `Run` เอง จึงไม่โดน backoff ใหม่ (2 key ใหม่ใน `ai.yaml`: `retry_backoff_seconds`, `max_retry_wait_seconds`)
