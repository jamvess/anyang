# AI-07: ข้อมูลที่ส่งผ่าน Vertex ระหว่างใช้เครดิต Free Trial ถูกนำไป train ไหม

| | |
|---|---|
| Owner | Jam |
| Branch | `docs/ai07-vertex-data` |
| Checklist item | ไม่มีข้อตรงใน checklist · คำถามค้างจาก `specs/features/ai/gemini-vertex.md` §10 ข้อ 5 (PR #87) |
| Status | in progress · 2026-10-31 |

## Plan

- [x] 1. 🤖 หาเอกสารทางการของ Google ที่ตอบคำถาม: เงื่อนไขข้อมูลของ Vertex AI (Service Specific Terms → "Training Restriction"), เงื่อนไขของ Free Trial (ข้อยกเว้นจาก GCP Agreement), และเงื่อนไขของ Gemini API free tier (เพื่อเทียบ) · สรุปว่าต้องเช็คตรงไหน
- [ ] 2. 🙋 Jam เปิดอ่าน 2 หน้าตามขั้นตอนที่เขียนให้ แล้วตอบในแชทว่าเงื่อนไขตรงกับที่สรุปไหม
- [ ] 3. 🤖 แก้ 3 ไฟล์ที่ยังเขียนว่ารอยืนยัน (`gemini-vertex.md` §10 ข้อ 5, `specs/poc/reports/P2.md` §4 และ §6, `docs/report/ai-evaluation.md`) ให้เป็นข้อสรุปพร้อมลิงก์และวันที่อ่าน · ร่าง comment สำหรับ PR #87
- [ ] 4. 🙋 Jam ตัดสินว่าจะให้ Claude โพสต์ comment ใน PR #87 ด้วย `gh` หรือโพสต์เอง

## Definition of done

- 3 ไฟล์ไม่มีข้อความว่า AI-07 "ยังไม่ได้ยืนยัน" อีก · มีลิงก์เอกสารและวันที่อ่าน
- ข้อสรุปมาจากเอกสารที่ Jam อ่านเองแล้ว ไม่ใช่สรุปของ Claude อย่างเดียว
- PR #87 มี comment ปิดคำถาม §10 ข้อ 5

## Decisions

## Next step

ขั้น 2 (🙋 Jam): เปิดเอกสาร 2 หน้าตามที่ Claude เขียนในแชท แล้วตอบ

## Waiting on

ไม่มี

## Notes for next time

- ข้อสรุปเบื้องต้นจากการค้น (ต้องให้ Jam ยืนยัน): Service Specific Terms มี "Training Restriction" (Google ไม่ใช้ Customer Data ไป train โดยไม่ได้รับอนุญาต) · Free Trial terms บอกว่าใช้ GCP Agreement รวม Service Specific Terms ยกเว้นที่ระบุ (SLA, indemnity, TSS) · Gemini API free tier ("unpaid Services") Google ใช้ prompt/response ไปพัฒนาได้
