# P4-lite ส่วนแรก: วัด TTFT ของ SSE บน api-staging (AI จำลอง)

| | |
|---|---|
| Owner | May |
| Branch | `poc/P4-lite-ttft` |
| Checklist item | เขียน report P4-lite ร่วมกับ Junior (S3) · ทำส่วนวัด TTFT พื้นฐาน · NFR-P1 (TTFT p95 < 2 วินาที) |
| Status | in progress · 2026-10-28 |

## Plan

- [ ] 1. 🤖 `poc/P4-lite/ttft.py`: สคริปต์ Python (httpx · รันผ่าน `uv` ของ `apps/api`) เปิด session ด้วย `POST /exam-preps/{id}/sessions` แล้วส่ง N ข้อความไป `POST /sessions/{id}/messages` ทีละข้อความ · วัดเวลาจนได้ event `token` แรก (TTFT) และเวลาจนได้ `done` · แยกครั้งแรก (อาจเป็น cold start ของ Cloud Run) ออกจากที่เหลือ · เขียนผลเป็น JSON ใน `poc/P4-lite/results/`
- [ ] 2. 🤖 test ของส่วนที่ไม่ใช้เน็ต (หา token แรกใน SSE, คำนวณ p50/p95) ใน `poc/P4-lite/test_ttft.py` ชื่อขึ้นต้นด้วย `NFRP1`
- [ ] 3. 🤖 รัน 50 ข้อความกับ `api-staging` (URL ใน `infra/README.md` · ไม่มี secret · AI จำลอง ไม่เสีย credit) แล้ว commit ผล
- [ ] 4. 🤖 `poc/P4-lite/README.md`: วิธีรัน, ผล, ข้อจำกัด (stub ไม่ผ่าน `ai.call` ยังไม่มี LLM จริง → ตัวเลขนี้คือ overhead ของ Cloud Run + SSE เท่านั้น), สิ่งที่ต้องวัดต่อเมื่อเปิด Gemini
- [ ] 5. 🙋 May เปิด demo link ใน Edge แล้วดูใน DevTools ว่า request ไป staging จริง (ขั้นละเอียดให้ตอนถึงข้อนี้)

## Definition of done

- สคริปต์รันซ้ำได้ด้วยคำสั่งเดียว และใช้ซ้ำได้ทันทีเมื่อ staging เปิด Gemini
- มีตัวเลข TTFT p50/p95 และ cold start ของ api-staging (AI จำลอง) อยู่ใน `poc/P4-lite/results/` และ README
- test ของส่วนที่ไม่ใช้เน็ตผ่าน · ruff ผ่าน
- checklist "เขียน report P4-lite ร่วมกับ Junior" ยังไม่ติ๊ก (เหลือ Gemini จริง, ต้นทุน, สลับ provider) แต่มี sub-bullet บอกส่วนที่เสร็จ

## Decisions

- 2026-10-28 · วัดกับ AI จำลองก่อน เพราะ Junior ยังห้ามเปิด `AI_PROVIDER=live` บน staging (infra/README.md) · ตัวเลขนี้คือ overhead ของ infra ใช้แยกว่าเวลาที่เพิ่มขึ้นทีหลังมาจาก LLM

## Next step

ขั้น 1: เขียน `poc/P4-lite/ttft.py`

## Waiting on

- Junior: เปิด Gemini บน staging (ต้องเช็ค JWT ทุก endpoint ก่อน) เพื่อวัดรอบจริง · ไม่บล็อกงานนี้

## Notes for next time

- staging: https://api-staging-659706857266.asia-southeast1.run.app · stub ส่ง `tutor_reply.sse` ตรงๆ ไม่มี delay ไม่ผ่าน gateway
