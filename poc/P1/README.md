# PoC P1 · อ่านลายมือคณิต (30 รูปจาก tablet)

spec: `specs/poc/README.md` P1 · data: `evals/handwriting/` · prompt: `prompts/extract_answer/v1.md` · worklog: `docs/worklog/poc-P1.md`

## รัน

ต้องมี `GEMINI_API_KEY` ใน `.env` (`docs/team/setup.md` A5) · ต้องมีรูปใน `evals/handwriting/raw/` และ May ต้อง label `labels.jsonl` แล้ว

```bash
cd apps/api
# 1) อ่านรูป (free tier ได้ 20 ครั้งต่อวันต่อ model · รันซ้ำวันถัดไปจะทำต่อจากรูปที่ค้าง)
uv run python ../../poc/P1/run.py --model gemini:gemini-3.5-flash-lite --limit 18
uv run python ../../poc/P1/run.py --model gemini:gemini-3.5-flash --limit 8
# 2) ให้คะแนน
uv run --with "antlr4-python3-runtime==4.11.*" python ../../poc/P1/score.py \
    --model gemini:gemini-3.5-flash --model gemini:gemini-3.5-flash-lite
```

- `--exclude-writer w04` ข้ามรูปของคนที่ไม่ OK เรื่อง free tier (Google อาจนำข้อมูลไปใช้พัฒนาโมเดล)
- ผลการอ่านอยู่ใน `out/<model>/` (gitignored) · คะแนนอยู่ใน `results/<model>/score.json` (มีแค่ตัวเลขและ id ของรูป)

## ให้คะแนนอย่างไร

| เรื่อง | วิธี |
|---|---|
| บรรทัดตรงไหม | ข้อความเหมือนกันหลังตัดช่องว่างและ `\left`/`\right` ออก หรือ SymPy บอกว่าเท่ากัน (`lines.py`) · **อนุพันธ์ ลิมิต และอินทิกรัล เทียบตามที่เขียน ไม่คิดค่าให้** · สมการสลับข้างได้ · คำตอบหลายส่วนสลับลำดับได้ |
| จับคู่บรรทัด | LCS: จับคู่ตามลำดับให้ได้มากที่สุด · บรรทัดที่ AI อ่านเกินหรืออ่านผิดนับเป็น "อ่านผิด" |
| line accuracy | บรรทัดที่จับคู่ได้ ÷ บรรทัดในเฉลย (ไม่นับ `unclear_lines`) · เป้า ≥ 80% |
| threshold | ค่าที่ต่ำที่สุดใน 0.50–0.95 ที่ flag บรรทัดที่อ่านผิดได้ ≥ 95% · ยิ่งต่ำ ผู้ใช้ยิ่งต้องยืนยันน้อย (AM-02) |

## ข้อจำกัด

- รูปทั้งหมดเขียนบน tablet (`evals/handwriting/README.md`) · ยังไม่ได้วัดกับรูปถ่ายกระดาษ
- เทียบแค่ Gemini 2 รุ่นของ free tier · ไม่ได้รัน Claude และ Mathpix เพราะต้องเสียเงิน
- `x(x²-1)` กับ `x³-x` นับว่าตรงกัน เพราะเท่ากันทางพีชคณิต
- SymPy parse ด้วย backend `antlr` (backend `lark` parse ผิดแบบเงียบๆ) · timeout ใช้ thread ซึ่งหยุดงานที่ค้างไม่ได้ (ตัวจริงต้องใช้ subprocess)

## Test

```bash
cd apps/api && uv run --with "antlr4-python3-runtime==4.11.*" pytest ../../poc/P1 -q
```
