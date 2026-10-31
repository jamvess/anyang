# AI-07: ข้อมูลที่ส่งผ่าน Vertex ระหว่างใช้เครดิต Free Trial ถูกนำไป train ไหม

| | |
|---|---|
| Owner | Jam |
| Branch | `docs/ai07-vertex-data` |
| Checklist item | ไม่มีข้อตรงใน checklist · คำถามค้างจาก `specs/features/ai/gemini-vertex.md` §10 ข้อ 5 (PR #87) |
| Status | in progress · 2026-10-31 |

## Plan

- [x] 1. 🤖 หาเอกสารทางการของ Google ที่ตอบคำถาม: เงื่อนไขข้อมูลของ Vertex AI (Service Specific Terms → "Training Restriction"), เงื่อนไขของ Free Trial (ข้อยกเว้นจาก GCP Agreement), และเงื่อนไขของ Gemini API free tier (เพื่อเทียบ) · สรุปว่าต้องเช็คตรงไหน
- [x] 2. 🙋 Jam เปิดอ่าน 2 หน้าตามขั้นตอนที่เขียนให้ แล้วตอบในแชทว่าเงื่อนไขตรงกับที่สรุปไหม
- [x] 3. 🤖 แก้ 3 ไฟล์ที่ยังเขียนว่ารอยืนยัน (`gemini-vertex.md` §10 ข้อ 5, `specs/poc/reports/P2.md` §4 และ §6, `docs/report/ai-evaluation.md`) ให้เป็นข้อสรุปพร้อมลิงก์และวันที่อ่าน · ร่าง comment สำหรับ PR #87
- [x] 4. 🙋 Jam ตัดสินว่าจะให้ Claude โพสต์ comment ใน PR #87 ด้วย `gh` หรือโพสต์เอง

## Definition of done

- 3 ไฟล์ไม่มีข้อความว่า AI-07 "ยังไม่ได้ยืนยัน" อีก · มีลิงก์เอกสารและวันที่อ่าน
- ข้อสรุปมาจากเอกสารที่ Jam อ่านเองแล้ว ไม่ใช่สรุปของ Claude อย่างเดียว
- PR #87 มี comment ปิดคำถาม §10 ข้อ 5

## Decisions

- 2026-10-31 · (ขั้น 4) Jam เลือกให้ Claude โพสต์ comment ใน PR #87 ด้วย `gh pr comment` · โพสต์แล้ว
- 2026-10-31 · (ขั้น 2) Jam อ่าน Service Specific Terms ("Training Restriction") และ Free Trial terms แล้วยืนยันว่าตรงกับที่สรุป: Vertex ช่วง Free Trial ไม่นำข้อมูลไป train · ข้อยกเว้นของ Free Trial มีแค่ SLA, indemnity, Technical Support
- 2026-10-31 · (ขั้น 3) แก้ `gemini-vertex.md` §10 ข้อ 5, `P2.md` §4 และ §6, `ai-evaluation.md` §3.5 · ใส่ด้วยว่าก่อน Beta ยังต้องใช้บัญชีเสียเงิน (ai-orchestration §2.9) เพราะ Free Trial ไม่มี SLA และหมดอายุ 27 ม.ค. 2027 · ร่าง comment ของ #87 แล้ว
## Next step

ครบทุกขั้นแล้ว · Jam พิมพ์ `/work-done`

## Waiting on

ไม่มี

## Notes for next time

- ข้อสรุปเบื้องต้นจากการค้น (ต้องให้ Jam ยืนยัน): Service Specific Terms มี "Training Restriction" (Google ไม่ใช้ Customer Data ไป train โดยไม่ได้รับอนุญาต) · Free Trial terms บอกว่าใช้ GCP Agreement รวม Service Specific Terms ยกเว้นที่ระบุ (SLA, indemnity, TSS) · Gemini API free tier ("unpaid Services") Google ใช้ prompt/response ไปพัฒนาได้
