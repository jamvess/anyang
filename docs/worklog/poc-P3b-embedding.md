# PoC P3b · embedding ภาษาไทย (MTH10101)

| | |
|---|---|
| Owner | Jam |
| Branch | `poc/P3b-embedding` |
| Checklist item | P3: ingest → A5 → A6 → A7 → `compute_importance` · เทียบกับ label · ลอง embedding 2–3 ตัวกับคำถาม 20 ข้อ (ส่วน embedding · ส่วน P3a อยู่ใน PR #37) |
| Status | paused · 2026-10-21 |

## Done today (2026-10-21, session บ่าย)

- คำถามของ May (PR #46) เข้ามาแล้ว · รันจริงครบ: **gemini-embedding-2 @768 recall@4 95%** · @3072 90% · bge-m3 45% · ผลใน `poc/P3/results/embed-*.json`
- เช็คแล้วว่า @1 = @4 ของ bge-m3 ไม่ใช่ bug (อันดับของ chunk ที่ถูกอยู่ใน Decisions)
- เพิ่ม `embedding.dimensions` ใน gateway + Gemini (`output_dimensionality`) + `embed.py --dimensions` · test ก่อน (Jam review) → api 172 · PoC 25 ผ่าน
- merge main แล้ว · ขอ Junior review ล่วงหน้าเฉพาะ `apps/api/` + `config/ai.yaml` ใน comment ของ PR #39 (Junior เป็น reviewer แล้ว · PR ยังเป็น draft)
- (เที่ยง) Junior comment ใน #39 ว่า OK + ตกลง 3 ข้อ (vector ผิดขนาด = error · cosine · tokens_in 0 จนย้าย Vertex) · Junior แก้ `data-model.md` ใน PR #54 · Jam approve #54 แล้ว

## Done (2026-10-20 → 21 เช้า)

- branch + draft PR #39 · ตัด chunk ชีท 4 ไฟล์ (`poc/P3/chunking.py`) · เทมเพลตคำถามให้ May
- `Gateway.embed()` + `GeminiProvider.embed()` + `embed.py` (recall@1/@4, cache vector) · test API 109 + PoC 23 ผ่าน
- smoke test เจอและแก้ 4 เรื่อง: embedding-2 รวมข้อความเป็น vector เดียว · เพดาน 8,192 token/request · ภาษาไทย 1.7 ตัวอักษรต่อ token (ตัด chunk ใหม่เป็น 116) · local model โหลดซ้ำทุก call
- smoke test bge-m3 ผ่าน (vector ของ 116 chunk อยู่ใน cache แล้ว) · ตัด embedding-001 ออก (key ไม่มีโควตา)

spec: `specs/poc/README.md` P3 (metric: recall@4 ของ retrieval · ผลที่ต้องได้: embedding model + มิติ vector + ขนาด chunk) · `specs/system/ai-orchestration.md` §1.4 Retrieval, §2.3.3 Chunk/Embed · AI-01, AI-08

## Plan

- [x] 1. 🤖 ตัด chunk ของชีท 4 ไฟล์ตาม §2.3.3 (400–800 tokens ไม่คร่อมเกิน 2 หน้า) จากข้อความ PyMuPDF ที่ ingest ไว้แล้ว · ทำเทมเพลตคำถาม `evals/topics/mth10101/retrieval_questions.jsonl` + คู่มือ + รายชื่อหัวข้อจาก label ให้กระจายคำถามครบ
- [x] 2. 🙋 **May (หรือ Junior) เขียนคำถาม 20 ข้อ + เฉลยหน้า** (ไม่ใช่ Jam · คน label ไม่ใช่คนทำ PoC) · Jam ส่งงานในกลุ่ม
- [x] 3. 🙋 Jam ตัดสิน model ที่จะลอง 2–3 ตัว และวิธีเรียก embedding ผ่าน provider layer (AI-01)
- [x] 4. 🤖 test ก่อน → โค้ด spike `poc/P3/embed.py`: embed chunk + คำถาม · recall@4 ต่อ model · มิติ vector · เวลา · ต้นทุน → 🙋 Jam review test
- [x] 5a. 🤖 test ก่อน: `output_dimensionality` (`embedding.dimensions` ใน config ค่าเริ่มต้น `None` · ตรวจขนาด vector · `embed.py --dimensions`) → 🙋 Jam review test → implement → รัน 768 มิติ
- [ ] 5. 🤖 รันจริง → สรุปเทียบ → ใส่ใน report P3 (ส่วน P3b)

## Definition of done

- คำถาม 20 ข้อ + เฉลยหน้า เขียนโดยคนที่ไม่ใช่ Jam
- recall@4 ของแต่ละ model (2–3 ตัว) บนชุดเดียวกัน · มิติ vector · เวลาและต้นทุน
- เลือก embedding model + ขนาด chunk ได้ (ตาม "ผลที่ต้องได้" ของ P3)
- ทุก AI call ผ่าน provider layer (AI-01) · เก็บ text คู่กับ vector (AI-08) · test ผ่าน

## Decisions

- 2026-10-20 · แยกจาก P3a (PR #37) เป็น branch ใหม่ ตามที่ตัดสินไว้ 19 ต.ค. · คำถามต้องเขียนโดยคนที่ไม่ใช่ Jam
- 2026-10-20 · ขั้น 1a: test ของตัวตัด chunk (`poc/P3/test_chunking.py` 7 ตัว fail ตามที่ควร) + โครง `chunking.py` · ตั้งชื่อ `chunking` ไม่ใช่ `chunk` เพราะชนกับ module `chunk` ของ Python 3.12 · ประมาณ token จากจำนวนตัวอักษร ÷ 3 (PoC เท่านั้น ไม่เรียก tokenizer) · เทมเพลตคำถามเป็น markdown table (`evals/topics/mth10101/retrieval_questions.md`) ให้คนเขียนกรอกง่าย · Claude แปลงเป็น jsonl ตอนรัน
- 2026-10-20 · ขั้น 1 เสร็จ: `chunking.py` ผ่าน test 7 ตัว · ตัดชีทจริงได้ 93 chunk (sheet-01 71, sheet-02 17, sheet-03 2, sheet-04 3) เก็บที่ `poc/P3/out/chunks.json` (gitignored) · **median 334 tokens · 58/93 chunk ต่ำกว่า 400** เพราะกฎ "ไม่คร่อมเกิน 2 หน้า" ตันก่อน: หน้าของชีทสั้น (median ~190 tokens ต่อหน้า เพราะ PyMuPDF กระจายสมการทีละบรรทัด) · ข้อมูลสำหรับเลือกขนาด chunk: อาจลองเทียบ 1 หน้า vs 2 หน้าใน spike
- 2026-10-20 · (Jam เลือกตามคำแนะนำ) เทียบ 3 model: `gemini-embedding-2`, `gemini-embedding-001` (Gemini API, key เดิม) และ `BAAI/bge-m3` (open-source รันในเครื่อง เป็นเส้นฐาน) · ไม่เอา multilingual-e5-large เพราะ input สูงสุด 512 tokens · เรียกผ่าน provider layer: เพิ่ม `Gateway.embed()` + `GeminiProvider.embed()` พร้อม test (route ตาม tier `embed`) · bge-m3 เป็น provider เฉพาะ PoC ใน `poc/P3/` · ติดตั้ง sentence-transformers ชั่วคราวผ่าน `uv run --with` · Jam บอก Junior ในกลุ่ม
- 2026-10-20 · ขั้น 4a test ก่อน: gateway `embed()` 6 ตัว (ต่อท้าย `test_ai_gateway.py`) · Gemini embed 4 ตัว (`test_gemini_provider.py`) · PoC `test_embed.py` 4 ตัว · fail 14 ตัวตามที่ควร · โครง: `EmbedRequest`/`EmbedResponse`/`EmbedProvider` ใน `providers/base.py` · `EmbeddingConfig` ใน `settings.py` · `config/ai.yaml` เพิ่ม section `embedding` (timeout_s 60, batch_size 50 · ป้าย [C]) เพราะ embed ไม่มี prompt จึงใช้ purpose เดิมไม่ได้
- 2026-10-20 · ขั้น 4b implement: `Gateway.embed` (แบ่ง batch, retry/backoff ร่วมกับ call ผ่าน `_with_retries`, ตรวจจำนวน vector, CallRecord purpose embed) · `GeminiProvider.embed` · `poc/P3/embed.py` (recall@1/@4, cache vector ต่อ model ตาม content_hash, LocalEmbedder เฉพาะ PoC) · test API 109 + PoC 23 ผ่าน
- 2026-10-21 · smoke test (คำถามทิ้ง 2 ข้อใน scratchpad ไม่ใช้เป็นผล) เจอ bug 2 จุด: (1) `gemini-embedding-2` รวมข้อความหลายอันใน request เป็น vector เดียว ต้องห่อแต่ละข้อความด้วย `types.Content` · แก้แล้ว + test ใหม่ 1 ตัว (test 001 ที่ review แล้วไม่แก้) (2) embedding-2 รับรวม 8,192 tokens ต่อ request → `embedding.batch_size` 50 → 10 · หลังแก้: embedding-2 ได้ 429 quota ทันที (ไม่มี retryDelay) · embedding-001 ได้ "Server disconnected" หลังรอหลายนาที · (Jam เลือก) รัน bge-m3 ในเครื่องก่อน + Jam เช็คโควตาที่ ai.dev/rate-limit
- 2026-10-21 · โควตาจาก ai.dev/rate-limit (Jam ส่งภาพ): Gemini Embedding 2 = RPM 100 · **TPM 30K** (ใช้ไป 31.41K) · นับ 1 ข้อความ = 1 request · **Gemini Embedding 001 ไม่มีในรายการของ key นี้** · Gemini 3.6 Flash (= 3.5-flash ของเรา) RPD เกินแล้ว (42) ทั้งที่ request ส่วนใหญ่ได้ 503 · (Jam ok) **ตัด `gemini-embedding-001` ออก** เหลือเทียบ embedding-2 กับ bge-m3 (spec ขอ 2–3 ตัว) · `embed.py` เว้นช่วงให้ไม่เกิน 25K token/นาที และ save cache ทีละ batch
- 2026-10-21 · **ภาษาไทยจริง ≈ 1.5–1.8 ตัวอักษรต่อ token** (วัดด้วย count_tokens ของ gemini-embedding-2 กับ 5 chunk: 1.47, 1.64, 1.70, 1.82, 1.82) · `chunking.py` ประมาณไว้ 3 → ต่ำไปประมาณ 1.75 เท่า · chunk จริงใหญ่กว่าที่คิด (มีก้อนหนึ่ง 1,096 token เกิน 800) · ข้อสังเกตเมื่อวานว่า chunk เล็กเกินไปจึงผิด · ต้องแก้ค่าประมาณแล้วตัด chunk ใหม่ (แก้ test ที่ Jam review แล้ว ต้องขออนุญาต)
- 2026-10-21 · (Jam อนุญาตแก้ test) `CHARS_PER_TOKEN` 3 → 1.7 (`Fraction(17, 10)` กันปัดเศษ float ที่ขอบ) · test 3 จุดแก้ตามอัตราใหม่ สิ่งที่ตรวจเหมือนเดิม · ตัด chunk ใหม่: **116 chunk** (sheet-01 90, sheet-02 20, sheet-03 3, sheet-04 3) · median 486 token · ต่ำกว่า 400: 25 · เกิน 800: 0 · 2 หน้า: 64 · ผล bge-m3 ที่รันค้างไว้ใช้ chunk ชุดเก่า ต้องรันใหม่
- 2026-10-21 · smoke test bge-m3 ผ่าน (คำถามทิ้ง 2 ข้อ · ลบไฟล์ผลทิ้งแล้ว ไม่ใช่ผลจริง): 116 chunk · 1,024 มิติ · embed chunk ทั้งหมด 409 วินาทีบน CPU (ครั้งเดียว มี cache ใน `out/embed/`) · 0.13 วินาทีต่อคำถาม · แก้ bug ของ PoC: `setdefault` โหลด model ใหม่ทุก call · local model ใช้ timeout 900 วินาทีเฉพาะ PoC (`ai.yaml` คง 60) และโหลด model ก่อนจับเวลา

- 2026-10-21 · ผลจริง (คำถาม 20 ข้อของ May, PR #46 · 116 chunk): **`gemini-embedding-2` recall@4 90% (18/20) · recall@1 75% · 3,072 มิติ · embed 116 chunk 21 วินาที · 0.16 วินาที/คำถาม** · พลาดข้อ 6 (diff cot) และ 17 (L'Hôpital) · **`bge-m3` recall@4 45% (9/20) · recall@1 45% · 1,024 มิติ · 0.57 วินาที/คำถามบน CPU** · @1 = @4 ของ bge-m3 ไม่ใช่ bug: เช็คอันดับของ chunk ที่ถูกแล้ว (script ใน scratchpad ไม่ commit) ข้อที่พลาดอยู่อันดับ 5, 6, 7, 7, 17, 18, 18, 20, 21, 79, 99 · ข้อที่พลาดหนักเป็นคำถามสูตร (cot อันดับ 79, sec⁻¹ อันดับ 99) เพราะ PyMuPDF ฉีกสมการเป็นตัวอักษรทีละบรรทัด · page ของ chunk ตรงกับเลขหน้า PDF viewer (เช็ค sheet-01:46 มี cot จริง)
- 2026-10-21 · ⚠️ schema ตอนนี้ `chunks.embedding vector(768)` แต่ embedding-2 ให้ 3,072 มิติ · pgvector index HNSW รับได้ไม่เกิน 2,000 มิติ · ต้องตัดสิน: ขอ `output_dimensionality` 768 หรือ 1536 จาก API แล้ววัด recall ซ้ำ หรือใช้ 3,072 กับ `halfvec`

- 2026-10-21 · (Jam เลือก) ขอ 768 มิติจาก API (`output_dimensionality`) ให้ตรงกับ `chunks.embedding vector(768)` แล้ววัด recall ซ้ำ · `EmbeddingConfig.dimensions` ค่าเริ่มต้น `None` (ไม่แก้ `config/ai.yaml` ตอนนี้ เพราะเป็นไฟล์ร่วม · ใส่ค่าจริงตอนอัปเดต `ai.yaml` ใน S2) · gateway ตรวจว่า vector ยาวเท่า `dimensions` (กันใส่ผิดขนาดลง DB) · PoC ส่ง `--dimensions 768` · cache/ผลแยกชื่อ `-d768` · test ใหม่: gateway 3 · gemini 2 · PoC 2 · red 4 + PoC import error (test "without dimensions keeps default" ผ่านอยู่แล้ว เป็นตัวกัน)

- 2026-10-21 · ข้อ 5a implement: `EmbedRequest.dimensions` · `EmbeddingConfig.dimensions` (ค่าเริ่มต้น `None`) · `Gateway.embed` ส่งค่าและ error ถ้า vector ยาวไม่ตรง · `GeminiProvider.embed` ส่ง `output_dimensionality` · `embed.py` `run_name()` + `--dimensions` · test api 152 + PoC 25 ผ่าน · **ผล 768 มิติ: recall@4 95% (19/20) · recall@1 75% · embed 116 chunk 21.6 วินาที · 0.16 วินาที/คำถาม · พลาดแค่ข้อ 6** · สูงกว่า 3,072 มิติ (90%) อยู่ 1 ข้อ (ข้อ 17) ซึ่งด้วยคำถามแค่ 20 ข้อถือว่าเท่ากัน · สรุป: ใช้ 768 มิติได้โดยไม่เสีย recall · `vector(768)` ใน schema ใช้ได้เลยโดยไม่ต้องทำ migration

- 2026-10-21 · merge main (ไม่มี conflict) · check: ruff ผ่าน · api 172 · PoC 25 · ขอ Junior review ล่วงหน้าเฉพาะ `apps/api/` + `config/ai.yaml` ใน comment ของ PR #39 (PR ยังเป็น draft เพราะ report ยังไม่เสร็จ) · ถาม 3 เรื่อง: vector ผิดขนาด = error, cosine vs inner product (Gemini ไม่ normalize ต่ำกว่า 3072), tokens_in = 0

- 2026-10-21 · **Junior ตกลง 3 ข้อในกลุ่มแชท** (review ล่วงหน้าของ #39): (1) vector ผิดขนาด = `AIProviderError` ไม่ตัดหรือเติมให้เอง (2) ใช้ cosine `<=>` ต่อ ตรงกับ HNSW `vector_cosine_ops` ใน `0001_init.sql:400` ไม่ต้อง normalize · Junior แก้ `data-model.md:363` เป็น "ยืนยันแล้ว (P3b)" เอง (3) `tokens_in = 0` ของ embed รับได้ช่วง free tier · ไม่ประมาณ ไม่เรียก count_tokens · AI-04 ของ embed ปิดตอนย้ายไป Vertex (comment ใน `gemini.py` ชี้ AI-04 อยู่แล้ว) · ต้องจดใน report P3 · Approve อย่างเป็นทางการตอนเอา #39 ออกจาก draft

- 2026-10-21 · Junior comment ใน #39 แล้ว (ส่วน apps/api + config/ai.yaml OK · ตกลง 3 ข้อ) · Junior แก้ `data-model.md` บรรทัด 362–363 ใน PR #54 (มิติ 768 + HNSW cosine ยืนยันแล้ว) · Jam approve #54 แล้ว (nit: backtick หาย ไม่บล็อก)

## Next step

1. Junior ตกลงส่วน `apps/api/` แล้ว (ดู Decisions 21 ต.ค.) ไม่ต้องแก้โค้ด
2. ข้อ 5 (ส่วนสุดท้าย) ทำบน branch `poc/P3` ไม่ใช่ที่นี่: ใส่ตาราง P3b ใน report P3 (`specs/poc/reports/poc-P3.md`, PR #37) · ตัวเลขอยู่ใน `poc/P3/results/embed-gemini_gemini-embedding-2-d768.json`, `embed-gemini_gemini-embedding-2.json`, `embed-local_BAAI_bge-m3.json` (ดูได้ด้วย `git show origin/poc/P3b-embedding:<path>`) · ทำพร้อมผล flash ของ P3a
3. เมื่อ Junior approve และ report มีตาราง P3b แล้ว → `/work-done` บน branch นี้

## Waiting on

ไม่มี (Junior จะ Approve อย่างเป็นทางการตอน #39 ออกจาก draft)

## Notes for next time

- `poc/P3/out/` gitignored (มีข้อความจากชีท) · chunk อยู่ที่ `out/chunks.json` · vector อยู่ที่ `out/embed/<model>/chunks.json` (key = content_hash)
- โควตา free tier (ai.dev/rate-limit, 21 ต.ค.): Gemini Embedding 2 = 100 RPM, **30K TPM**, นับ 1 ข้อความ = 1 request · Embedding 001 ไม่มีใน key นี้ · Gemini 3.6 Flash (= `gemini-3.5-flash`) 5 RPM / 20 RPD และ request ที่ได้ 503 ก็นับ
- ภาษาไทย ≈ 1.7 ตัวอักษรต่อ Gemini token (วัดด้วย count_tokens) · ต้นทุนและการตัด chunk ของระบบจริงต้องใช้ค่านี้ ไม่ใช่ ÷3 หรือ ÷4 แบบภาษาอังกฤษ
- bge-m3 บน CPU: โหลด model ครั้งแรกต้องดาวน์โหลด torch + model ประมาณ 2–3 GB · embed 116 chunk ใช้ 409 วินาที · smoke test ใช้คำถามทิ้ง 2 ข้อใน scratchpad (ลบผลทิ้งแล้ว)
- Git Bash heredoc กับ `python -c "..."` ที่มี `$` หรือ `\` ให้ระวัง · ใช้ Write tool เขียน script เป็นไฟล์ปลอดภัยกว่า
- รัน embed ที่มิติอื่น: `cd apps/api && uv run python ../../poc/P3/embed.py --model gemini:gemini-embedding-2 --dimensions 768` · cache และผลแยกชื่อ `-d768` · 116 chunk ใช้ ~22 วินาที
- ยังไม่ใส่ `embedding.dimensions: 768` และ model ของ tier `embed` ใน `config/ai.yaml` (ไฟล์ร่วม) · ทำใน PR อัปเดต `ai.yaml` ของ S2 หลังผล P3a
- PR #54 (`data-model.md` มิติ 768 + cosine) ของ Junior: approve แล้ว · ถ้ายังไม่ merge ตอนกลับมา ให้เตือน Junior กด Merge เมื่อ CI `api-integration` เขียว
- ruff ของโค้ดนอก `apps/api` ให้รันจาก `apps/api` ด้วย `--config pyproject.toml` · ถ้ารันจาก root จะเตือน import order ของ `test_rls_isolation.py` ผิดๆ
