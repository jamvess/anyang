# PoC P3b · embedding ภาษาไทย (MTH10101)

| | |
|---|---|
| Owner | Jam |
| Branch | `poc/P3b-embedding` |
| Checklist item | P3: ingest → A5 → A6 → A7 → `compute_importance` · เทียบกับ label · ลอง embedding 2–3 ตัวกับคำถาม 20 ข้อ (ส่วน embedding · ส่วน P3a อยู่ใน PR #37) |
| Status | in progress · 2026-10-21 |

spec: `specs/poc/README.md` P3 (metric: recall@4 ของ retrieval · ผลที่ต้องได้: embedding model + มิติ vector + ขนาด chunk) · `specs/system/ai-orchestration.md` §1.4 Retrieval, §2.3.3 Chunk/Embed · AI-01, AI-08

## Plan

- [x] 1. 🤖 ตัด chunk ของชีท 4 ไฟล์ตาม §2.3.3 (400–800 tokens ไม่คร่อมเกิน 2 หน้า) จากข้อความ PyMuPDF ที่ ingest ไว้แล้ว · ทำเทมเพลตคำถาม `evals/topics/mth10101/retrieval_questions.jsonl` + คู่มือ + รายชื่อหัวข้อจาก label ให้กระจายคำถามครบ
- [ ] 2. 🙋 **May (หรือ Junior) เขียนคำถาม 20 ข้อ + เฉลยหน้า** (ไม่ใช่ Jam · คน label ไม่ใช่คนทำ PoC) · Jam ส่งงานในกลุ่ม
- [x] 3. 🙋 Jam ตัดสิน model ที่จะลอง 2–3 ตัว และวิธีเรียก embedding ผ่าน provider layer (AI-01)
- [ ] 4. 🤖 test ก่อน → โค้ด spike `poc/P3/embed.py`: embed chunk + คำถาม · recall@4 ต่อ model · มิติ vector · เวลา · ต้นทุน → 🙋 Jam review test
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

## Next step

รัน smoke test ด้วย `local:BAAI/bge-m3` (`uv run --with sentence-transformers`) · Jam เช็คโควตา embedding ที่ ai.dev/rate-limit · รอ May เขียนคำถาม

## Waiting on

May (หรือ Junior) เขียนคำถาม 20 ข้อ (ขั้น 2)

## Notes for next time

- `poc/P3/out/` gitignored (มีข้อความจากชีท) · chunk และ vector เก็บใน `out/` เหมือนกัน
