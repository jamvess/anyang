# PoC P3b · embedding ภาษาไทย (MTH10101)

| | |
|---|---|
| Owner | Jam |
| Branch | `poc/P3b-embedding` |
| Checklist item | P3: ingest → A5 → A6 → A7 → `compute_importance` · เทียบกับ label · ลอง embedding 2–3 ตัวกับคำถาม 20 ข้อ (ส่วน embedding · ส่วน P3a อยู่ใน PR #37) |
| Status | in progress · 2026-10-20 |

spec: `specs/poc/README.md` P3 (metric: recall@4 ของ retrieval · ผลที่ต้องได้: embedding model + มิติ vector + ขนาด chunk) · `specs/system/ai-orchestration.md` §1.4 Retrieval, §2.3.3 Chunk/Embed · AI-01, AI-08

## Plan

- [ ] 1. 🤖 ตัด chunk ของชีท 4 ไฟล์ตาม §2.3.3 (400–800 tokens ไม่คร่อมเกิน 2 หน้า) จากข้อความ PyMuPDF ที่ ingest ไว้แล้ว · ทำเทมเพลตคำถาม `evals/topics/mth10101/retrieval_questions.jsonl` + คู่มือ + รายชื่อหัวข้อจาก label ให้กระจายคำถามครบ
- [ ] 2. 🙋 **May (หรือ Junior) เขียนคำถาม 20 ข้อ + เฉลยหน้า** (ไม่ใช่ Jam · คน label ไม่ใช่คนทำ PoC) · Jam ส่งงานในกลุ่ม
- [ ] 3. 🙋 Jam ตัดสิน model ที่จะลอง 2–3 ตัว และวิธีเรียก embedding ผ่าน provider layer (AI-01)
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

## Next step

Jam review test ของ chunking + เทมเพลตคำถาม → ถ้า ok: implement `chunking.py` แล้วตัด chunk จริงจาก `poc/P3/out/pages/sheet-*.json` · Jam ส่งเทมเพลตให้ May/Junior

## Waiting on

ไม่มี

## Notes for next time

- `poc/P3/out/` gitignored (มีข้อความจากชีท) · chunk และ vector เก็บใน `out/` เหมือนกัน
