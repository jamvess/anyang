# ห้องติวตอนมี token: การ์ดจาก DB + เลือกหัวข้อ + โจทย์ที่ SymPy ตรวจเฉลยแล้ว (demo ขั้น 6)

| | |
|---|---|
| Owner | Jam |
| Branch | `feat/room-problems-db` |
| Checklist item | ⭐ demo ขั้น 6: ห้องติวในทางที่มี token: คำทัก `open_session` + การ์ดจาก DB + เลือกหัวข้อด้วยกฎง่าย + `generate_problem` ที่ SymPy ตรวจเฉลยแล้ว (คลังโจทย์เป็นทางสำรอง · D3) (TM-01, TM-15, AM-11) |
| Status | in progress · 2026-11-13 |

## Plan

ตอนนี้ห้องที่มี token เปิดมาแค่คำทักจาก template ไม่มีการ์ด ไม่มีโจทย์ (#123) · งานนี้ทำให้เปิดห้องแล้วได้: การ์ดความคืบหน้าจาก DB → tutor ทัก (`open_session`) พร้อมเหตุผลที่เลือกหัวข้อ → โจทย์ของหัวข้อนั้นที่สร้างด้วย `generate_problem` และ SymPy ยืนยันเฉลยแล้ว เก็บใน `problems` · หัวข้อมาจาก ingestion (#130)

- [x] 1. 🤖 (13 พ.ย. · Jam ok) `/spec-feature` → `specs/features/tutor/room-problems-db.md`: เปิดห้อง (การ์ดจาก `topics` + `topic_progress` · ไม่มีหัวข้อ → แบบเดิม) · กฎเลือกหัวข้อแบบง่าย (ยังไม่ใช่ planner เต็ม · TM-01, TM-02) · `generate_problem/v1` (input: หัวข้อ, skill, ข้อความจากหน้าที่มา, ระดับยากเป้าตามดาว · output: โจทย์ + นิพจน์ที่ SymPy คำนวณได้ + เฉลย + ขั้นตอน + `answer_format`) · ตรวจเฉลยด้วย SymPy แล้วสร้างใหม่ไม่เกิน `checker.max_generate_retries` (AM-11 · ai-orchestration §2.4.6) · ทางสำรองเมื่อสร้างไม่ผ่าน · บันทึก `problems` + การ์ดโจทย์ใน `messages` (กลับมาเห็นได้ · TM-13) · หัวข้อที่ยังไม่ยืนยัน scope · 🙋 Jam review spec + ร่าง prompt
- [x] 2. 🤖 (13 พ.ย. · Jam ok) `/spec-to-tests` (fake provider + repository ปลอม + SymPy จริง) · 🙋 Jam review test
- [x] 3. 🤖 (13 พ.ย. · green ยกเว้น test boundary ที่ใช้ setattr บน config frozen · รอ Jam ok แก้ test) `/implement-feature` จน green · ไฟล์กลาง (`config/ai.yaml` ค่า `generate_problem`, `specs/system/api.md`) ถามก่อน
- [ ] 4. 🤖 รันจริงบน Vertex: สร้างโจทย์ของหัวข้อ MTH10101 (จากผล ingestion) แล้วนับว่า SymPy ยืนยันผ่านกี่ % ในรอบที่ 1, 2, 3 (calibrate `max_generate_retries` · learning.yaml บอกให้วัดตอนมี feature)
- [ ] 5. 🤖 อัปเดต docs + checklist แล้ว `/work-done`

## Definition of done

- มี token + prep ที่มีหัวข้อ: เปิดห้องได้ `session` → `progress_card` (จาก DB) → คำทักที่บอกหัวข้อและเหตุผล → `problem` ที่มีแถวใน `problems` (`verified = true`) → `done`
- โจทย์ทุกข้อที่ส่งถึงผู้ใช้ผ่าน SymPy (AM-11) · สร้างไม่ผ่าน → ทางสำรองตาม spec
- prep ที่ยังไม่มีหัวข้อ: ทำงานเหมือนเดิม (#123)
- RLS: `problems` และ `messages` ของ tenant อื่นมองไม่เห็น

## Decisions

- 2026-11-13 · เลือกขั้น 6 ก่อนขั้น 7 เพราะขั้น 7–9 รอโจทย์จริงจากขั้นนี้ (Jam)

## Next step

ขั้น 1: อ่าน `room-sessions-db.md`, `demo-room.md` §2 F, ai-orchestration §2.2.2–2.2.4 + §2.4.6, learning-model §4 แล้วเขียน spec

## Waiting on

Junior: `POST /scope/confirm` จริง (demo ขั้น 5) · ไม่บล็อกงานนี้ ถ้า spec ใช้หัวข้อที่ยังไม่ยืนยันได้ (เสนอใน spec)

## Notes for next time

- ไม่มี
