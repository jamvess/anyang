# PoC P1 · อ่านลายมือคณิต (30 รูปจาก tablet)

| | |
|---|---|
| Owner | Jam |
| Branch | `poc/P1` (ต่อจาก `poc/P3` เพื่อใช้ gateway · merge PR #15 ก่อน) |
| Checklist item | P1: รันรูปทั้งหมดกับ Gemini, Claude, Mathpix · ให้คะแนนด้วย SymPy · วาด precision–recall ของ confidence |
| Status | in progress · 2026-10-20 |

## Done today (2026-10-19)

- แผน + ตัดสินใจขั้น 1 (ฟรีทั้งหมด: Gemini 3.5-flash กับ 3.5-flash-lite · ขอ consent เพิ่มเรื่อง free tier ซึ่งทั้ง 5 คน OK แล้ว · จับคู่บรรทัดด้วย LCS)
- `poc/P1/lines.py` (ตัดสินบรรทัดด้วย SymPy antlr) · `run.py` · `score.py` · README · test 30 ตัวเขียว
- อ่านรูปจริงด้วย `gemini-3.5-flash-lite` แล้ว 18/30 รูป (hw_001–hw_018 · เฉลี่ยประมาณ 3.5 วินาทีต่อรูป · ได้ 503 1 ครั้ง)
- เจอ bug ร้ายแรงเรื่อง JSON escape ของ LaTeX (ดู Decisions) · ยังไม่ได้แก้ รอ Jam ตอบ

spec: `specs/poc/README.md` P1 · data: `evals/handwriting/` (30 รูป, `labels.jsonl` รอ May พิมพ์ `lines` ภายใน 22 ต.ค.) · prompt: `prompts/extract_answer/v1.md`

## Plan

- [x] 1. 🙋 Jam ตัดสิน: (ก) AI-07 ส่งรูปเพื่อนผ่านช่องทางไหน (ข) จะใช้ provider ไหนบ้าง (ค) วิธีจับคู่บรรทัดของ AI กับเฉลย
- [x] 2. 🤖 test ก่อน → `poc/P1/lines.py`: แปลง LaTeX รายบรรทัดเป็น SymPy (backend antlr · ตัด `=` นำหน้า · แยก `,` ระดับบนสุด) + ตัดสินว่า 2 บรรทัดเท่ากันไหม (string เหมือนกันหลัง normalize หรือ SymPy เท่ากัน ภายใน timeout) + จับคู่บรรทัด
- [x] 3. ~~provider ที่ยังไม่มี~~ ไม่ต้องทำ: ใช้ Gemini 2 รุ่นซึ่งมี provider อยู่แล้ว
- [x] 4. 🤖 `poc/P1/run.py`: รัน `extract_answer` ทุกรูปกับทุก provider · เก็บผลดิบ, latency, token
- [x] 5. 🤖 `poc/P1/score.py`: line accuracy ต่อ provider · precision–recall ของ confidence ที่หลาย threshold · ต้นทุนและเวลาต่อรูป · dry run ด้วย fake provider + เฉลยปลอม
- [x] 6. 🙋 รอ May ส่ง `labels.jsonl` ที่พิมพ์แล้ว (ภายใน 22 ต.ค.) · merge แล้วใน PR #26 (20 ต.ค.)
- [x] 7. 🤖 แก้ bug escape ใน gateway บน `poc/P3`: test ก่อน → 🙋 Jam review test → แก้ `_parse` + เพิ่มประโยคใน `ai-orchestration.md` §Output → merge `poc/P3` เข้า `poc/P1`
- [x] 8. 🤖 ซ่อม cache แบบ offline: `poc/P1/out/` และ `poc/P3/out/{pages,questions}/` ด้วยฟังก์ชันเดียวกับ gateway
- [ ] 9. 🤖 อ่านรูปที่เหลือ hw_019–hw_030 (หลัง 14:00 น.) → รันให้คะแนนกับ label ของ May → สรุปผล → `/poc-report P1` · เสนอ provider + ค่า `ocr.confirm_below_confidence`

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
- 2026-10-19 · ทั้ง 5 คนตอบ OK เรื่อง free tier แล้ว (Jam ยืนยัน) · ไม่ต้อง `--exclude-writer`
- 2026-10-19 · `poc/P1/score.py` เขียว (test ของ P1 รวม 30 ตัว) · line accuracy รวม/แยกตาม medium และ writer · PR curve ที่ threshold 0.50–0.95 · เลือก threshold ต่ำสุดที่ recall ≥ 95% · latency/token ต่อรูป · ให้คะแนนเฉพาะแถวที่ `labeled_by` มีค่า · dry run ด้วยเฉลยปลอมได้ตัวเลขตามที่ควร · README ของ P1 เขียนแล้ว

- 2026-10-19 · **BUG: LaTeX หายเพราะ JSON escape** · Gemini เขียน `\frac` ลงใน JSON โดยไม่ escape backslash · `\f` `\b` `\t` `\r` `\n` เป็นรหัสพิเศษของ JSON จึงถูก parse เป็นตัวอักษรควบคุมแบบเงียบๆ (`\frac` → form feed + `rac`) · กระทบ P1 13/18 รูป และ P3: `out/pages/midterm-*.json` (form feed 88/92 จุด), `out/questions/*.json` (23/30 จุด) ซึ่งเป็น input ของ A7 · ข้อเสนอที่รอ Jam ตอบ: (1) แก้ใน gateway หลัง `json.loads` ก่อน validate: form feed/backspace → `\f`/`\b` เสมอ · tab/CR ที่ตามด้วยตัวอักษร → `\t`/`\r` · newline ที่ตามด้วย neq/nabla/not/nu/ni/ne → `\n` · newline ปกติไม่แตะ · test ก่อน (2) ซ่อมไฟล์ cache ของ P1/P3 ด้วยกฎเดียวกันแบบ offline (ไม่เสียโควตา)
- 2026-10-19 · **ผลเบื้องต้น (ไม่เป็นทางการ เทียบกับข้อความในใบลอก ไม่ใช่เฉลยของ May · และยังติด bug escape):** 3.5-flash-lite ถูก 65/75 บรรทัด (87%) · อ่านผิด 10 บรรทัด แต่ 9 บรรทัดมาจาก hw_004 (bug escape) กับ hw_009 · ไม่มี threshold ที่จับได้ ≥ 95% เพราะบรรทัดที่ผิดมี confidence 0.95–0.98 · หลังแก้ bug ต้องคิดใหม่
- 2026-10-19 · **AI อ่าน `x` เป็น `X`** (hw_009 ลายมือ Junior · ได้ 0/4 บรรทัด) · ข้อเสนอ: (1) นับว่าผิดตามจริง แล้วรายงานเป็นข้อค้นพบ (แนะนำ) (2) ให้คะแนนแบบไม่สนตัวพิมพ์ใหญ่/เล็กของตัวแปร (3) ทำ `extract_answer/v2` ให้ใช้ตัวพิมพ์เล็กถ้าไม่ชัด · hw_009 บรรทัดสุดท้ายในรูปไม่มีวงเล็บปิด AI อ่านตามจริงและเขียนไว้ใน notes ถูกต้องตามคู่มือ · hw_018 AI อ่าน `x=-1` เป็น `x=1` และ confidence ลดเหลือ 0.85 (อ่านผิดจริง)
- 2026-10-20 · (Jam เลือกตามคำแนะนำ) bug escape: แก้ตามข้อเสนอ (1)+(2) · ทำบน `poc/P3` แล้ว merge `poc/P3` เข้า `poc/P1` เพราะ P1 แตกจาก P3 (ถ้าทำกลับทาง โค้ด P1 จะติดไปใน P3) · เพิ่มประโยคเรื่องการซ่อมใน `ai-orchestration.md` §Output ใน PR เดียวกัน เพราะเป็น behavior ใหม่ของ gateway · `gateway.py` เป็นไฟล์ของ Junior: แจ้งในกลุ่มแล้วให้ Junior review
- 2026-10-20 · (Jam เลือกตามคำแนะนำ) `x` อ่านเป็น `X`: นับว่าผิดตามจริง แล้วรายงานเป็นข้อค้นพบใน report · ไม่แก้ prompt ระหว่าง PoC เพื่อให้ตัวเลขตรงความจริง
- 2026-10-20 · gateway ซ่อม escape แล้ว (`repair_unescaped_latex` · commit บน `poc/P3` แล้ว merge เข้ามา) · **ผลกระทบจริงน้อยกว่าที่เขียนไว้วันที่ 19:** P1 โดนแค่ hw_004 (form feed 9 จุด ใน 5 บรรทัด) ไม่ใช่ 13/18 · P3 ไม่โดนเลย · ซ่อม hw_004 แล้วด้วยฟังก์ชันเดียวกับ gateway (script ใช้ครั้งเดียว ไม่ได้ commit · สำรองไว้ที่ `out/gemini-3.5-flash-lite/hw_004.json.bak`) · scan ซ้ำแล้ว 0/18 · (Jam เลือกตามคำแนะนำ) กฎ newline ไม่ซ่อม `\ne` `\ni` `\nu` `\not` เพราะชนกับข้อความคณิตปกติ (รายละเอียดอยู่ใน `ai-orchestration.md` §Output)
- 2026-10-20 · **ผลเบื้องต้นกับ label ของ May (18/30 รูป · 3.5-flash-lite · หลังซ่อม hw_004):** line accuracy 70/75 = 93.3% (ผ่านเป้า 80%) · อ่านผิด 5 บรรทัด: hw_009 4 บรรทัด (`x` เป็น `X` · confidence 0.95–0.98) และ hw_018 1 บรรทัด (`x=-1` เป็น `x=1` · 0.85) · ยังไม่มี threshold ไหนจับได้ ≥ 95% (ที่ 0.90 จับได้ 1/5) เพราะ confidence ของ hw_009 สูง · latency เฉลี่ย 3.4 วินาที (p95 5.6) · token ต่อรูป 1,609 in / 182 out · `results/` ยังไม่ commit เพราะยังไม่ครบ 30 รูป
- 2026-10-20 · **label hw_009 บรรทัด 4 ไม่ตรงกับรูป:** ในรูปเขียน `=(2x-3)(x+2` (ไม่มีวงเล็บปิด) แต่ label เป็น `=(2x-3)(x+2)` ซึ่งขัดกับกฎข้อ 1 ใน `evals/README.md` (พิมพ์ตามที่เขียน) · ตัว `x` ในรูปนี้ก็ดูคล้าย `X` ด้วย · (Jam เลือกตามคำแนะนำ) ส่งให้ May แก้เอง เพราะคนทำ PoC ไม่ควรแก้ label เอง · ตัวเลขไม่เปลี่ยนเพราะบรรทัดนี้ผิดจาก X อยู่แล้ว · ใน report ให้เขียนว่า x ในรูปนี้กำกวม

## Next step

หลัง 14:00 น. (เช็คโควตาด้วย request เดียวก่อน): `cd apps/api && uv run python ../../poc/P1/run.py --model gemini:gemini-3.5-flash-lite` (อ่าน hw_019–hw_030 ที่เหลือ) → `score.py` กับ label ของ May · ก่อนถึงเวลานั้นรัน `score.py` กับ 18 รูปที่มีอยู่ได้เลย (ไม่ใช้โควตา)

## Waiting on

โควตา free tier รีเซ็ต 20 ต.ค. ≈ 14:00 น. · May แก้ label hw_009 บรรทัด 4 · Junior review การแก้ gateway (PR #15)

## Notes for next time

- preview script (เทียบกับใบลอก) อยู่ใน scratchpad ของ session 2026-10-19: อ่าน `S` จาก `evals/handwriting/raw/copy-sheets/build_sheets.py` และ map hw → version จาก `copy_sheets_key.md` (ทั้งสองไฟล์ gitignored อยู่ในเครื่อง Jam) · ห้ามใช้เป็นผลทางการ และห้ามให้ May เห็น

- SymPy service ตัวจริง (`apps/api/app/math/`) เป็นงาน S3 ของ Junior · `poc/P1/lines.py` เป็นโค้ด PoC ใช้แล้วทิ้ง แต่สิ่งที่เจอ (antlr vs lark, กรณีพิเศษ) ควรส่งต่อให้ Junior
