# ปรับ threshold ใน AI flow specs และ learning-model ตามผล P1 P2 P3

| | |
|---|---|
| Owner | Jam |
| Branch | `docs/thresholds-from-poc` |
| Checklist item | อัปเดต threshold ใน AI flow specs และ `learning-model.md` ตามผล P1 P2 P3 (D2) |
| Status | in progress · 2026-10-31 |

## Plan

- [x] 1. 🤖 ทำรายการทุกค่าที่ผูกกับ PoC: ทุก key ใน `config/learning.yaml` ที่ป้ายพูดถึง P1/P2/P3 หรือรอ PoC · ตาราง calibration ใน `learning-model.md` §9 · ตัวเลขใน `ai-orchestration.md` (flow 2.3 ingest, 2.4 checker, 2.10 routing, latency/ต้นทุน) · เทียบกับตัวเลขใน `specs/poc/reports/P1.md`, `P2.md`, `P3.md` · ทำเป็นตาราง: ค่า · ตอนนี้ · PoC วัดได้อะไร · ข้อเสนอ (คง / เปลี่ยน / ยังรอ + ป้ายที่มา)
- [x] 2. 🙋 Jam ตัดสินทีละแถวในตาราง (ตอบเป็นเลขแถว หรือ "ok ทุกแถว")
- [x] 3. 🤖 แก้ตามที่ตัดสิน: `learning-model.md` (ตารางค่าและ §9), `ai-orchestration.md` (เฉพาะ flow ที่ PoC วัด) · ไม่เปลี่ยนหลักการ
- [x] 4. 🤖 แก้ `config/learning.yaml` (ค่าหรือป้ายที่มา) ถ้ามีแถวที่ต้องเปลี่ยน · รัน `uv run pytest` เพราะ test อ่าน config · ไฟล์นี้ Jam + Junior เป็นเจ้าของ (CODEOWNERS)
- [ ] 5. 🙋 Jam บอกแชทกลุ่มก่อน merge (ถ้าแก้ `config/learning.yaml`) · ข้อความจะร่างให้

## Definition of done

- ไม่มีค่าใน `config/learning.yaml`, `learning-model.md`, `ai-orchestration.md` ที่ยังเขียนว่ารอผล P1, P2 หรือ P3 · ค่าที่ PoC วัดไม่ได้ระบุว่าวัดเมื่อไหร่แทน
- ทุกค่าที่เปลี่ยนมีป้าย [A]/[B]/[calc]/[C] และอ้าง report ของ PoC
- `uv run pytest` และ `uv run ruff check .` ผ่าน (ถ้าแตะ config)
- ตรงกับ checklist: "อัปเดต threshold ใน AI flow specs และ `learning-model.md` ตามผล P1 P2 P3 (D2)"

## ตารางขั้น 1 (31 ต.ค. · รอ Jam ตัดสิน)

ไม่มีค่าไหนที่ผล P1 P2 P3 บอกให้เปลี่ยนตัวเลข · ทุกแถวเป็นการแก้ป้ายที่มา หรือเติมผลลงใน spec

| # | ค่า / ที่อยู่ | ตอนนี้ | PoC วัดได้อะไร | ข้อเสนอ |
|---|---|---|---|---|
| 1 | `checker.sympy_timeout_seconds` (yaml + LM §8) | 2 วินาที [calc] | P2: median 0.14, ช้าสุด 0.44 วินาที, timeout 0/50 | **คง 2** · เพิ่มหลักฐาน P2 ในป้าย |
| 2 | `checker.numeric_rel_tolerance` (yaml + LM §8) | 0.01 [C] · "P2 วัดว่าทศนิยมตัดสินผิดกี่ข้อ" | P2 ไม่มีโจทย์ `numeric` (expression 30, equation 11, factored 9) | **คง** · ป้ายใหม่: P2 วัดไม่ได้ · วัดตอนทำ `numeric` (Should) |
| 3 | `checker.max_generate_retries` (yaml + LM §8) | 2 [C] · "P2/S3" | P2 ไม่ได้ทดสอบ `generate_problem` (ยังไม่มีใน code) | **คง** · ป้ายใหม่: วัดตอนมี `generate_problem` ในห้องติว |
| 4 | LM §8 แถว Checker targets | เป้า 95 / 80 / 85% | P2: 100% / 96.4% / 100% ผ่าน | **เติมผล P2** |
| 5 | LM §9 แถว "P2 (S3) สัญญาณแยกบรรทัดที่อ่านผิด" + ป้าย `ocr.always_confirm` "S3: try a better signal" | รอ P2 | P2 ใช้บรรทัดจาก label ไม่ได้อ่าน OCR · `extract_answer/v2` ยังไม่ได้ทำ | **ยังรอ** · ย้ายไปช่วงอื่น (Jam เลือก: S4 / เทอม 2) |
| 6 | LM §9 เพิ่มแถว P2 | ไม่มี | ตามแถว 1–4 | **เพิ่ม** "PoC P2 (S3) · ทำแล้ว" |
| 7 | `stars.*`, `grounding_chunks` (P3) | ติดป้าย P3 แล้ว (PR #60, #89) | — | **คง** ไม่ต้องแก้ |
| 8 | `checker.sympy_workers`, `planner.default_minutes_per_problem` | รอ P4-lite | ไม่ใช่ P1–P3 | **คง** ไม่อยู่ในงานนี้ |
| 9 | AO §2.10 ตาราง tier | main/embed "เลือกจาก spike" · vision "รุ่นกลาง · Mathpix ถ้า OCR < 80%" | P1 flash-lite 95.2% · P3 A5 flash, A6 วัดไม่ได้ · P3b embedding-2 @768 · P2 flash | **เปลี่ยนให้ตรง `ai.yaml` 1.3** · main = flash ชั่วคราว (A6 รอวัด P3a บน Vertex: Jam เลือก S4 / เทอม 2) |
| 10 | AO §2.10 เป้า ≤ 5 บาท, TTFT p95 < 2 วินาที | "วัดจริงใน PoC" | ไม่ใช่ P1–P3 | **ยังรอ** · ระบุว่า P4-lite (S3) |
| 11 | AO §2.3.7 A2b "จะใช้แทน A2 หรือไม่ ตัดสินจากผล P3" | รอ P3 | P3: A2b 14 หน้า 40.5 วินาที · A4 ตัดข้อตรง 43/43 | **ตัดสิน:** ไฟล์สแกนใช้ A2b ทั้งไฟล์ · A2 เฉพาะรูปเดี่ยว |
| 12 | AO §3.6 แถว topic extraction, embedding, checker | ยังไม่มีผล | P3a ❌ · P3b ✅ · P2 ✅ | **เติมผล** แบบแถว P1 |
| 13 | `ai.yaml` `embedding.timeout_s` + comment "confirm from P3 logs" (ไฟล์กลาง · นอกแผน) | 60 [C] | P3b: 116 chunk 21.6 วินาที (~1.8 วินาที/batch) · A6 ใช้ token out 93% ของ 16,000 | **คง** · แก้ป้าย (ถ้าทำต้องบอกกลุ่ม) หรือข้าม |

LM = `learning-model.md` · AO = `ai-orchestration.md` · นอกงานนี้ (เปลี่ยนหลักการ): P3 เสนอให้ code ตั้ง skill id เองแทน LLM (A6)

## Decisions

- 31 ต.ค. Jam ok ทุกแถวของตารางขั้น 1
- แถว 5 → **เทอม 2**: S3–S4 งานเต็มแล้ว และการยืนยันทุกครั้ง (AM-02) ยังใช้ได้อยู่
- แถว 9 → **S4**: วัด P3a ใหม่บน Vertex ก่อน demo รวม เพราะ demo ต้องแสดง upload → scope และ report §3 ต้องใช้ตัวเลขนี้
- แถว 13 → **ทำ**: แก้ comment ใน `config/ai.yaml` (ไฟล์กลาง · ค่าไม่เปลี่ยน · ต้องบอกกลุ่มในขั้น 5)

## Next step

ขั้น 5 (🙋): Jam ส่งข้อความที่ร่างไว้ในแชทกลุ่ม (แก้ `config/learning.yaml` 1.4 + `config/ai.yaml` 1.4 แค่ป้าย ค่าไม่เปลี่ยน) แล้วรัน `/work-done`

## Waiting on

ไม่มี

## Notes for next time

- 28 ต.ค. PR #73 ทำ learning-model v1.2 จากการทบทวน design (ไม่ได้มาจากผล PoC) · งานนี้คือส่วนที่เหลือ: ปรับตามผล PoC
- ค่าที่ทำไปแล้วในงานอื่น: `ocr.always_confirm` (P1 · PR #45) · `stars.*` ป้าย P3 (PR #60) · `stars.no_past_exam_method` (PR #89) · `grounding_chunks` ป้าย P3b
