# Learning model: difficulty gate + mastery cap (A + C)

| | |
|---|---|
| Owner | Jam |
| Branch | `docs/learning-model-difficulty` |
| Checklist item | ไม่มีข้อตรง · ใกล้สุด: "อัปเดต threshold ใน AI flow specs และ `learning-model.md` ตามผล P1 P2 P3 (D2)" (Jam · S4) · งานนี้มาจากการทบทวน design ก่อน Progress 1 |
| Status | in progress · 2026-10-26 |

## Plan

- [x] 1. 🤖 ร่าง `learning-model.md` v1.2: §1 บอกข้อจำกัดว่า BKT ไม่รู้ความยาก · §4 ระดับเป้าตามดาวและ mode + เพดาน mastery ตามระดับยากสุดที่ทำถูกเอง (ค่า [calc] ผูกกับ `weak_below` และ `mastery_threshold`) · §5 readiness ใช้ mastery หลังเพดาน · §10 เพิ่ม KT-IDEM และ Elo เป็นทางเลือกหลัง Alpha
- [x] 2. 🤖 แก้ `config/learning.yaml` ให้ตรงกับ §4 (key ระดับเป้า + เพดาน) และเช็คว่า loader ใน `apps/api` ยังอ่านได้ (`uv run pytest`)
- [ ] 3. 🤖 แก้ `ai-orchestration.md` §2.2.4 และ §2.5.2 ให้เงื่อนไข "ผ่าน" ตรงกับ §4
- [ ] 4. 🙋 Jam review diff ทั้ง 3 ไฟล์ (ตัดสินค่าเป้าของ ★★ และ ★)
- [ ] 5. 🙋 บอกในแชทกลุ่ม: กระทบการ์ดความคืบหน้าของ May (ระดับและความพร้อม % จะต่ำลงถ้ายังไม่เคยทำโจทย์ระดับเป้า) และ TM-16, PM-03 ใน `requirements.md` (ไฟล์ร่วม) ต้องแก้ตาม · ขอ OK ก่อนแก้ `requirements.md`
- [ ] 6. 🤖 แก้ TM-16 และ PM-03 หลังทีม OK (หรือเขียนเป็นข้อเสนอใน PR ถ้ายังไม่ OK)

## Definition of done

- `learning-model.md`, `config/learning.yaml`, `ai-orchestration.md` บอกกติกาเดียวกัน: ผ่านต้องมีข้อที่ทำถูกเองที่ระดับเป้า · mastery ที่ใช้คิดระดับ, ผ่าน และ readiness ถูกจำกัดด้วยเพดานตามระดับยากสุดที่ทำถูก
- ไม่มีตัวเลขใหม่ที่ไม่มีป้ายที่มา (เพดานเป็น [calc] จากค่าที่มีอยู่)
- DB ไม่เปลี่ยน: `topic_progress.mastery` เก็บค่า BKT ดิบ
- `uv run pytest` และ `uv run ruff check .` ผ่าน
- PR review โดย Junior (CODEOWNERS ของ `config/learning.yaml`) · บอก May ในแชทกลุ่มแล้ว

## Decisions

- 2026-10-26 · ใช้ A (ประตูความยาก) + C (เพดาน mastery) ใน MVP · BKT มาตรฐานไม่คิดความยาก ตอบถูกโจทย์ง่าย 3 ข้อก็ถึง 0.95 · B (guess/slip ตามความยาก) แค่ชะลอ ไม่กัน · D (Elo/logistic) รอคุยกับอาจารย์และข้อมูลหลัง Alpha
- 2026-10-26 · เก็บค่า BKT ดิบใน DB ใช้เพดานตอนคิดระดับ, ผ่าน, readiness · ทำโจทย์ถึงเป้าแล้วค่าจริงขึ้นทันที และมีข้อมูลดิบไว้ fit ทีหลัง
- 2026-10-26 · (ร่าง รอ Jam ยืนยัน) เพดานขาด 1 ขั้น = (weak_below + mastery_threshold) ÷ 2 = 0.725 · ขาด ≥ 2 ขั้น = weak_below · คิดจาก `bkt.*` จึงไม่เพิ่ม key ใน config · Triage ใช้เป้า ★★ = 2 เหมือน Tight · "ผ่าน" เปลี่ยนจาก "จบด้วยโจทย์ระดับเป้า" เป็น "เคยทำถูกเองที่ระดับเป้า" (`d_max`)

## Next step

ขั้น 3: แก้ `specs/system/ai-orchestration.md` §2.2.4 "เงื่อนไข Done" และตาราง mode ใน §2.5.2 ให้ใช้ระดับเป้า + mastery_eff ตาม `learning-model.md` §4

## Waiting on

ไม่มี

## Notes for next time

- 2026-10-26 · Jam อนุญาตให้แก้ `apps/api/app/settings.py` (ของ Junior) เพิ่ม 2 field ใน `DoneConfig` · ต้องบอก Junior ใน PR

- ค่าที่เสนอ: เป้า ★★★ = 3 · ★★ = 3 (ปกติ) / 2 (Tight) · ★ = 2 · เพดาน: ต่ำกว่าเป้า ≥ 2 ขั้น → `weak_below` · ต่ำกว่าเป้า 1 ขั้น → ต่ำกว่า `mastery_threshold` · ถึงเป้า → ไม่มีเพดาน
- งานวิจัยที่ต้องเปิดอ่านก่อนอ้าง: Pardos & Heffernan (2011) KT-IDEM · Pelánek (2016) Elo rating in adaptive educational systems
