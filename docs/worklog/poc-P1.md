# PoC P1 · อ่านลายมือคณิต (30 รูปจาก tablet)

| | |
|---|---|
| Owner | Jam |
| Branch | `poc/P1` (ต่อจาก `poc/P3` เพื่อใช้ gateway · merge PR #15 ก่อน) |
| Checklist item | P1: รันรูปทั้งหมดกับ Gemini, Claude, Mathpix · ให้คะแนนด้วย SymPy · วาด precision–recall ของ confidence |
| Status | in progress · 2026-10-19 |

spec: `specs/poc/README.md` P1 · data: `evals/handwriting/` (30 รูป, `labels.jsonl` รอ May พิมพ์ `lines` ภายใน 22 ต.ค.) · prompt: `prompts/extract_answer/v1.md`

## Plan

- [x] 1. 🙋 Jam ตัดสิน: (ก) AI-07 ส่งรูปเพื่อนผ่านช่องทางไหน (ข) จะใช้ provider ไหนบ้าง (ค) วิธีจับคู่บรรทัดของ AI กับเฉลย
- [x] 2. 🤖 test ก่อน → `poc/P1/lines.py`: แปลง LaTeX รายบรรทัดเป็น SymPy (backend antlr · ตัด `=` นำหน้า · แยก `,` ระดับบนสุด) + ตัดสินว่า 2 บรรทัดเท่ากันไหม (string เหมือนกันหลัง normalize หรือ SymPy เท่ากัน ภายใน timeout) + จับคู่บรรทัด
- [x] 3. ~~provider ที่ยังไม่มี~~ ไม่ต้องทำ: ใช้ Gemini 2 รุ่นซึ่งมี provider อยู่แล้ว
- [x] 4. 🤖 `poc/P1/run.py`: รัน `extract_answer` ทุกรูปกับทุก provider · เก็บผลดิบ, latency, token
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

- 2026-10-19 · (Jam: ยังไม่ใช้แบบเสียเงิน) (ก) AI-07 บังคับใช้ตั้งแต่ Beta ช่วง PoC จึงยังไม่ผิด แต่ consent เดิมไม่ได้บอกว่า free tier อาจเอาข้อมูลไป train · ส่งข้อความ LINE ขอ OK เพิ่มจากทั้ง 5 คน · ใครไม่ OK ให้ตัดรูปของคนนั้นออก (ข) ใช้ `gemini-3.5-flash` (รุ่นกลางตาม spec) เทียบกับ `gemini-3.5-flash-lite` ซึ่งเป็น free tier ทั้งคู่และโควตาแยกกัน · ไม่ได้รัน Claude/Mathpix เพราะต้องเสียเงิน ต้องเขียนเป็นข้อจำกัดใน report · 30 รูปต่อรุ่นเกินโควตา 20 ครั้งต่อวัน และชนกับ P3 ที่ใช้ 3.5-flash จึงต้องรันกระจาย 2–3 วัน (ค) จับคู่บรรทัดแบบ sequence alignment (LCS): บรรทัดที่ตรงกันนับว่าถูก · บรรทัดที่เกินหรือขาดนับว่าผิด
- 2026-10-19 · `poc/P1/lines.py` เขียว 24/24 ในรอบแรก · SymPy `simplify` คิดอนุพันธ์/ลิมิตให้เอง (`d/dx(x²) - 2x` → 0) จึงแทน Derivative/Limit/Integral ด้วยสัญลักษณ์ทึบก่อน simplify (ตัวเดียวกันได้สัญลักษณ์เดียวกัน) · คำตอบหลายส่วนจับคู่แบบไม่สนลำดับ · timeout ใช้ `checker.sympy_timeout_seconds` จาก config (PoC ใช้ thread ไม่ได้ kill · ตัวจริงต้องใช้ subprocess) · ข้อจำกัด: `x(x²-1)` กับ `x³-x` นับว่าตรง (เท่ากันทางพีชคณิต)
- 2026-10-19 · `poc/P1/run.py`: เรียก `extract_answer` ทีละรูปผ่าน `Run` ของ P3 (เว้นช่วง free tier, เก็บคำตอบดิบ, log) · `--model`, `--limit`, `--exclude-writer` · cache ต่อรูปใน `poc/P1/out/<model>/` (gitignored) · ดูชนิดไฟล์จาก byte แรก (ไฟล์ของ Junior เป็น JPEG) · dry run ด้วย fake provider ผ่าน · แก้ `poc/P3/common.py` ให้ `Run` รับ `out` และ `model` (บน branch นี้ · ถ้าแก้ `common.py` บน `poc/P3` อีก ต้องระวัง conflict)

## Next step

ขั้น 5: `poc/P1/score.py` · อ่าน `labels.jsonl` (เฉพาะแถวที่ `lines` ไม่ว่าง) + `out/<model>/hw_NNN.json` → `align()` ต่อรูป → line accuracy ต่อ model (รวม และแยกตาม medium/writer) · precision–recall ของ confidence (บรรทัดที่ AI อ่านผิด = `predicted_wrong`; threshold 0.5–0.95) · latency/token ต่อรูป · เขียน `results/<model>/score.json` · test ก่อน (ส่วนที่คิด PR curve) · dry run ด้วยเฉลยปลอม

## Waiting on

May (`labels.jsonl` ภายใน 22 ต.ค.) · ทั้ง 5 คนตอบ OK เรื่อง free tier (Jam ส่งข้อความแล้วหรือยัง ให้ถามก่อนรันจริง)

## Notes for next time

- SymPy service ตัวจริง (`apps/api/app/math/`) เป็นงาน S3 ของ Junior · `poc/P1/lines.py` เป็นโค้ด PoC ใช้แล้วทิ้ง แต่สิ่งที่เจอ (antlr vs lark, กรณีพิเศษ) ควรส่งต่อให้ Junior
