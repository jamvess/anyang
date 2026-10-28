# Feature: ห้องติว · การ์ดความคืบหน้า

| | |
|---|---|
| Area | tutor |
| Requirements | TM-15, TM-11, PM-03 (แสดงค่าที่ API คำนวณ) |
| Owner | May |
| Reviewer | Junior |
| Status | implemented (#63) · OQ 3, 4 ตอบแล้วใน api.md v1.4 (#71) · type ใช้ของที่ generate (#74) |
| Related system spec | api.md "SSE events" (`progress_card`), "ห้องติว" (`Message.card`) · ai-orchestration.md §2.2.2 (ระดับ 4 ขั้น, ความพร้อม, การ์ดเก็บใน `messages` role `card`) · wireframe S15, S24 · `chat-room-ui.md` AC-4 · `room-http.md` |

## 1. Context

ทุกครั้งที่เปิด session ระบบส่ง event `progress_card` ก่อนข้อความเปิดของติวเตอร์ (TM-15) และเมื่อผู้ใช้ขอดูความคืบหน้าระหว่างติวก็ส่งการ์ดใบเดียวกัน (TM-11) · การ์ดถูกเก็บใน `messages` เป็น role `card` (`card` = snapshot) ย้อนดูแชทเก่าจะเห็นสถานะ ณ วันนั้น · ตอนนี้หน้าเว็บข้าม event นี้ (chat-streaming.md AC-7) และซ่อนข้อความ role `card` (chat-room-ui.md AC-4) · feature นี้แสดงการ์ดตาม wireframe S15

## 2. Behavior

**ข้อมูล:** `{days_left, passed, total, readiness, topics: [{id, name, stars, level, review_due, origin}]}` (api.md) · หน้าเว็บ**ไม่คำนวณตัวเลขเอง** (apps/web/CLAUDE.md) แค่จัดรูปแบบ

**หน้าตา** (wireframe S15)

- หัวการ์ด: "ความคืบหน้า" + "สอบใน {days_left} วัน"
- 2 ตัวเลข: "ผ่านแล้ว {passed} / {total} หัวข้อ" และ "ความพร้อม {readiness × 100 ปัดเป็นจำนวนเต็ม}%"
- บรรทัดอธิบายใต้ตัวเลข: "ความพร้อม = สัดส่วนของเนื้อหาข้อสอบที่คาดว่าทำได้ ไม่ใช่คะแนนสอบ" (ai-orchestration §2.2.2)
- รายการหัวข้อ**ตามลำดับที่ API ส่งมา** (ไม่เรียงใหม่) · แต่ละแถว: ชื่อ, ดาว ★ เต็มตาม `stars` จาก 3, ระดับ
- ระดับ: `not_started` = "ยังไม่เริ่ม" · `weak` = "อ่อน" · `developing` = "กำลังดี" · `passed` = "ผ่าน" (ai-orchestration §2.2.2 · enum ตาม api.md v1.4) · ค่าอื่นแสดง "—" (API ไม่ส่ง แต่กันหน้าพังถ้า backend เพิ่มค่าใหม่)
- ป้ายเล็กข้างชื่อ (May ตัดสิน 2026-10-21): `review_due = true` → "ถึงรอบทวน" · `origin = "user"` → "นอกเอกสาร" (ai-orchestration §2.3.6)
- หัวข้อเกิน `PROGRESS_CARD_VISIBLE_TOPICS` (6 · ค่าของ UI · May ตัดสิน ตาม wireframe S15): แสดง 6 หัวข้อแรก ตามด้วยปุ่ม "อีก {n} หัวข้อ" · กดแล้วแสดงครบทุกหัวข้อในการ์ด และปุ่มหายไป

**แสดงตรงไหน**

- ข้อความ role `card` ในประวัติ (`Message.card` ไม่เป็น null) → แสดงการ์ดในตำแหน่งตามเวลา · ไม่ใช่ bubble (ไม่มีชื่อผู้พูด, ไม่มี `data-role`) จึงยังตรงกับ chat-room-ui AC-4 ที่ว่า "ไม่มี bubble"
- ข้อความ role `card` ที่ `card` เป็น null → ไม่แสดงอะไร (เหมือนเดิม)
- event `progress_card` ระหว่าง stream (ทั้งตอนเปิดห้องและตอนตอบ) → เพิ่มการ์ดต่อท้ายรายการ ณ ตำแหน่งที่ event มา · ข้อความของติวเตอร์ที่ตามมาเป็น bubble ใหม่หลังการ์ด
- การ์ดคั่นกลาง: ข้อความติวเตอร์ก่อนและหลังการ์ดไม่รวมกันใต้ชื่อเดียว (การ์ดตัดการรวมตาม AC-3)

**Accessibility:** การ์ดเป็น `role="group"` มี `aria-label="ความคืบหน้า"` · ปุ่ม "อีก n หัวข้อ" เข้าถึงด้วย keyboard ได้

## 3. Inputs and outputs

| | Type / schema | ตัวอย่าง |
|---|---|---|
| Input | `Message` role `card` จาก `GET /sessions/{id}` · SSE `progress_card` | ข้อความ `m0` ใน `apps/api/app/stubs/room.json` |
| Output | การ์ดในรายการข้อความ | "ผ่านแล้ว 1 / 4 หัวข้อ · ความพร้อม 25%" |

## 4. Acceptance criteria

ใช้ข้อมูลการ์ดจาก stub (`days_left 5, passed 1, total 4, readiness 0.25`, 4 หัวข้อ) เว้นแต่ระบุ

**แสดงจากประวัติ (TM-15)**

- **AC-1 (TM15)** Given ข้อความ role `card` ที่มีการ์ดของ stub When render รายการ Then เห็นการ์ด (`role="group"` ชื่อ "ความคืบหน้า") ที่มี "สอบใน 5 วัน", "1 / 4 หัวข้อ", "25%" และบรรทัดอธิบายความพร้อม · ไม่มี element `[data-role]` ของข้อความนี้
- **AC-2 (TM15)** Given การ์ดของ stub Then แถวหัวข้อเรียง ตัวประกอบร่วม, ผลต่างกำลังสอง, กำลังสองสมบูรณ์, แยกตัวประกอบพหุนามดีกรีสอง (ตามที่ส่งมา) · ระดับเป็น "ผ่าน", "กำลังดี", "ยังไม่เริ่ม", "อ่อน" ตามลำดับ · ดาวเต็ม 1, 3, 2, 3
- **AC-3 (TM15)** Given หัวข้อที่ `review_due = true` Then แถวนั้นมีป้าย "ถึงรอบทวน" · หัวข้ออื่นไม่มี · Given หัวข้อที่ `origin = "user"` Then มีป้าย "นอกเอกสาร"
- **AC-4 (TM15)** Given `level = "mystery"` Then แถวแสดงระดับ "—"
- **AC-5 (PM03)** Given `readiness` = 0.004, 0.005, 0.996 Then แสดง 0%, 1%, 100% (ปัดครึ่งขึ้น)
- **AC-6 (TM15)** Given ข้อความ role `card` ที่ `card = null` Then ไม่มีการ์ดและไม่มี bubble

**หัวข้อเยอะ (TM-15 · boundary ที่ `PROGRESS_CARD_VISIBLE_TOPICS`)**

- **AC-7 (TM15)** มี `PROGRESS_CARD_VISIBLE_TOPICS` หัวข้อพอดี → แสดงครบ ไม่มีปุ่ม "อีก" · มี `PROGRESS_CARD_VISIBLE_TOPICS + 1` หัวข้อ → แสดง 6 แถว และปุ่ม "อีก 1 หัวข้อ" · When กดปุ่ม Then แสดง 7 แถว และปุ่มหายไป

**ระหว่าง stream (TM-15, TM-11)**

- **AC-8 (TM15)** Given stream เปิดห้อง `progress_card` → `token tutor "สวัสดี"` → `done` Then การ์ดอยู่ก่อน bubble ติวเตอร์ "สวัสดี" (ใช้ fixture `room_session_start.txt`)
- **AC-9 (TM11)** Given ห้องที่มีข้อความแล้ว When ส่ง "ขอดูความคืบหน้า" และ stream ตอบ `token tutor "นี่เลย"` → `progress_card` → `token tutor "ยังตามแผนอยู่"` → `done` Then เห็น bubble ติวเตอร์ "นี่เลย", การ์ด, bubble ติวเตอร์ "ยังตามแผนอยู่" ตามลำดับ และชื่อติวเตอร์ขึ้น 2 ครั้ง (การ์ดตัดการรวม)

**ไม่กระทบของเดิม**

- **AC-10** test เดิมของ MessageList, RoomPageHttp, chat-room-ui AC-11 (มีแค่ปุ่มแนบรูปกับส่ง · fixture มี 4 หัวข้อจึงไม่มีปุ่ม "อีก") ผ่านโดยไม่แก้ · **ยกเว้น** chat-streaming AC-7 ใน `ChatRoomStream.test.tsx` ที่ส่ง `progress_card` คั่น token แล้วคาด bubble เดียว ขัดกับ AC-9 · ตัดบรรทัด `progress_card` ออกจาก test นั้น (May อนุมัติ 2026-10-21) ส่วน `problem`, `verdict`, event ที่ไม่รู้จักยังถูกข้ามเหมือนเดิม

**AC-tenant (SA-06):** ไม่เกี่ยว · แสดงข้อมูลที่ API ส่งมา การแยก tenant อยู่ที่ API

## 5. Data changes

ไม่มี

## 6. API / SSE changes

ไม่มี · ใช้ `progress_card` และ `Message.card` ที่มีอยู่ (api.md)

## 7. AI calls

ไม่มี (การ์ด render จาก DB ไม่ผ่าน LLM · TM-15)

## 8. Test plan

| Test | ระดับ | ครอบคลุม AC |
|---|---|---|
| `tests/chat/ProgressCard.test.tsx` (ใหม่) | unit (component) | AC-1 ถึง AC-7 |
| `tests/chat/ChatRoomStream.test.tsx` (เพิ่ม test) | integration (ChatRoom + transport ปลอม) | AC-8, AC-9 |
| test เดิมทั้งหมด | — | AC-10 |

## 9. Out of scope

- intent "ขอดูความคืบหน้า" เป็นงานของ backend (router) · หน้าเว็บแค่แสดง event ที่มา
- กดหัวข้อในการ์ดเพื่อเปลี่ยนเรื่อง (TM-01 ให้ผู้ใช้พิมพ์ขอเอง)
- การ์ดโจทย์ (`problem`) · feature แยก

## 10. Open questions

ตัดสินแล้ว (May · 2026-10-21)

1. หัวข้อเยอะ: แสดง 6 หัวข้อ + ปุ่ม "อีก n หัวข้อ" (AC-7)
2. `review_due` และ `origin = user`: ป้ายเล็กข้างชื่อ (AC-3)

Junior ตอบแล้ว (api.md v1.4 · #71 · 2026-10-21)

3. `level` = `not_started` | `weak` | `developing` | `passed` (ตรงกับที่ spec ใช้) · `topics[]` เป็น model `ProgressTopic` แล้ว หน้าเว็บใช้ type ที่ generate (#74)
4. `origin` = `doc` | `user` · `stars` ไม่เป็น null

## 11. Spec changes needed

- ~~api.md `progress_card.topics[]`~~ ทำแล้วใน v1.4 (#71)
- **chat-room-ui.md** AC-4: เพิ่มหมายเหตุว่าข้อความ role `card` ที่มี `card` แสดงเป็นการ์ด (ไม่ใช่ bubble) ตาม `progress-card.md`
- **chat-streaming.md** AC-7: `progress_card` ไม่ถูกข้ามแล้ว
