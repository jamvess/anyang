# P9-lite · free tier ของ Google AI Studio พอสำหรับแอปไหม (เป้าข้อ 9 ของ advisor)

| | |
|---|---|
| Owner | Junior |
| Branch | `poc/p9-lite-free-tier-quota` |
| Checklist item | ยังไม่มีใน `docs/team/sprint-checklists.md` · เป้าข้อ 9 ของ advisor สำหรับ จ. 30 พ.ย. 2569 ("ทดสอบว่าโควตา free tier ของ Google AI Studio พอสำหรับแอปไหม") · เพิ่มเข้าเช็คลิสต์ใน `/work-done` |
| Status | in progress · 2026-11-28 |

## Plan

- [ ] 1. 🤖 หาค่าโควตา free tier ปัจจุบัน (RPM / TPM / RPD) ของ `gemini-3.5-flash` และ `gemini-3.5-flash-lite` จากเอกสารทางการ
- [ ] 2. 🙋 ยืนยันกับหน้า AI Studio: เปิด https://aistudio.google.com → เลือกโปรเจกต์ใหม่ของ key → **Usage & Billing** / **Rate limits** → บอก Claude ว่าเห็นคำว่า "Free tier" ไหม และ RPM / TPM / RPD ของ 2 model นี้ (หรือตอบ "ตรง" ถ้าตรงกับข้อ 1) · key อยู่ใน `.env` ที่ root แล้ว (โปรเจกต์ใหม่ ไม่ใช่ `anyang-513006`) · ห้ามวาง key ใน chat
- [ ] 3. 🤖 PoC spec สั้นๆ ใน `specs/poc/README.md` (P9-lite · คำถาม, metric, เกณฑ์) + ข้อมูลสังเคราะห์ใน `poc/P9-lite/data/` (PDF ชีทไทย 3 หน้าจาก `pymupdf` + คำตอบพิมพ์สังเคราะห์ · ไม่มีลายมือ ไม่ใช้ `evals/topics/*/raw` · AI-07)
- [ ] 4. 🤖 `poc/P9-lite/load.py`: gateway live + `AI_MODEL_OVERRIDE=gemini:<model>` · ครอบ provider ด้วยตัวนับทุก attempt (gateway retry ซ่อน 429/503) · 1 session = `open_session` → (`generate_problem` → `typed_answer` → `check_answer` → `explain_check`) × k → `tutor_reply` × m → `session_summary` · `classify_material` แยก · จดสถานะ latency token และ quota id ของ 429 (ต่อนาที / ต่อวัน) ลง `results/<label>.json` · อ่านไฟล์นอก `data/` ไม่ได้ · unit test ด้วย fake provider
- [ ] 5. 🤖 รัน 3 รอบต่อ model (flash, flash-lite): smoke 1 session → session ต่อกันจนชน RPD → burst 3 session พร้อมกัน (RPM) · ใช้โควตาของ key หมดทั้งวัน
- [ ] 6. 🤖 คำนวณ session/วัน = min(RPD ÷ call ต่อ session) และผู้ใช้พร้อมกันตาม RPM/TPM · เทียบ Vertex (P4-lite) · ผลภาษาไทยครึ่งหน้าสำหรับ advisor + `/poc-report P9-lite`

## Definition of done

- ค่า RPM / TPM / RPD ยืนยันกับหน้า AI Studio แล้ว
- อัตรา 429 / 503 และ latency p50 / p95 ต่อ purpose จากการรันจริง
- session/วัน และผู้ใช้พร้อมกันที่ free tier รองรับ
- คำตอบชัดว่า "พอ / ไม่พอ สำหรับอะไร" (dev, demo, Beta)
- input ทุกตัวเป็นข้อมูลสังเคราะห์หรือชีทสาธารณะ (AI-07)

## Decisions

- 2026-11-28 · ชื่อ PoC `P9-lite` · ต่อจาก P8-lite
- 2026-11-28 · ยิง gateway ตรงด้วยสคริปต์ ไม่ยิงผ่าน API · วัดโควตาได้ตรงโดยไม่ต้องมี DB หรือ token · flow ของ session ตาม purpose ที่ห้องติวเรียกจริง
- 2026-11-28 · key ใน `.env` ที่ root ของ repo · โปรเจกต์ใหม่ที่ไม่ผูก billing (ถ้าผูกจะได้ paid tier)

## Next step

ข้อ 1: หาค่าโควตา free tier ปัจจุบันของ `gemini-3.5-flash` และ `gemini-3.5-flash-lite`

## Waiting on

ไม่มี

## Notes for next time

- `.env` อยู่ที่ root ของ repo ไม่ใช่ `apps/api/.env` · `AI_MODEL_OVERRIDE` ยังว่าง (ตั้งเป็น env ตอนรันสคริปต์ ไม่ต้องแก้ `.env`)
