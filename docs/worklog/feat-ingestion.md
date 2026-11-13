# Ingestion ใน apps/api: ไฟล์ → หัวข้อ + ดาว (demo ขั้น 4)

| | |
|---|---|
| Owner | Jam |
| Branch | `feat/ingestion` |
| Checklist item | ⭐ demo ขั้น 4: ingestion ใน `apps/api` (งานเบื้องหลัง: classify → อ่านไฟล์ → chunk + embed → สกัดหัวข้อ → `compute_importance`) ลง `materials`, `chunks`, `topics`, `topic_sources` · `GET /exam-preps/{id}/ingestion` จริง (SM-01, SM-03, SM-04, CM-06, AI-08) · เริ่มก่อนข้ออื่น |
| Status | in progress · 2026-11-13 |

## Plan

ต้องเสร็จก่อน พฤ. 19 พ.ย. (ต่อทุกขั้นของ demo) · ย้าย pipeline ที่พิสูจน์แล้วใน `poc/P3/` (★★★ ตรง 83%) เข้า `apps/api` ตาม ai-orchestration §2.3.2–2.3.5 · prompt ใช้ของเดิมที่วัดแล้ว (A2b, A4, A5 v2, A6 v2, A7) · ไม่รอ endpoint materials ของ Junior: ต่อกันผ่าน interface (อ่านไฟล์ + เริ่ม job) แล้ว endpoint ของ Junior เรียกเข้ามา

- [x] 1. 🤖 (13 พ.ย. · Jam ok) `/spec-feature` → `specs/features/scope/ingestion.md`: ขั้นของ job และสถานะใน `ingestion_jobs` · ทางของแต่ละ `kind` (ชีท text layer / สแกน → A2b / ข้อสอบเก่า → A4) · chunk + embed · A5 → A6 → A7 → `compute_importance` · ตารางที่เขียน · รันซ้ำได้ (idempotent) · เมื่อไฟล์ล้ม · `GET /exam-preps/{id}/ingestion` ตาม api.md `Ingestion` · `classify_material` (A1, ยังไม่มี prompt) · interface ที่ Junior ต่อ · ข้อเสนอถึง Junior (service role, ตัวรัน job) · 🙋 Jam review spec
- [x] 2. 🤖 (13 พ.ย. · Jam ok) `/spec-to-tests`: unit test ด้วย fake provider + repository ปลอม · integration test เขียน DB จริงบน Supabase ในเครื่อง (RLS + `tenant_id`) · 🙋 Jam review test
- [x] 3. 🤖 (13 พ.ย. · green ในเครื่อง · Jam ok ai.yaml, api.md, แก้ fake ของ test) `/implement-feature` จน green · ไฟล์กลางที่อาจต้องแก้ (`config/ai.yaml`, `specs/system/api.md`) ถามก่อน
- [x] 4. 🤖 (13 พ.ย. · หัวข้อ 20/27, ★★★ 9/12, map 70%, ≤ 1.44 นาทีต่อไฟล์ · Jam รับผล · embed batch 1 บน Vertex) รันจริงบน Vertex กับชีท + ข้อสอบ MTH10101 (`evals/topics/mth10101/raw/`) ผ่าน pipeline ใหม่ · เทียบกับผล P3 (`poc/P3/score.py`) ว่าไม่แย่ลง
- [ ] 5. 🤖 อัปเดต docs + checklist แล้ว `/work-done`

## Definition of done

- ไฟล์ที่ยืนยันแล้วของการเตรียมสอบ 1 ชุด → job รันจนจบ → `topics` (ดาวจาก `compute_importance`), `topic_sources` (หน้าที่มา), `chunks` (text + vector 768), `past_exam_questions` อยู่ใน DB ของ tenant นั้น (RLS)
- `GET /exam-preps/{id}/ingestion` แสดงความคืบหน้ารายไฟล์และ `scope_ready`
- ผลบน MTH10101 ไม่แย่กว่า P3 (★★★ 10/12)
- ไม่มี provider SDK นอก gateway · ไม่มี threshold ใน code · ตารางใหม่ (ถ้ามี) มี `tenant_id` + RLS + isolation test

## Decisions

- 2026-11-13 · เลือกงานนี้ก่อน เพราะใหญ่สุดและขั้น 5–8 ของ demo รออยู่ (Jam)

## Next step

ขั้น 5: `/work-done` · ก่อน merge ส่งข้อความกลุ่ม (ไฟล์กลาง `config/ai.yaml`, `specs/system/api.md` + migration `0005`)

## Waiting on

Junior: endpoint materials + Storage (demo ขั้น 3) เพื่อต่อ end to end · ไม่บล็อกขั้น 1–4 ของงานนี้

## Notes for next time

- รันจริง: สคริปต์ใน scratchpad ใช้ `InMemoryIngestionStore` + `PyMuPdfDocuments` + ไฟล์ใน `evals/topics/mth10101/raw/` แล้วเขียนผลแบบ P3 ให้ `poc/P3/score.py` ให้คะแนน · ทุกไฟล์ ready · ขั้นรวม 2 นาที
- เน็ตหลุดกลางทางทำให้ embed ล้มด้วย `getaddrinfo failed` · ไฟล์ล้มตามที่ออกแบบ (ลองใหม่ได้)
