# PoC P3a · เอกสาร → หัวข้อ + ดาว (MTH10101)

spec: `specs/poc/README.md` P3 · label: `evals/topics/mth10101/labels.json` · worklog: `docs/worklog/poc-P3.md`

## รัน

ต้องมี `GEMINI_API_KEY` และ `AI_MODEL_OVERRIDE` ใน `.env` (`docs/team/setup.md` A5) และไฟล์ PDF ใน `evals/topics/mth10101/raw/`

```bash
cd apps/api
uv run python ../../poc/P3/ingest.py && uv run python ../../poc/P3/run.py && uv run python ../../poc/P3/score.py
```

| script | ทำอะไร | AI calls |
|---|---|---|
| `ingest.py` | ชีทอ่านจาก text layer · ข้อสอบสแกน (ตัวอักษรไทยใน text layer < 30%) อ่านด้วย `vision_extract_pages` ทั้งฉบับใน call เดียว แล้วตัดรายข้อด้วย `split_past_exam` | 4 |
| `run.py` | A5 `extract_topics_local` ทีละชีท → A6 `merge_topics` → A7 `map_questions` ทีละข้อสอบ → ดาว (`stars.py`) | 7 |
| `score.py` | เทียบกับ label: หัวข้อ (จับคู่ด้วยหน้าที่ทับกัน IoU ≥ 0.5), ★★★, การ map ข้อสอบ, นาทีต่อไฟล์ | 0 |

- ผลที่ทำเสร็จแล้วถูกเก็บไว้ใน `out/` (gitignored เพราะมีข้อความจากชีท) · รันซ้ำจะไม่เรียก AI ซ้ำ · ถ้าอยากทำใหม่ทั้งหมดให้ใส่ `--force`
- ผลสรุปอยู่ที่ `results/<model>/` (commit ได้ มีแค่ชื่อหัวข้อ ช่วงหน้า ดาว และเวลา)
- free tier: เรียกได้ 5 ครั้งต่อนาที และ **20 ครั้งต่อวันต่อ model** · `common.py` เว้นช่วง 13 วินาทีระหว่าง call · เวลาต่อไฟล์นับเฉพาะเวลาที่ AI ทำงานจริง (`latency_ms`) ไม่นับเวลารอโควตา
- ถ้าจะเทียบ model อื่น ให้เปลี่ยน `AI_MODEL_OVERRIDE` แล้วรัน `run.py` + `score.py` ใหม่ (ผลจะแยกโฟลเดอร์ตาม model)

## Test

```bash
cd apps/api && uv run pytest ../../poc/P3 -q
```

`stars.py` เป็นสูตรดาวแบบ PoC ใช้แล้วทิ้ง · ตัวจริง (`compute_importance`) ทำใน P8-lite ช่วง S4
