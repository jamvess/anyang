# ตรวจ ai-orchestration.md และ learning-model.md ให้ครบ (D2)

| | |
|---|---|
| Owner | Jam |
| Branch | `docs/d2-ai-learning-spec-review` |
| Checklist item | ตรวจ `specs/system/ai-orchestration.md` และ `learning-model.md` ใน repo ให้ครบ (D2) |
| Status | in progress · 2026-10-20 |

## Plan

- [ ] 1. 🤖 ตรวจแบบไล่เทียบอัตโนมัติ: (ก) key ของ `config/learning.yaml` ที่ spec อ้าง มีจริงไหม และ key ที่ไม่มี spec อ้างเลย (ข) AI purpose ใน §3.1 ตรงกับ `config/ai.yaml` และโฟลเดอร์ใน `prompts/` ไหม (ค) requirement ID ที่ spec อ้าง มีใน `requirements.md` ไหม และ requirement AI-/TM-/AM- ที่ยังไม่มี spec ส่วนไหนรองรับ (ง) ตาราง §3.2 ตรงกับ `data-model.md` และ `supabase/migrations/0001_init.sql` ไหม (จ) SSE events §3.3 ตรงกับ `api.md` ไหม (ฉ) ตัวเลขใน spec ที่ไม่ได้มาจาก `learning.yaml` (magic number)
- [ ] 2. 🤖 อ่านทั้งสองไฟล์ทีละ section หา: ข้อความที่ขัดกันเอง, ลำดับเลข section ที่สลับ (2.3 มาก่อน 2.2, 2.1 อยู่หลัง 2.5), ข้อความที่อ้างภาพใน .docx (9 จุด) ซึ่งไม่มีใน repo, สิ่งที่ PoC P1/P3 เจอแล้วแต่ spec ยังไม่เขียน
- [ ] 3. 🤖 รวบรวมเป็นตาราง findings ใน PR description: จุด · ปัญหา · ข้อเสนอ · ไฟล์ของใคร
- [ ] 4. 🙋 Jam ตัดสินทีละข้อ: แก้เลย / ไม่แก้ / เลื่อนไปทำหลังผล PoC (ข้อ S4 "อัปเดต threshold ตามผล P1 P2 P3") · ตอบเป็นเลขข้อ เช่น "1 แก้, 2 เลื่อน"
- [ ] 5. 🤖 แก้ตามที่ Jam ตัดสินใน `ai-orchestration.md` และ `learning-model.md` (ไฟล์ของ Jam) · ถ้าต้องแก้ไฟล์ของคนอื่นหรือไฟล์กลาง (`requirements.md`, `api.md`, `config/ai.yaml`, `data-model.md`) จะถามก่อนทุกครั้ง
- [ ] 6. 🤖 ติ๊ก checklist ใน `docs/team/sprint-checklists.md` แล้ว `/work-done`

## Definition of done

- ทุก finding มีคำตัดสิน (แก้ / ไม่แก้ / เลื่อน พร้อมเหตุผล)
- ข้อที่ตัดสินว่าแก้ ถูกแก้แล้วใน PR นี้ · ข้อที่เลื่อนเขียนไว้ว่าจะทำตอนไหน
- การอ้างอิงข้ามไฟล์ (config key, purpose, requirement ID, table, SSE event) ตรงกันหมด หรือมีเหตุผลที่ยังไม่ตรง
- checklist ข้อนี้ติ๊กแล้ว

## Decisions

- 2026-10-20 · เลือกทำข้อนี้ระหว่างรอโควตา free tier (P1/P3 รันได้หลัง 14:00 น.) · งานนี้ไม่ต้องใช้โควตา

## Next step

ขั้น 1: ไล่เทียบ config key, purpose, requirement ID, table, SSE event ระหว่างสอง spec กับไฟล์ที่เกี่ยวข้อง

## Waiting on

ไม่มี

## Notes for next time

- `poc/P1/` ขึ้นเป็น untracked บน branch นี้ (คือ `out/` และ `results/` ของ P1) · ห้าม commit
