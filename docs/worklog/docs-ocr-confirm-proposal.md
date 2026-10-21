# ข้อเสนอเปลี่ยน AM-02 + ocr.confirm_below_confidence ตามผล P1

| | |
|---|---|
| Owner | Jam |
| Branch | `docs/ocr-confirm-proposal` |
| Checklist item | อัปเดต `config/learning.yaml` (`ocr.confirm_below_confidence`, `stars.*`) และ `config/ai.yaml` (model ที่เลือก) ผ่าน PR (ส่วน `ocr` เท่านั้น · `stars.*` และ `ai.yaml` รอผล P3) |
| Status | in progress · 2026-10-21 |

ที่มา: `specs/poc/reports/P1.md` §4–§5 · confidence ที่ model ให้ตัวเองแยกบรรทัดผิดไม่ได้ (0.85–0.98) · threshold ไม่มีค่าไหนจับได้ ≥ 95%

## Plan

- [x] 1. 🤖 ร่างข้อเสนอให้ทีมตัดสิน (ใน PR description + ข้อความกลุ่ม): ทางเลือก, ผลกระทบต่อ UX/API/ไฟล์ของแต่ละคน, ข้อเสนอแนะ · รวมเรื่อง "ส่งรูปพร้อมข้อความกำกับ" ที่ `api.md` รอ Jam อยู่ (flow เดียวกัน)
- [ ] 2. 🙋 Jam ส่งในกลุ่ม · ทีมตัดสิน (Junior: API/checker · May: UI กล่องยืนยัน)
- [ ] 3. 🤖 แก้ตามที่ตัดสิน: `requirements.md` AM-02 (ไฟล์กลาง) · `learning.yaml` `ocr.*` + `learning-model.md` §8–9 · `ai-orchestration.md` §2.2.5, §2.2.10, §3.5, §3.6 · `specs/poc/README.md` P1 · `api.md` ข้อรอตัดสิน (ไฟล์กลาง)
- [ ] 4. 🤖 checklist: sub-bullet ใต้ข้อ "อัปเดต config" ว่าส่วน ocr เสร็จ · `/work-done` · reviewer ทั้ง Junior และ May (ไฟล์กลาง)

## Definition of done

- ทีมตัดสินแล้ว (บันทึกในกลุ่มหรือ PR)
- spec, requirement และ config ตรงกับที่ตัดสิน · ค่าใน `learning.yaml` มีป้ายที่มาอ้าง P1 report
- `api.md` ข้อ "ส่งรูปพร้อมข้อความกำกับ" มีคำตอบ

## Decisions

- 2026-10-21 · เลือกทำข้อนี้ระหว่างรอโควตา (P3) และรอคำถามของ May (P3b) · ทำเฉพาะส่วน `ocr` ของข้อ "อัปเดต config"
- 2026-10-21 · ข้อเสนออยู่ใน description ของ PR #45 · เรื่อง 1 (AM-02): ก ยืนยันทุกครั้ง (แนะนำ) / ข threshold 0.95 (ใน P1 จับ 2 กรณีที่อันตรายได้ แต่พลาด X ทั้ง 4 · ตัวอย่างน้อย) / ค คง 0.8 · เรื่อง 2 (รูป + ข้อความ): ก เป็น caption ไม่ส่งเข้า OCR/checker (แนะนำ) / ข เป็น context ของ checker / ค ไม่รับ

## Next step

🙋 Jam ส่งข้อเสนอในกลุ่ม (ลิงก์ PR #45) · รอทีมตอบเรื่อง 1 และ 2 · แล้วขั้น 3 แก้ไฟล์ตามที่ตัดสิน

## Waiting on

ทีม (Junior, May) ตอบเรื่อง 1 และ 2 ในกลุ่มหรือ PR #45

## Notes for next time

- `poc/` อาจขึ้นเป็น untracked (out/ ของ P1/P3) · ห้าม commit
