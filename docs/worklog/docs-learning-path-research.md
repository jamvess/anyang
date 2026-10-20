# รายการงานวิจัยรองรับ learning path และ progress tracking

| | |
|---|---|
| Owner | Jam |
| Branch | `docs/learning-path-research` |
| Checklist item | เตรียมรายการงานวิจัยเรื่อง learning path และ progress tracking สำหรับคุยกับทีม (`learning-model.md` §10) |
| Status | in progress · 2026-10-20 |

## Plan

- [x] 1. 🤖 ตั้งคำถามต่อด้าน (คุยกับ Jam แล้ว 20 ต.ค. · ดู Decisions)
- [ ] 2. 🤖 ค้นและตรวจงานวิจัยด้านละ 2–3 ชิ้นใน 7 ด้าน (เริ่มจาก 1–3) · ทุกชิ้นต้องเปิดลิงก์ได้จริงและอ่าน abstract แล้ว · ชิ้นที่อ้างอยู่แล้วใน learning-model.md ไม่ค้นซ้ำ · สรุป: พบอะไร · รองรับหรือท้าทาย design ข้อไหน · ใช้ที่ไหน (code / config / prompt / UI / รายงาน)
- [ ] 3. 🤖 เขียนเป็นเอกสาร `docs/research/learning-path.md` (ภาษาไทย) และลิงก์จาก `learning-model.md` §10 · งานวิจัยที่ใช้อ้างค่าใน config อยู่แล้ว (Corbett & Anderson, Cepeda, Beck & Gong ฯลฯ) ไม่ต้องค้นซ้ำ แค่อ้างถึง
- [ ] 4. 🙋 Jam อ่านแล้วเลือก: ชิ้นไหนจะเอาไปคุยกับทีมและอาจารย์ · ข้อเสนอเปลี่ยน design ข้อไหนที่จะเสนอ · ตอบเป็นเลขข้อ
- [ ] 5. 🤖 ทำ agenda 1 หน้าสำหรับคุยกับทีม/อาจารย์: คำถามที่ต้องตัดสิน + งานวิจัยที่รองรับแต่ละข้อ
- [ ] 6. 🤖 ติ๊ก checklist แล้ว `/work-done`

## Definition of done

- ครบ 7 ด้าน (ดู Decisions) · แต่ละด้านมีงานวิจัยอย่างน้อย 2 ชิ้นที่ตรวจแล้วว่ามีจริง (ลิงก์เปิดได้)
- แต่ละชิ้นบอกว่ารองรับหรือท้าทายการตัดสินใจไหนของเรา
- Jam เลือกแล้วว่าจะเอาอะไรไปคุย · มี agenda พร้อมใช้
- checklist ข้อนี้ติ๊กแล้ว

## Decisions

- 2026-10-20 · เลือกทำข้อนี้ระหว่างรอโควตา free tier (P1/P3 รันได้หลัง 14:00 น.)
- 2026-10-20 · (Jam ตัดสิน) เอาเฉพาะ core ของ MVP 7 ด้าน: 1 knowledge tracing · 2 mastery learning · 3 progress/readiness · 4 learning path (prerequisite) · 5 ฝึกด้วยโจทย์ + feedback (retrieval practice, pretesting, formative feedback) · 6 spaced review · 7 พิสูจน์ผล (learning gain) · ตัดออกจาก MVP: แบ่งเวลาเมื่อเวลาไม่พอ, interleaving, motivation/affect, LLM tutor risk
- 2026-10-20 · (Jam ok) เอกสารมีคอลัมน์ "ใช้ที่ไหน": ด้าน 1–6 อยู่ในแอป (code/config/prompt/UI) และใช้ในรายงาน · ด้าน 7 อยู่นอกแอป (pilot + รายงาน) แอปแค่เก็บ log · calibration หลัง Alpha (↩️) ทำนอกแอปแล้วแก้ config
- 2026-10-20 · คำถามที่จะใส่ agenda: ด้าน 1 BKT ระดับหัวข้อ vs ระดับ skill (Done ดูระดับ skill) · ด้าน 3 สูตรความพร้อมยังไม่เคยเทียบกับคะแนนสอบจริง และ mastery ไม่มี forgetting

## Next step

ขั้น 2: ค้นงานวิจัยด้าน 1 (knowledge tracing: Pelánek 2017, Gervet et al. 2020, Khajah et al. 2016) ด้าน 2 (Bloom 1968, Kulik et al. 1990) ด้าน 3 (Bull & Kay open learner model, Dunlosky & Rawson 2012) · ตรวจว่ามีจริง อ่าน abstract

## Waiting on

ไม่มี

## Notes for next time

- `poc/` ขึ้นเป็น untracked บน branch นี้ (คือ `out/` และ `results/` ของ P1) · ห้าม commit
