# วัด P3a ใหม่บน Vertex (เอกสาร → หัวข้อ + ดาว)

| | |
|---|---|
| Owner | Jam |
| Branch | `poc/P3a-vertex` |
| Checklist item | วัด P3a ใหม่บน Vertex: prompt A5/A6 ที่ปรับแล้ว (fallback ของ P3) · ตัดสิน model ของ tier `main` · เช็ค token out ของ `merge_topics` (คำตอบบน free tier ไม่ผ่าน schema ทั้งคู่) · วัด A2b `vision_extract_pages` บน flash-lite (P3 รันบน flash) · เติมผลใน `P3.md`, `ai-orchestration.md` §2.10 และ §3.6, `docs/report/ai-evaluation.md` §3 |
| Status | in progress · 2026-10-31 |

## Plan

- [ ] 1. 🤖 `poc/P3/common.py` + `ingest.py` + `run.py` + `score.py`: เพิ่มโหมด `--provider vertex` · ใช้ model ตาม tier ใน `config/ai.yaml` (A2b = vision flash-lite, A5 = mid flash, A6 = main flash) · tier small (A4 `split_past_exam`, A7 `map_questions`) ยังเป็น TODO จึงรับ model จาก flag `--small-model` · เว้นระหว่าง call สั้นลง (Vertex ไม่มีโควตา 20/วัน) · ใช้ `gateway.retries` ตาม config · ผลแยกโฟลเดอร์ `out/vertex/` และ `results/vertex-a5<v>/` ไม่ทับผลเดิม · test ใน `poc/P3/test_p3.py` (ไม่เรียก AI)
- [ ] 2. 🙋 Jam เลือก model ของ tier small สำหรับรอบนี้ (A4, A7): `gemini-3.5-flash-lite` หรือ `gemini-3.5-flash`
- [ ] 3. 🙋 Jam รัน ingest บน Vertex (A2b บน flash-lite + A4) · `cd apps/api` → `uv run python ../../poc/P3/ingest.py --provider vertex --small-model vertex:<model>` · ใช้ประมาณ 4 call · ดูว่า A4 ตัดข้อได้ 43 ข้อเหมือนเดิมไหม
- [ ] 4. 🙋 Jam รัน A5 → A6 → A7 บน Vertex 2 รอบ คือ A5 `v1` และ `v2` · `uv run python ../../poc/P3/run.py --provider vertex --small-model vertex:<model> --a5-prompt v1` แล้ว `score.py --provider vertex --a5-prompt v1` · ทำซ้ำด้วย `v2` · ประมาณ 7 call ต่อรอบ
- [ ] 5. 🤖 สรุปผลเป็นตาราง เทียบกับรอบ free tier: หัวข้อตรง (IoU ≥ 0.5), ★★★ ทั้ง pipeline, map ข้อสอบ, นาทีต่อไฟล์, A6 ผ่าน schema ไหม, token out ของ `merge_topics` เทียบกับเพดาน 16,000, A2b บน flash-lite (เวลา, token, จำนวนข้อที่ A4 ตัดได้)
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

## Next step

ขั้น 1 (🤖): เพิ่มโหมด `--provider vertex` ใน `poc/P3/common.py` แล้วต่อเข้า `ingest.py`, `run.py`, `score.py`

## Waiting on

ไม่มี

## Notes for next time

- PDF อยู่ที่ `evals/topics/mth10101/raw/` (gitignored · มีในเครื่อง Jam) · cache เดิมอยู่ใน `poc/P3/out/` อย่าเขียนทับ
- รอบ free tier (21 ต.ค.): flash-lite หัวข้อตรง 1/27 · A5 ของ flash 15/27 · A6 ของ flash ไม่ผ่าน schema (skill id ผิด 1 ตัว · token out 11,242 และ 14,944 จาก 16,000) · A2b 14 หน้า 40.5 วินาที บน flash
- P3 เสนอให้ code ตั้ง skill id เองแทน LLM (เปลี่ยนหลักการ · ไม่อยู่ในงานนี้)
