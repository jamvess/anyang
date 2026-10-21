# อัปเดต config ตามผล P1 + P3

| | |
|---|---|
| Owner | Jam |
| Branch | `chore/config-after-p1-p3` |
| Checklist item | อัปเดต `config/learning.yaml` (`ocr.confirm_below_confidence`, `stars.*`) และ `config/ai.yaml` (model ที่เลือก) ผ่าน PR |
| Status | in progress · 2026-10-21 |

## Plan

- [x] 1. 🙋 Jam ส่งข้อความในกลุ่ม: จะแก้ `config/ai.yaml` (ไฟล์ร่วม) และขอ Junior อนุญาตแก้ test `test_AI02_live_mode_refuses_placeholder_model_ids` ให้ใช้ purpose ที่ tier ยังเป็น TODO (เพราะ tier `mid` จะมี model จริงแล้ว)
- [x] 2. 🙋 Jam ตัดสิน: prefix ของ model (`vertex:` หรือ `gemini:`) · tier `small` ใส่หรือปล่อย TODO
- [x] 3. 🤖 แก้ test ข้อ 1 (ถ้า Junior ok) ให้ red ก่อน แล้วแก้ `config/ai.yaml`: `vision` (P1), `embed` + `embedding.dimensions: 768` (P3b), `mid` (P3 A5), `main` ชั่วคราว (P3 A6 ยังไม่ได้วัด) · ทุกบรรทัดอ้าง report
- [x] 4. 🤖 `config/learning.yaml` → `stars.three_star_min_r` ค่าเดิม ป้ายเพิ่มผล P3 · `stars.weight_other_instructor` คง [C] (P3 วัด overlap ไม่ได้) · `specs/system/learning-model.md` แถว `three_star_min_r` และตาราง calibrate
- [x] 5. 🤖 รัน pytest + ruff ของ api

## Definition of done

- `config/ai.yaml` ไม่มี TODO ใน tier ที่ P1/P3 ตัดสินแล้ว และทุกค่าอ้าง report (P1.md, P3.md)
- `config/learning.yaml` + `learning-model.md` บันทึกผล P3 ของ `stars.*` (ส่วน `ocr` ทำแล้วใน PR #45)
- test ของ api ผ่าน · ทีมรู้เรื่องการแก้ไฟล์ร่วม

## Decisions

- 2026-10-21 · ทำระหว่างรอ flash รอบ 16:00 น. ของ P3 · ถ้ารอบนั้นได้ผล A6 อาจต้องแก้ tier `main` อีกครั้ง

- 2026-10-21 · (Jam เลือก a a) prefix `vertex:` ตามแผน architecture + AI-07 (Beta ห้าม free tier) · ยังไม่มี Vertex provider → error "no provider" ชัดเจน · PoC ใช้ `AI_MODEL_OVERRIDE` ไม่กระทบ · tier `small` ปล่อย TODO (ยังไม่ได้เทียบ flash กับ lite ในงานของ small)

- 2026-10-21 · ข้อ 4 (ทำก่อนข้อ 3 ระหว่างรอ Junior · Jam ok): ค่าไม่เปลี่ยนเลย แก้แค่ป้าย/หมายเหตุ · `three_star_min_r` ★★★ 10/12 = 83% ยืนยันได้แค่ > 0.5 · `weight_other_instructor` คง [C] P3 วัดไม่ได้ · `grounding_chunks` คง 4 จาก P3b recall@4 19/20 · `learning-model.md` 3 แถว + ตารางแผน calibrate

- 2026-10-21 · ข้อ 1: Junior ok ต่อหน้า Jam (ทั้ง `ai.yaml` และแก้ test) · ให้ Junior approve PR เพื่อเป็นหลักฐานใน repo
- 2026-10-21 · ข้อ 3: test เปลี่ยนวิธี (Junior ok): สร้าง config ที่ tier `mid` เป็น TODO เองใน test แทนการพึ่ง `ai.yaml` · สิ่งที่ตรวจเหมือนเดิม · `ai.yaml` v1.2: vision = `vertex:gemini-3.5-flash-lite` (P1) · mid = `vertex:gemini-3.5-flash` (P3 A5) · main = flash ชั่วคราว (A6 0/20) · embed = `vertex:gemini-embedding-2` · small คง TODO
- 2026-10-21 · **`embedding.dimensions: 768` ไม่ได้ใส่ใน PR นี้** เพราะ section `embedding` และ `EmbeddingConfig.dimensions` อยู่ใน #39 ยังไม่ merge (config เป็น `_Strict` ใส่ key ที่ไม่รู้จักจะ error) → ใส่ใน #39 แทน
- 2026-10-21 · ข้อ 5: ruff ผ่าน · api 156 ผ่าน · PoC P3 12, P1 30 (ต้อง `--with antlr4-python3-runtime==4.11.*`) · รัน `pytest ../../poc` รวมกันแล้ว error เพราะ `score.py` ของ P1 กับ P3 ชื่อซ้ำ (มีอยู่แล้วบน main ไม่ได้เกิดจาก PR นี้)

## Next step

ครบทุกขั้นแล้ว · ก่อน `/work-done`: เพิ่ม `dimensions: 768` ใน section `embedding` ของ `config/ai.yaml` บน branch `poc/P3b-embedding` (#39) · แล้ว `/work-done` PR นี้ (reviewer: Junior + May เพราะ `ai.yaml` เป็นไฟล์ร่วม) · ติ๊ก checklist ข้อ config ได้ (ocr ทำใน #45, stars + model ทำใน PR นี้)

## Waiting on

ไม่มี

## Notes for next time

- `Gateway._route` แยก provider จาก prefix ก่อน `:` · `vertex:` ยังไม่มี provider (มีแค่ `gemini:` ที่ใช้ API key) → ถ้าใช้ `vertex:` ระบบจริงจะ error "no provider" จนกว่าจะมี Vertex provider · PoC ใช้ `AI_MODEL_OVERRIDE` จึงไม่กระทบ
