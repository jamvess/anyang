# อัปเดต config ตามผล P1 + P3

| | |
|---|---|
| Owner | Jam |
| Branch | `chore/config-after-p1-p3` |
| Checklist item | อัปเดต `config/learning.yaml` (`ocr.confirm_below_confidence`, `stars.*`) และ `config/ai.yaml` (model ที่เลือก) ผ่าน PR |
| Status | in progress · 2026-10-21 |

## Plan

- [ ] 1. 🙋 Jam ส่งข้อความในกลุ่ม: จะแก้ `config/ai.yaml` (ไฟล์ร่วม) และขอ Junior อนุญาตแก้ test `test_AI02_live_mode_refuses_placeholder_model_ids` ให้ใช้ purpose ที่ tier ยังเป็น TODO (เพราะ tier `mid` จะมี model จริงแล้ว)
- [x] 2. 🙋 Jam ตัดสิน: prefix ของ model (`vertex:` หรือ `gemini:`) · tier `small` ใส่หรือปล่อย TODO
- [ ] 3. 🤖 แก้ test ข้อ 1 (ถ้า Junior ok) ให้ red ก่อน แล้วแก้ `config/ai.yaml`: `vision` (P1), `embed` + `embedding.dimensions: 768` (P3b), `mid` (P3 A5), `main` ชั่วคราว (P3 A6 ยังไม่ได้วัด) · ทุกบรรทัดอ้าง report
- [ ] 4. 🤖 `config/learning.yaml` → `stars.three_star_min_r` ค่าเดิม ป้ายเพิ่มผล P3 · `stars.weight_other_instructor` คง [C] (P3 วัด overlap ไม่ได้) · `specs/system/learning-model.md` แถว `three_star_min_r` และตาราง calibrate
- [ ] 5. 🤖 รัน pytest + ruff ของ api

## Definition of done

- `config/ai.yaml` ไม่มี TODO ใน tier ที่ P1/P3 ตัดสินแล้ว และทุกค่าอ้าง report (P1.md, P3.md)
- `config/learning.yaml` + `learning-model.md` บันทึกผล P3 ของ `stars.*` (ส่วน `ocr` ทำแล้วใน PR #45)
- test ของ api ผ่าน · ทีมรู้เรื่องการแก้ไฟล์ร่วม

## Decisions

- 2026-10-21 · ทำระหว่างรอ flash รอบ 16:00 น. ของ P3 · ถ้ารอบนั้นได้ผล A6 อาจต้องแก้ tier `main` อีกครั้ง

- 2026-10-21 · (Jam เลือก a a) prefix `vertex:` ตามแผน architecture + AI-07 (Beta ห้าม free tier) · ยังไม่มี Vertex provider → error "no provider" ชัดเจน · PoC ใช้ `AI_MODEL_OVERRIDE` ไม่กระทบ · tier `small` ปล่อย TODO (ยังไม่ได้เทียบ flash กับ lite ในงานของ small)

## Next step

ข้อ 1: Jam ส่งข้อความในกลุ่ม (ร่างอยู่ในแชท)

## Waiting on

ทีมตอบเรื่อง `ai.yaml` + Junior ตอบเรื่อง test

## Notes for next time

- `Gateway._route` แยก provider จาก prefix ก่อน `:` · `vertex:` ยังไม่มี provider (มีแค่ `gemini:` ที่ใช้ API key) → ถ้าใช้ `vertex:` ระบบจริงจะ error "no provider" จนกว่าจะมี Vertex provider · PoC ใช้ `AI_MODEL_OVERRIDE` จึงไม่กระทบ
