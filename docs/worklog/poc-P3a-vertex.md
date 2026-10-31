# วัด P3a ใหม่บน Vertex (เอกสาร → หัวข้อ + ดาว)

| | |
|---|---|
| Owner | Jam |
| Branch | `poc/P3a-vertex` |
| Checklist item | วัด P3a ใหม่บน Vertex: prompt A5/A6 ที่ปรับแล้ว (fallback ของ P3) · ตัดสิน model ของ tier `main` · เช็ค token out ของ `merge_topics` (คำตอบบน free tier ไม่ผ่าน schema ทั้งคู่) · วัด A2b `vision_extract_pages` บน flash-lite (P3 รันบน flash) · เติมผลใน `P3.md`, `ai-orchestration.md` §2.10 และ §3.6, `docs/report/ai-evaluation.md` §3 |
| Status | in progress · 2026-10-31 |

## Plan

- [x] 1. 🤖 `poc/P3/common.py` + `ingest.py` + `run.py` + `score.py`: เพิ่มโหมด `--provider vertex` · ใช้ model ตาม tier ใน `config/ai.yaml` (A2b = vision flash-lite, A5 = mid flash, A6 = main flash) · tier small (A4 `split_past_exam`, A7 `map_questions`) ยังเป็น TODO จึงรับ model จาก flag `--small-model` · เว้นระหว่าง call สั้นลง (Vertex ไม่มีโควตา 20/วัน) · ใช้ `gateway.retries` ตาม config · ผลแยกโฟลเดอร์ `out/vertex/` และ `results/vertex-a5<v>/` ไม่ทับผลเดิม · test ใน `poc/P3/test_p3.py` (ไม่เรียก AI)
- [x] 2. 🙋 Jam เลือก model ของ tier small สำหรับรอบนี้ (A4, A7): `gemini-3.5-flash-lite` หรือ `gemini-3.5-flash`
- [x] 3. 🙋 Jam รัน ingest บน Vertex (A2b บน flash-lite + A4) · `cd apps/api` → `uv run python ../../poc/P3/ingest.py --provider vertex --small-model vertex:<model>` · ใช้ประมาณ 4 call · ดูว่า A4 ตัดข้อได้ 43 ข้อเหมือนเดิมไหม
- [x] 4. 🙋 Jam รัน A5 → A6 → A7 บน Vertex 2 รอบ คือ A5 `v1` และ `v2` · `uv run python ../../poc/P3/run.py --provider vertex --small-model vertex:gemini-3.5-flash --a5-prompt v1` แล้ว `score.py --provider vertex --a5-prompt v1` · ทำซ้ำด้วย `v2` · ประมาณ 7 call ต่อรอบ
- [x] 5. 🤖 สรุปผลเป็นตาราง เทียบกับรอบ free tier: หัวข้อตรง (IoU ≥ 0.5), ★★★ ทั้ง pipeline, map ข้อสอบ, นาทีต่อไฟล์, A6 ผ่าน schema ไหม, token out ของ `merge_topics` เทียบกับเพดาน 16,000, A2b บน flash-lite (เวลา, token, จำนวนข้อที่ A4 ตัดได้)
- [ ] 6. 🙋 Jam ตัดสิน: ผ่านหรือไม่ผ่าน · ใช้ A5 version ไหน · model ของ tier main · ถ้า A6 ยังพังให้ทำ `merge_topics/v2` ไหม (ถ้าทำ ต้องวน ขั้น 4 อีกรอบ)
- [ ] 7. 🤖 `/poc-report P3` (เพิ่มส่วน "รอบ Vertex") + `specs/poc/README.md` บรรทัดผล P3 + `ai-orchestration.md` §2.10, §3.6 + `docs/report/ai-evaluation.md` §3 + `config/ai.yaml` ถ้าเปลี่ยน prompt หรือ model (ไฟล์กลาง)
- [ ] 8. 🙋 Jam บอกแชทกลุ่ม (ถ้าแก้ `config/ai.yaml`)

## Definition of done

- มีตัวเลข P3a บน Vertex ครบทุก metric ของ P3 (หัวข้อ, ★★★ ทั้ง pipeline, map, นาทีต่อไฟล์) และ A6 ได้ผลหรือรู้ว่าทำไมไม่ได้
- รู้ token out ของ `merge_topics` และของ A2b บน flash-lite เทียบกับเพดาน
- Jam ตัดสิน model ของ tier main และ A5 version แล้ว · จดใน `P3.md`
- `ai-orchestration.md` §2.10, §3.6 และ `docs/report/ai-evaluation.md` §3 ไม่มีคำว่า "รอวัด P3a บน Vertex" แล้ว
- `uv run pytest ../../poc/P3 -q` ผ่าน
- ตรงกับ checklist: "วัด P3a ใหม่บน Vertex: …"

## Decisions

- 2026-10-31 · tier small รอบนี้ (A4, A7) = `vertex:gemini-3.5-flash-lite` · ตรงกับชื่อ tier และได้ข้อมูลไว้ตัดสิน tier small ใน config · ถ้า A7 พลาดต้องแยกว่าเพราะ model หรือ prompt

- 2026-10-31 · ingest รอบ 1 (small = flash-lite): A4 ของ midterm-2561-1 ไม่ผ่าน schema 2 ครั้ง เพราะ flash-lite ไม่ escape backslash ของ LaTeX ใน JSON (`\sqrt` → `Invalid \escape`) · เนื้อหาครบ · midterm-2559-1 ผ่าน (23 ข้อ) → flash-lite ไม่สม่ำเสมอกับ LaTeX ใน JSON · ใช้ประกอบการตัดสิน tier small · เสนอแยกงาน: gateway ซ่อม escape ที่ไม่ถูกต้องก่อน parse (§2.9)
- 2026-10-31 · Jam เปลี่ยน tier small รอบนี้เป็น `vertex:gemini-3.5-flash` แล้วรัน ingest `--force` ใหม่ · A4 ได้ 23 + 20 = 43 ข้อ q_no ตรงกับรอบ free tier ทุกข้อ
- A2b บน flash-lite (3 ครั้ง): 2559 (14 หน้า) 12.3 s / out 3,477 · 27.0 s / out 7,666 (schema retry 1 ครั้ง) · 2561 (12 หน้า) 9.6 s / out 3,199 · 8.2 s / out 3,353 · รอบเดิมบน flash 40.5 s / out 7,943 · ทุกครั้งต่ำกว่าเพดาน 16,000

- 2026-10-31 · run บน Vertex (small = flash): **A5 v1 → A6 ไม่ผ่าน schema ทั้ง 2 ครั้ง** (out รวม 31,968 ≈ 16,000 ต่อครั้ง = ชนเพดาน) · **A5 v2 → A6 ครั้งแรกถูกตัดที่เพดาน ครั้งที่สองผ่าน** (out รวม 29,125 · 83.6 s) · คำตอบดิบของ A6 รอบ v1 ถูกรอบ v2 เขียนทับ (`SaveRaw` นับเลขใหม่ทุก process) จึงยืนยันได้จาก token เท่านั้น

- 2026-10-31 · ขั้น 6 Jam: ทำ `merge_topics/v2` ในงานนี้ + เพิ่มงบ token (ข้อ 1 ก) · v2: เก็บทุก section ของชีทเป็นหัวข้อของตัวเอง, รวมเฉพาะที่ซ้ำข้ามไฟล์จริง, หัวข้อของไฟล์แบบฝึกหัดไปรวมกับหัวข้อในชีทที่ฝึก, skill 2–4 ข้อ และ mistake 1–2 ข้อ (จากเดิม 2–5 และ 1–3 · ลด token) · `config/ai.yaml` 1.6: `merge_topics` `max_tokens` 16000 → 32000 คง `thinking: medium` (`prompt` ยังเป็น v1 จนกว่าจะตัดสินจากผล) · `run.py`/`score.py` มี `--a6-prompt` · `SaveRaw` ไม่เขียนทับคำตอบของรอบก่อนแล้ว

## ผลขั้น 5 (P3a บน Vertex · 31 ต.ค.)

| Metric | เป้า | free tier 21 ต.ค. (flash-lite ทั้งชุด) | Vertex A5 v1 | Vertex A5 v2 |
|---|---|---|---|---|
| A5 อย่างเดียว หัวข้อตรง (IoU ≥ 0.5) | — | flash 15/27 = 56% | **21/27 = 78%** (44 หัวข้อ) | 20/27 = 74% (51 หัวข้อ) |
| A6 `merge_topics` ผ่าน schema | — | flash 0/20 | ❌ 0/2 (ชนเพดาน) | ✅ ครั้งที่ 2 (ครั้งแรกชนเพดาน) |
| หัวข้อตรงหลัง A6 | ≥ 80% | 1/27 | — | ❌ 7/27 = 26% (A6 รวมเหลือ 17 หัวข้อ จาก 51) |
| ★★★ ทั้ง pipeline | ≥ 80% | 1/12 | — | ❌ 2/12 |
| ★★★ สูตร + map ของ label (ไม่ใช้ AI) | ≥ 80% | 10/12 | — | ✅ 10/12 = 83% (เท่าเดิม) |
| map ข้อสอบเข้าหัวข้อที่ถูก | — | 2/43 | — | 7/43 (ต่ำเพราะหัวข้อไม่ตรง) |
| นาทีต่อไฟล์ (สูงสุด) | ≤ 3 | 1.34 | — | ✅ 0.95 |
| A4 ตัดข้อสอบ | — | 43/43 (flash) | flash 43/43 · flash-lite JSON พัง 1/2 ไฟล์ | |
| A2b 14 หน้า | — | flash 40.5 s | flash-lite 12.3 s และ 27.0 s (retry 1) | |

**อ่านผล:** คอขวดย้ายจาก A5 ไปที่ A6 · (1) A6 รวมหัวข้อที่ label แยกไว้เข้าด้วยกัน (เช่น ลิมิต + ความต่อเนื่อง, chain rule + อนุพันธ์ตรีโกณ/log/ผกผัน รวมเป็นหัวข้อเดียว) (2) A6 ใช้ output เกือบหรือเกิน 16,000 token ทุกครั้ง (`thinking: medium` นับรวมใน `max_tokens`) จึงพังแบบสุ่ม · token ของรอบ v2 ทั้ง pipeline: in 134,253 / out 53,496

## Next step

ขั้น 4 รอบ 2 (🙋): Jam รัน `run.py` + `score.py` ด้วย `--a6-prompt v2` สำหรับ A5 `v1` และ `v2` (A5 อยู่ใน cache · 3 call ต่อรอบ)

## Waiting on

ไม่มี

## Notes for next time

- PDF อยู่ที่ `evals/topics/mth10101/raw/` (gitignored · มีในเครื่อง Jam) · cache เดิมอยู่ใน `poc/P3/out/` อย่าเขียนทับ
- รอบ free tier (21 ต.ค.): flash-lite หัวข้อตรง 1/27 · A5 ของ flash 15/27 · A6 ของ flash ไม่ผ่าน schema (skill id ผิด 1 ตัว · token out 11,242 และ 14,944 จาก 16,000) · A2b 14 หน้า 40.5 วินาที บน flash
- P3 เสนอให้ code ตั้ง skill id เองแทน LLM (เปลี่ยนหลักการ · ไม่อยู่ในงานนี้)
