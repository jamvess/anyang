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
- ถ้าจะเทียบ prompt A5 version อื่นโดยไม่แก้ `config/ai.yaml`: `uv run python ../../poc/P3/run.py --a5-prompt v2` แล้ว `uv run python ../../poc/P3/score.py --a5-prompt v2` · ผลอยู่ใน `results/<model>-a5<version>/`

## รันบน Vertex AI (31 ต.ค. · วัด P3a ใหม่)

ต้องมี ADC (`gcloud auth application-default login`) และ `GOOGLE_CLOUD_PROJECT` / `GOOGLE_CLOUD_LOCATION` ใน `.env` (`docs/team/setup.md` A5) · ไม่ใช้ `AI_MODEL_OVERRIDE`: แต่ละ call ใช้ model ของ tier ตัวเองใน `config/ai.yaml` (A2b = vision, A5 = mid, A6 = main) · tier small (A4, A7) ต้องบอกด้วย `--small-model` · ใน `config/ai.yaml` 1.7 คือ `vertex:gemini-3.5-flash` (flash-lite เขียน JSON ที่มี LaTeX พัง · `specs/poc/reports/P3.md` §7)

```bash
cd apps/api
uv run python ../../poc/P3/ingest.py --provider vertex --small-model vertex:gemini-3.5-flash
uv run python ../../poc/P3/run.py --provider vertex --small-model vertex:gemini-3.5-flash --a5-prompt v2 --a6-prompt v2
uv run python ../../poc/P3/score.py --provider vertex --a5-prompt v2 --a6-prompt v2
```

- cache แยกไว้ที่ `out/vertex/` (ไม่ทับผล free tier) · ผลสรุปอยู่ที่ `results/vertex-a5<version>/` · `run.json` บอก model ของแต่ละ call
- เว้น 1 วินาทีระหว่าง call (Vertex ไม่มีโควตา 20 ต่อวัน) และ retry ตาม `gateway.retries` ของ config
- `--a5-prompt` และ `--a6-prompt` มีค่าเริ่มต้นตาม `config/ai.yaml` (ตอนนี้ v2 ทั้งคู่) · ผลรอบ free tier เดิม (`results/gemini-3.5-flash-lite-a5v1/`) ทำด้วย `merge_topics` v1 จึงต้องใส่ `--a5-prompt v1 --a6-prompt v1` ถ้าจะรัน `score.py` กับผลนั้นใหม่
- ข้อจำกัดที่รู้แล้ว: A5 และ A4 ที่อยู่ใน cache ไม่ถูกนับเวลาใน `run.json` · cache ของ Vertex ไม่แยกตาม model (เปลี่ยน model ต้องใส่ `--force`)

## Test

```bash
cd apps/api && uv run pytest ../../poc/P3 -q
```

`stars.py` เป็นสูตรดาวแบบ PoC ใช้แล้วทิ้ง · ตัวจริง (`compute_importance`) ทำใน P8-lite ช่วง S4
