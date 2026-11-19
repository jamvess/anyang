# fake provider มีคำตอบตั้งต้นของ ingestion

| | |
|---|---|
| Owner | Jam |
| Branch | `feat/fake-ingestion` |
| Checklist item | fake provider มีคำตอบตั้งต้นของ `classify_material` (และ purpose อื่นของ ingestion) ให้ลองเส้นอัปโหลดในโหมด fake ได้ (พบใน #151) |
| Status | in progress · 2026-11-19 |

## Plan

ตอนนี้ `AI_PROVIDER=fake` (`app/ai/gateway.py` `_build_gateway`) ตอบแค่ `tutor_reply` · ingestion เรียก `classify_material`, `vision_extract`, `vision_extract_pages`, `split_past_exam`, `extract_topics_local`, `merge_topics`, `map_questions` และ `embed` · ทุกตัวล้ม ("no scripted response") และ `FakeProvider` ไม่มี `embed` เลย · ไฟล์จึงล้มทุกไฟล์ในโหมด fake (#151) · ทุกไฟล์ของ prep ได้ key `f1`, `f2`, … (`file_keys`) คำตอบปลอมจึงอ้าง `f1:1-1` ได้

- [ ] 1. 🤖 แก้ spec `specs/features/scope/ingestion.md` §2.7 (ตัวรัน job ในเครื่อง): โหมด fake ตอบทุก purpose ของ ingestion ด้วยคำตอบตายตัวที่ผ่าน schema · `embed` ปลอมคืน vector ยาว `embedding.dimensions` · prep ที่อัปโหลดในโหมด fake ไปถึงหน้า scope ได้ (หัวข้อปลอม 2–3 หัวข้อ) → 🙋 Jam review
- [ ] 2. 🤖 `/spec-to-tests` (unit: คำตอบตั้งต้นผ่าน schema ทุกตัว · เส้นเต็ม classify → ingest → build_scope ใน fake mode ได้ scope) → 🙋 Jam review test
- [ ] 3. 🤖 `/implement-feature`: คำตอบตั้งต้นใน `app/stubs/` · `FakeProvider.embed` · `_build_gateway` ใส่ defaults · ruff · pytest ทั้งชุด
- [ ] 4. 🙋 (ถ้าอยาก) ลองในเบราว์เซอร์ด้วย `AI_PROVIDER=fake`

## Definition of done

- ในโหมด fake อัปโหลด PDF → AI ดูไฟล์ → ยืนยัน → อ่านไฟล์ → หน้า scope ได้โดยไม่เรียก AI จริง
- test ใหม่ผ่าน · test เดิมผ่านโดยไม่แก้ · ruff, pytest, CI เขียว

## Decisions

- 2026-11-19 · Jam เลือกข้อ 1 ของ `/work-start Jam`

## Next step

ข้อ 1: แก้ spec `ingestion.md` §2.7 แล้วให้ Jam review

## Waiting on

ไม่มี

## Notes for next time

- API ทั้งชุดในเครื่องใช้ 8–22 นาที (integration บน `anyang-dev`) · unit อย่างเดียวราว 4–5 นาที
