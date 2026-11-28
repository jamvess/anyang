# P9-lite · free tier ของ Google AI Studio พอสำหรับแอปไหม (เป้าข้อ 9 ของ advisor)

| | |
|---|---|
| Owner | Junior |
| Branch | `poc/p9-lite-free-tier-quota` |
| Checklist item | ยังไม่มีใน `docs/team/sprint-checklists.md` · เป้าข้อ 9 ของ advisor สำหรับ จ. 30 พ.ย. 2569 ("ทดสอบว่าโควตา free tier ของ Google AI Studio พอสำหรับแอปไหม") · เพิ่มเข้าเช็คลิสต์ใน `/work-done` |
| Status | in progress · 2026-11-28 |

## Plan

- [x] 1. 🤖 หาค่าโควตา free tier ปัจจุบัน (RPM / TPM / RPD) ของ `gemini-3.5-flash` และ `gemini-3.5-flash-lite` จากเอกสารทางการ
- [x] 2. 🙋 ยืนยันกับหน้า AI Studio: เปิด https://aistudio.google.com → เลือกโปรเจกต์ใหม่ของ key → **Usage & Billing** / **Rate limits** → บอก Claude ว่าเห็นคำว่า "Free tier" ไหม และ RPM / TPM / RPD ของ 2 model นี้ (หรือตอบ "ตรง" ถ้าตรงกับข้อ 1) · key อยู่ใน `.env` ที่ root แล้ว (โปรเจกต์ใหม่ ไม่ใช่ `anyang-513006`) · ห้ามวาง key ใน chat
- [x] 3. 🤖 PoC spec สั้นๆ ใน `specs/poc/README.md` (P9-lite · คำถาม, metric, เกณฑ์) + ข้อมูลสังเคราะห์ใน `poc/P9-lite/data/` (PDF ชีทไทย 3 หน้าจาก `pymupdf` + คำตอบพิมพ์สังเคราะห์ · ไม่มีลายมือ ไม่ใช้ `evals/topics/*/raw` · AI-07)
- [x] 4. 🤖 `poc/P9-lite/load.py`: gateway live + `AI_MODEL_OVERRIDE=gemini:<model>` · ครอบ provider ด้วยตัวนับทุก attempt (gateway retry ซ่อน 429/503) · 1 session = `open_session` → (`generate_problem` → `typed_answer` → `check_answer` → `explain_check`) × k → `tutor_reply` × m → `session_summary` · `classify_material` แยก · จดสถานะ latency token และ quota id ของ 429 (ต่อนาที / ต่อวัน) ลง `results/<label>.json` · อ่านไฟล์นอก `data/` ไม่ได้ · unit test ด้วย fake provider
- [ ] 5. 🤖 รัน (แก้หลังข้อ 2): **`gemini-3.5-flash-lite` (ตัวหลัก)** smoke 1 session → session ต่อกันจนชน RPD → burst 3 session พร้อมกัน (RPM) · **`gemini-3.6-flash`** รอบสั้นจนชน 20 RPD · **`gemini-3.5-flash`** 1 call เพื่อยืนยันว่าถูกปฏิเสธ แล้วจด error · คุณภาพของ flash-lite: schema retry / schema fail ต่อ purpose และสัดส่วนโจทย์ที่ SymPy parse ได้ (P3 เคยเจอ LaTeX ใน JSON พัง)
- [ ] 6. 🤖 (เพิ่ม 28 พ.ย. · Junior) ต้นทุนต่อโจทย์ (request + token) และผลของ session จริงราว 10 โจทย์ · ต้นทุน ingestion ต่อการเตรียมสอบ 1 วิชา (classify, extract_topics_local, merge_topics, map_questions) จาก `ai_calls` ของการซ้อม 20 พ.ย. หรือ CSV ใน `.local/` เทียบกับ RPM/TPM/RPD ของ free tier · คำนวณ session/วัน = min(RPD ÷ call ต่อ session) และผู้ใช้พร้อมกันตาม RPM/TPM · เทียบ Vertex (P4-lite) · ผลภาษาไทยครึ่งหน้าสำหรับ advisor + `/poc-report P9-lite`

## Definition of done

- ค่า RPM / TPM / RPD ยืนยันกับหน้า AI Studio แล้ว
- อัตรา 429 / 503 และ latency p50 / p95 ต่อ purpose จากการรันจริง
- session/วัน และผู้ใช้พร้อมกันที่ free tier รองรับ
- คำตอบชัดว่า "พอ / ไม่พอ สำหรับอะไร" (dev, demo, Beta)
- input ทุกตัวเป็นข้อมูลสังเคราะห์หรือชีทสาธารณะ (AI-07)

## ผลข้อ 1 (28 พ.ย.)

- หน้าทางการ (`ai.google.dev/gemini-api/docs/rate-limits` → redirect ไป `aistudio.google.com/docs/rate-limits`) **ไม่ลงตัวเลข free tier ของ 3.5 Flash / Flash-Lite แล้ว** ให้ไปดูค่าของโปรเจกต์ที่ https://aistudio.google.com/rate-limit · "Specified rate limits are not guaranteed and actual capacity may vary"
- โควตานับ **ต่อโปรเจกต์ ไม่ใช่ต่อ key** · RPD reset เที่ยงคืนเวลา Pacific (= 15:00 เวลาไทย)
- Free = โปรเจกต์ที่ไม่ผูก billing · ผูก billing แล้วเป็น Tier 1 ทันที
- ตัวเลขที่ชุมชนวัดได้ (ยังไม่ใช่ทางการ): `gemini-3.5-flash` 5 RPM · 250k TPM · **20 RPD** · `gemini-3.5-flash-lite` 15 RPM · **500 RPD** · ตรงกับที่ทีมเจอ 31 ต.ค. (20 RPD)

## ผลข้อ 2 (28 พ.ย. · Junior ดูหน้า Rate Limit ของ AI Studio · Free tier · โปรเจกต์ `gen-lang-client-…` ไม่ใช่ `anyang-513006`)

| model | RPM | TPM | RPD |
|---|---|---|---|
| `gemini-3.5-flash` (ของเรา) | ไม่มีใน free tier | | |
| `gemini-3.5-flash-lite` | 15 | 250K | 500 |
| `gemini-3.6-flash`, `gemini-3.8-flash` | 5 | 250K | 20 |
| Gemini 3.5 Transcribe (Live API) | 3 | | 25 · gateway ใช้ไม่ได้ |

- คาดไว้ (Junior): Flash เต็มรุ่นได้ < 1 session/วัน · Flash-Lite ราว 20 session/วัน ถ้าคุณภาพพอ · ผลรันเป็นตัวตัดสิน

## Decisions

- 2026-11-28 · ชื่อ PoC `P9-lite` · ต่อจาก P8-lite
- 2026-11-28 · ยิง gateway ตรงด้วยสคริปต์ ไม่ยิงผ่าน API · วัดโควตาได้ตรงโดยไม่ต้องมี DB หรือ token · flow ของ session ตาม purpose ที่ห้องติวเรียกจริง
- 2026-11-28 · เกณฑ์ (ก) 5 และ (ข) 30 session/วัน เป็น [C] · เพิ่ม (ค) ผู้ใช้พร้อมกันโดยไม่โดน 429 (Junior)
- 2026-11-28 · ไม่ commit PDF สังเคราะห์ สร้างตอนรัน (Junior ให้เลือก · ไม่ต้องโหลดฟอนต์เพิ่ม)
- 2026-11-28 · `load.py` ใช้ helper ของห้องจริง (`verified`, `check_answer`, `_explain_input`, `_check_result_text`) เพื่อให้ input เหมือนห้อง · import ตัว private ได้เฉพาะใน PoC
- 2026-11-28 · เจอ 429 ต่อวันแล้วหยุดส่งทันที ไม่เริ่ม session ใหม่ (ไม่เปลืองโควตาของวันถัดไป) · เลขโปรเจกต์ใน error ถูกลบก่อนเขียน `results/`
- 2026-11-28 · key ใน `.env` ที่ root ของ repo · โปรเจกต์ใหม่ที่ไม่ผูก billing (ถ้าผูกจะได้ paid tier)

## Next step

ข้อ 5 รอบแรก: `make_sheet.py` แล้ว smoke 1 session บน `gemini-3.5-flash-lite` พร้อม `--classify` (คำสั่งใน `poc/P9-lite/README.md`) · ดู `results/smoke-flash-lite.json` ว่าทุก purpose ok ก่อนรันรอบ daily

## Waiting on

ไม่มี

## Notes for next time

- ชีทสังเคราะห์สร้างด้วย `poc/P9-lite/make_sheet.py` ใช้ฟอนต์ `LeelawUI.ttf` (tahoma อ่านกลับ `-` เป็น soft hyphen) · subset font แล้วไฟล์ 28 KB · **PDF ไม่ commit** (gitignore ใน `poc/P9-lite/.gitignore`) เพราะ Leelawadee UI เป็นฟอนต์ของ Windows ที่แจกต่อไม่ได้ · สร้างตอนรัน · นอก Windows ใช้ `--font` กับฟอนต์เปิด เช่น Sarabun
- `.env` อยู่ที่ root ของ repo ไม่ใช่ `apps/api/.env` · `AI_MODEL_OVERRIDE` ยังว่าง (ตั้งเป็น env ตอนรันสคริปต์ ไม่ต้องแก้ `.env`)
