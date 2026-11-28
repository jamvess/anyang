# PoC P9-lite · โควตา free tier ของ Google AI Studio

spec: `specs/poc/README.md` P9-lite · เป้าข้อ 9 ของ advisor (30 พ.ย. 2569) · report: `specs/poc/reports/P9-lite.md`

**ข้อมูลสังเคราะห์เท่านั้น (AI-07):** สคริปต์อ่านได้แค่ไฟล์ใน `data/` · ห้ามใส่ลายมือหรือไฟล์ของผู้ใช้จริง

## รัน

ต้องมี `GEMINI_API_KEY` ใน `.env` ที่ root ของ repo · key ต้องอยู่ใน**โปรเจกต์ที่ไม่ผูก billing** (ผูกแล้วจะเป็น Tier 1 ไม่ใช่ free tier) · โควตานับต่อโปรเจกต์ และ RPD reset ตอนเที่ยงคืนเวลา Pacific (15:00 เวลาไทย)

```bash
cd apps/api
PYTHONUTF8=1 uv run python ../../poc/P9-lite/make_sheet.py            # ชีทสังเคราะห์ (gitignored · นอก Windows ใส่ --font <Sarabun.ttf>)
PYTHONUTF8=1 uv run python ../../poc/P9-lite/load.py --model gemini-3.5-flash-lite --sessions 1 --think 30 --classify --label smoke-flash-lite
PYTHONUTF8=1 uv run python ../../poc/P9-lite/load.py --model gemini-3.5-flash-lite --sessions 40 --think 30 --label daily-flash-lite
PYTHONUTF8=1 uv run python ../../poc/P9-lite/load.py --model gemini-3.5-flash-lite --sessions 3 --concurrency 3 --label burst-flash-lite
```

- 1 session = `generate_problem` → `open_session` → ต่อโจทย์: `typed_answer` → `check_answer` → `explain_check` (โจทย์ที่ 2, 4, … ตอบผิดก่อน แล้วตอบถูกหลังได้ hint) → `tutor_reply` × `--chat` → `session_summary` · `--problems` 3 และ `--chat` 2 เป็นค่าเริ่มต้น
- `--think 30`: นักเรียนอ่านและทำ 30 วินาทีก่อนส่งคำตอบหรือแชททุกครั้ง · `0` = burst (ยิงต่อกันทันที)
- ใช้ `Gateway` ตัวจริง (prompt, `config/ai.yaml`, retry, SymPy) กับ provider `gemini` อย่างเดียว ไปไม่ถึง Vertex และไม่เขียน `ai_calls`
- นับทุก attempt ที่ provider เพราะ retry ของ gateway ซ่อน 429/503 · เมื่อเจอ 429 แบบต่อวัน (`…PerDay…`) จะหยุดส่ง และไม่เริ่ม session ใหม่
- บันทึก `results/<label>.json` หลังทุก batch (`meta.finished: false` ระหว่างรัน) · หยุดกลางทาง (Ctrl+C) ก็ยังได้ session ที่จบแล้ว · รันใน background อย่า pipe ผ่าน `grep` (บัฟเฟอร์จนไม่เห็นความคืบหน้า)
- ผลอยู่ใน `results/<label>.json`: `summary` (ตัวเลขรวม), `sessions`, `attempts` (ทุก request), `calls` (`CallRecord` ของ gateway) · ไม่มี key และเลขโปรเจกต์
- **เปราะ:** `load.py` import helper private ของ `app/services/photo_check.py` (`_explain_input`, `_check_result_text`) เพื่อให้ input ของ `explain_check` เหมือนห้องจริง · ถ้า Jam เปลี่ยนชื่อหรือ signature สคริปต์จะพัง (test ใน `poc/P9-lite` จับได้) · แก้ที่สคริปต์ ไม่ต้องแก้แอป
- test (ไม่ใช้ network): `uv run --project apps/api pytest poc/P9-lite` (รันจาก root)

## ผล

(รอรัน)
