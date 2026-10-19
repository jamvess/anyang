# PoC P1 · อ่านลายมือคณิต (30 รูปจาก tablet)

| | |
|---|---|
| Owner | Jam |
| Branch | `poc/P1` (ต่อจาก `poc/P3` เพื่อใช้ gateway · merge PR #15 ก่อน) |
| Checklist item | P1: รันรูปทั้งหมดกับ Gemini, Claude, Mathpix · ให้คะแนนด้วย SymPy · วาด precision–recall ของ confidence |
| Status | in progress · 2026-10-19 |

spec: `specs/poc/README.md` P1 · data: `evals/handwriting/` (30 รูป, `labels.jsonl` รอ May พิมพ์ `lines` ภายใน 22 ต.ค.) · prompt: `prompts/extract_answer/v1.md`

## Plan

- [ ] 1. 🙋 Jam ตัดสิน: (ก) AI-07 ส่งรูปเพื่อนผ่านช่องทางไหน (ข) จะใช้ provider ไหนบ้าง (ค) วิธีจับคู่บรรทัดของ AI กับเฉลย
- [ ] 2. 🤖 test ก่อน → `poc/P1/lines.py`: แปลง LaTeX รายบรรทัดเป็น SymPy (backend antlr · ตัด `=` นำหน้า · แยก `,` ระดับบนสุด) + ตัดสินว่า 2 บรรทัดเท่ากันไหม (string เหมือนกันหลัง normalize หรือ SymPy เท่ากัน ภายใน timeout) + จับคู่บรรทัด
- [ ] 3. 🤖 provider ที่ยังไม่มีตามข้อ 1 (เช่น Claude) ใน `apps/api/app/ai/providers/` · test ก่อน
- [ ] 4. 🤖 `poc/P1/run.py`: รัน `extract_answer` ทุกรูปกับทุก provider · เก็บผลดิบ, latency, token
- [ ] 5. 🤖 `poc/P1/score.py`: line accuracy ต่อ provider · precision–recall ของ confidence ที่หลาย threshold · ต้นทุนและเวลาต่อรูป · dry run ด้วย fake provider + เฉลยปลอม
- [ ] 6. 🙋 รอ May ส่ง `labels.jsonl` ที่พิมพ์แล้ว (ภายใน 22 ต.ค.)
- [ ] 7. 🤖 รันจริง → สรุปผล → `/poc-report P1` · เสนอ provider + ค่า `ocr.confirm_below_confidence`

## Definition of done

- รันซ้ำได้ด้วยคำสั่งเดียวตาม `poc/P1/README.md`
- มีตัวเลขเทียบเป้า: line accuracy ≥ 80% ต่อ provider · threshold ที่จับบรรทัดอ่านผิดได้ ≥ 95% · ต้นทุนและ latency ต่อรูป
- ทุก AI call ผ่าน `ai.call()` · test ผ่าน · report P1 ร่างแล้ว พร้อมข้อจำกัดว่ารูปทั้งหมดมาจาก tablet

## Decisions

- 2026-10-19 · `poc/P1` แตกจาก `poc/P3` เพราะ gateway ยังอยู่ใน PR #15 · ต้อง merge PR #15 ก่อน PR นี้
- 2026-10-19 · ให้คะแนนด้วย `sympy.parsing.latex.parse_latex(backend="antlr")` (ต้องใช้ `antlr4-python3-runtime==4.11`) · backend `lark` parse ผิดแบบเงียบๆ (`2x\sin(x)+x^{2}\cos(x)` → `2x·sin(x²+x)·cos(x)`) จึงห้ามใช้ · antlr ยังต้องแก้เอง 2 กรณี: บรรทัดที่ขึ้นต้นด้วย `=` และ `x=0, x=\ln(2)` (ส่วนหลัง comma หายไปเงียบๆ)

## Next step

ขั้น 1: Jam ตอบ 3 เรื่องในแชท

## Waiting on

Jam (ขั้น 1) · May (`labels.jsonl` ภายใน 22 ต.ค.)

## Notes for next time

- SymPy service ตัวจริง (`apps/api/app/math/`) เป็นงาน S3 ของ Junior · `poc/P1/lines.py` เป็นโค้ด PoC ใช้แล้วทิ้ง แต่สิ่งที่เจอ (antlr vs lark, กรณีพิเศษ) ควรส่งต่อให้ Junior
