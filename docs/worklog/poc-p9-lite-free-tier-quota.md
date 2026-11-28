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
- [ ] 5. 🤖 รัน (แก้หลังข้อ 2 · 28 พ.ย.: 3.6-flash ไม่รันต่อ ใช้ตัวเลขจากหน้า Rate Limit แทน): **`gemini-3.5-flash-lite` (ตัวหลัก)** smoke 1 session → session ต่อกันจนชน RPD → burst 3 session พร้อมกัน (RPM) · **`gemini-3.6-flash`** รอบสั้นจนชน 20 RPD · **`gemini-3.5-flash`** 1 call เพื่อยืนยันว่าถูกปฏิเสธ แล้วจด error · คุณภาพของ flash-lite: schema retry / schema fail ต่อ purpose และสัดส่วนโจทย์ที่ SymPy parse ได้ (P3 เคยเจอ LaTeX ใน JSON พัง)
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

## ผล burst ผู้ใช้ 1 คน ไม่มี think time (28 พ.ย. · `results/burst-1user-flash-lite.json`)

- 1 session + classify บน `gemini-3.5-flash-lite` · ส่ง 16 request ใน 37 วินาที · ok 13 · 503 1 ครั้ง ("high demand") · **429 ต่อนาที 2 ครั้งที่ request ที่ 16** (`GenerateRequestsPerMinutePerProjectPerModel-FreeTier`) · gateway ยอมแพ้ → session ไม่จบ (ห้องจริงจะขึ้น "ระบบช้า")
- สคริปต์ไม่มีเวลาคิดของนักเรียน จึงยิงเร็วกว่าคนจริง · 15 RPM ถูกใช้หมดโดยผู้ใช้คนเดียว
- คุณภาพ: `generate_problem` 2/2 SymPy ยืนยัน (schema retry 1) · `classify_material` schema retry 1 · `check_answer` ไม่มี schema error
- latency ok: call 0.9–1.7 s · `explain_check` TTFT p95 2.4 s · `open_session` TTFT 3.3 s

## ผล smoke --think 30 (28 พ.ย. · `results/smoke-flash-lite.json`)

- session จบ · 21 request (3 โจทย์ + chat 2 · ไม่นับ classify) ใน 3.7 นาที · 429: 0 · 503: 1 (`typed_answer` · gateway retry ผ่าน) · SymPy ยืนยัน 3/3 (`generate_problem` 4 attempt)
- รอบ burst เดิมเก็บไว้ที่ `results/burst-1user-flash-lite.json`: ผู้ใช้คนเดียวที่ยิงต่อกันชน 15 RPM ที่ request ที่ 16 + 503 "high demand"

## ผล session 10 โจทย์ (28 พ.ย. · `results/session10-flash-lite.json` · flash-lite · --think 30)

- session จบ · **68 request ใน 10 นาที** · 429: 0 · 503: 0 · tokens_in 86.8K · tokens_out 8.5K
- **ต่อโจทย์ ≈ 6.5 request · 8.7K token in · 0.85K token out** (รวม retry)
- **peak 12 request ใน 60 วินาที จากผู้ใช้คนเดียว** (เพดาน 15 RPM) → ผู้ใช้พร้อมกันได้ราว 1 คน (เกณฑ์ ค)
- คุณภาพ: `generate_problem` 13 call ได้ 10 โจทย์ · **schema_error 3/13 (23%)** หลัง schema retry (ไม่ใช่ถูกตัด: tokens_out ~470) · อีก 3 call ผ่านหลัง retry · โจทย์ที่ได้ SymPy ยืนยันทุกข้อ · ส่งต่อ Jam: น่าจะเป็นเรื่อง JSON + LaTeX แบบเดียวกับ P3

## ผล gemini-3.5-flash (28 พ.ย. · `results/reject-flash.json`)

- **ไม่ถูกปฏิเสธ:** 6/6 ok ผ่าน provider `gemini` (AI Studio key) · latency 2–12 s (ช้ากว่า flash-lite 2–4 เท่า)
- **ข้อค้นพบ (Junior ดูหน้า Rate Limit · 28 พ.ย.):** AI Studio นับ 6 request ของ `gemini-3.5-flash` เป็นของ **Gemini 3.6 Flash** (6/5 RPM · 6/20 RPD · 4.63K TPM) · คือชื่อ `gemini-3.5-flash` ถูกส่งต่อไปที่ 3.6 Flash และใช้โควตา RPM 5 · RPD 20 ของตัวนั้น · โปรเจกต์เป็น Free tier จริง (Usage เขียน "Free tier" · ไม่ได้ตั้ง billing)
- ผลกับแอป: บน free tier ค่า `config/ai.yaml` ของเรา (`3.5-flash`) จะได้ model คนละตัวกับบน Vertex และได้แค่ 20 request/วัน · ไม่ใช้โควตาที่เหลือของ 3.6 Flash ต่อ (Junior) · ข้อ "ยืนยัน 3.6-flash ชน 20 RPD" ในแผนจึงตัดออก: หน้า Rate Limit แสดงตัวเลขแล้ว

## ต้นทุน ingestion ต่อการเตรียมสอบ 1 วิชา (ประมาณ · 28 พ.ย.)

ที่มา: `.local/ai_calls_caps.csv.csv` (ai_calls ของ `anyang-dev` 17–20 พ.ย. · max tokens_out ต่อ purpose) + `.local/rehearsal-api.utf8.log` (tokens_in ของ 35 call) · วิชาแบบ MTH10101 ไฟล์ 6 ไฟล์ (ชีท 4 + ข้อสอบสแกน 2) · chunk 116 (ingestion.md §2.3)

| purpose | request | tokens_in ต่อ call (max) | tokens_out ต่อ call (max) |
|---|---|---|---|
| classify_material | 6 | 2.4K | 0.3K |
| vision_extract_pages (ข้อสอบสแกน) | 2 | 15.7K | 7.5K |
| split_past_exam | 2 | 3.9K | 4.0K |
| extract_topics_local (ชีท) | 4 | 45.7K | 2.6K |
| merge_topics | 1 | 4.9K | 23.3K |
| map_questions | 1–2 | 6.5K | 4.7K |
| **รวม generate** | **~17** | **~150K** | **~67K** |
| embed (`gemini-embedding-2`) | 116 ที่ `batch_size` 1 (Vertex) · ~12 ถ้า batch 10 บน Gemini API | | |

- flash-lite: 17 request = 3% ของ 500 RPD · input สูงสุดต่อ call 46K < 250K TPM (ไฟล์ทำทีละไฟล์ · ingestion.md §3 ข้อ 1) → **โควตาพอ** · แต่ P3 ตัด flash-lite ออกจาก A5/A6 เพราะแบ่งหัวข้อหยาบและ JSON พังกับ LaTeX (`P3.md`) → **คุณภาพไม่พอ**
- 3.6 / 3.8 flash: 17 จาก 20 RPD → 1 วิชาต่อวัน ไม่เหลือให้ติวเลย
- embed: free tier ของ `gemini-embedding-2` = RPM 100 · TPM 30K · RPD 1K (Junior ดู 28 พ.ย.) · 116 chunk ต่อวิชา request พอ แต่ token รวมของ chunk (log: embed in สูงสุด 45.7K ต่อ call) เกิน 30K TPM → ต้องกระจายเกิน 1 นาที
- ตัดสิน: ไม่รัน ingestion บน free tier (Junior: "don't run if clearly won't fit")

## รอบ daily ครั้งแรก (28 พ.ย. · ถูกหยุด · ไม่มีผล)

- รัน `--sessions 40 --concurrency 3 --think 30 --label daily-flash-lite` ราว 17:2x–17:35 น. (เวลาไทย) แล้ว Junior ต้องปิดเครื่อง จึงหยุดกลางทาง
- **ไม่มีผลเหลือ:** สคริปต์รุ่นนั้นเขียน `results/` ตอนจบเท่านั้น และ `grep` ที่ pipe ไว้บัฟเฟอร์บรรทัดความคืบหน้า จึงไม่รู้ว่าจบไปกี่ session · ใช้โควตา flash-lite ไปเพิ่มเท่าไรให้ดูในหน้า Rate Limit
- `TaskStop` หยุดแค่ shell: process ของ Python (`load.py` + SymPy worker) ยังรันต่อ ต้อง `Stop-Process` เอง (หยุดแล้ว เหลือ 0 process)
- แก้แล้ว (commit `wip`): `load.py` บันทึก `results/<label>.json` หลังทุก batch (`meta.finished: false`) และตอน Ctrl+C · test ใหม่ 1 ตัว · รวม 10 passed

## Decisions

- 2026-11-28 · ชื่อ PoC `P9-lite` · ต่อจาก P8-lite
- 2026-11-28 · ยิง gateway ตรงด้วยสคริปต์ ไม่ยิงผ่าน API · วัดโควตาได้ตรงโดยไม่ต้องมี DB หรือ token · flow ของ session ตาม purpose ที่ห้องติวเรียกจริง
- 2026-11-28 · เกณฑ์ (ก) 5 และ (ข) 30 session/วัน เป็น [C] · เพิ่ม (ค) ผู้ใช้พร้อมกันโดยไม่โดน 429 (Junior)
- 2026-11-28 · ไม่ commit PDF สังเคราะห์ สร้างตอนรัน (Junior ให้เลือก · ไม่ต้องโหลดฟอนต์เพิ่ม)
- 2026-11-28 · `load.py` ใช้ helper ของห้องจริง (`verified`, `check_answer`, `_explain_input`, `_check_result_text`) เพื่อให้ input เหมือนห้อง · import ตัว private ได้เฉพาะใน PoC
- 2026-11-28 · เจอ 429 ต่อวันแล้วหยุดส่งทันที ไม่เริ่ม session ใหม่ (ไม่เปลืองโควตาของวันถัดไป) · เลขโปรเจกต์ใน error ถูกลบก่อนเขียน `results/`
- 2026-11-28 · key ใน `.env` ที่ root ของ repo · โปรเจกต์ใหม่ที่ไม่ผูก billing (ถ้าผูกจะได้ paid tier)

## Done today (28 พ.ย.)

- ข้อ 1–4 เสร็จ: ค่าโควตา free tier (ยืนยันกับหน้า AI Studio), PoC spec P9-lite, ข้อมูลสังเคราะห์, `load.py` + 10 test
- รันแล้ว: burst 1 คน (ชน 15 RPM ที่ request 16 + 503), smoke `--think 30` (21 request · จบ), session 10 โจทย์ (68 request · peak 12/นาที · schema error ของ `generate_problem` 3/13), `gemini-3.5-flash` (ถูกนับเป็น 3.6 Flash)
- ต้นทุน ingestion ประมาณจากการซ้อม 20 พ.ย. (ไม่รันบน free tier)
- รอบ daily ถูกหยุด ไม่มีผล (ดูหัวข้อ "รอบ daily ครั้งแรก")

## Next step

รันรอบ daily ใหม่บน flash-lite **หลัง 15:00 น. เวลาไทย** (RPD reset เที่ยงคืน Pacific) จาก `apps/api` ใน background **ไม่ pipe ผ่าน grep**: `env -u AI_PROVIDER -u AI_MODEL_OVERRIDE PYTHONUTF8=1 uv run python ../../poc/P9-lite/load.py --model gemini-3.5-flash-lite --sessions 40 --concurrency 3 --think 30 --label daily-flash-lite` · ถ้าต้องหยุดกลางทาง ผลถึง batch ล่าสุดอยู่ใน `results/daily-flash-lite.json` · หยุดแล้วเช็คว่าไม่มี `python.exe` ของ `load.py` ค้าง · จบแล้วทำข้อ 6 (สรุปภาษาไทยสำหรับ advisor + `/poc-report P9-lite`) · ถ้ารีบก่อน advisor 30 พ.ย. ทำข้อ 6 จากผลที่มีได้เลย แล้วใส่ผล daily ทีหลัง

## Waiting on

ไม่มี (key อยู่ใน `.env` ที่ root แล้ว)

## Notes for next time

- โควตาที่ใช้ไปของวันนี้ดูได้ที่ https://aistudio.google.com/rate-limit (Junior เห็นก่อนรอบ daily: flash-lite 79/500 RPD · peak 12/15 RPM)
- 3.6 Flash ใช้ไปแล้ว 6/20 ของวันนี้ · ไม่ต้องใช้ต่อ (Junior)
- ข้อ 6 ต้องมี: session/วัน ที่ 3 และ 10 โจทย์ · ต้นทุนต่อโจทย์ (request + token) · ผู้ใช้พร้อมกัน (ค) · ingestion ต่อวิชา · บรรทัด "ผู้ใช้คนเดียวก็ชน 15 RPM ได้ + เจอ 503 high demand" · ข้อค้นพบ 3.5-flash → 3.6 Flash · import private ของ `photo_check.py` เปราะ

- ชีทสังเคราะห์สร้างด้วย `poc/P9-lite/make_sheet.py` ใช้ฟอนต์ `LeelawUI.ttf` (tahoma อ่านกลับ `-` เป็น soft hyphen) · subset font แล้วไฟล์ 28 KB · **PDF ไม่ commit** (gitignore ใน `poc/P9-lite/.gitignore`) เพราะ Leelawadee UI เป็นฟอนต์ของ Windows ที่แจกต่อไม่ได้ · สร้างตอนรัน · นอก Windows ใช้ `--font` กับฟอนต์เปิด เช่น Sarabun
- `.env` อยู่ที่ root ของ repo ไม่ใช่ `apps/api/.env` · `AI_MODEL_OVERRIDE` ยังว่าง (ตั้งเป็น env ตอนรันสคริปต์ ไม่ต้องแก้ `.env`)
