# ERD ของ data model ให้ครบตาม `0001_init.sql` (D3)

| | |
|---|---|
| Owner | Junior |
| Branch | `docs/erd-d3` |
| Checklist item | ปรับ `schema.sql` ตามที่เจอระหว่าง P3 + วาด ERD (D3) |
| Status | ready for `/work-done` · 2026-10-20 |

## Plan

- [x] 1. 🤖 เทียบ ERD ใน `specs/system/data-model.md` กับ foreign key ทุกตัวใน `supabase/migrations/0001_init.sql` แล้วจดส่วนที่ขาดหรือผิด
- [x] 2. 🤖 วาด ERD ใหม่ แยกเป็น 3 รูปตามกลุ่ม (Tenancy + User · Content + Scope · Tutoring + Progress + Logs) ใส่ PK/FK และ column สำคัญ · ไม่ลากเส้น `tenant_id` ไปหา `tenants` ทุกตาราง แต่เขียนเป็นกฎไว้แทน
- [x] 3. 🙋 Junior เปิดไฟล์บน GitHub (branch `docs/erd-d3` → `specs/system/data-model.md`) แล้วดูว่า diagram ทั้ง 3 รูปแสดงผลได้และอ่านรู้เรื่อง
- [x] 4. 🤖 อ่าน `poc/P3` แล้วจดสิ่งที่อาจต้องแก้ใน schema ลงหัวข้อ "สิ่งที่ยังรอผล PoC" (ยังไม่เขียน migration จนกว่า P3 จะมีผล)
- [x] 5. 🤖 `/work-check` แล้ว `/work-done`

## Definition of done

- ERD มีครบทุกตาราง (27 ตารางใน `public` + `auth.users` = 28) และทุก foreign key ใน `0001_init.sql`
- ทั้ง 3 diagram แสดงผลบน GitHub ได้
- สิ่งที่ต้องแก้ใน schema หลัง P3 มีจดไว้ชัดเจน · ข้อใน checklist ยังไม่ติ๊กจนกว่าจะแก้ schema ตามผล P3

## Decisions

- 2026-10-20 · ขั้น 5: merge `origin/main` เข้า branch (ไม่มี conflict) · `/work-check` ผ่าน เปลี่ยนแค่ไฟล์ `.md` จึงไม่มี test ให้รัน
- 2026-10-20 · ขั้น 3: Junior เปิดดูบน GitHub แล้ว diagram ทั้ง 3 รูปแสดงผลได้
- 2026-10-20 · ขั้น 4: จดสิ่งที่อาจต้องแก้ใน schema จาก P3a ได้ 5 ข้อ (ช่วงหน้าของหัวข้อ, คะแนนข้อสอบ, เหตุผลที่ map ไม่ได้, การตัดหัวข้อตาม note, คุณภาพข้อความ) · ยังไม่เขียน migration เพราะ P3a รันไม่ครบและ P3b ยังไม่เริ่ม
- 2026-10-20 · ใน ERD ไม่ลากเส้น `tenant_id` (รูป 1 ลากให้ดู 2 เส้นเป็นตัวอย่าง) · ถ้าลากครบ 26 เส้น รูปจะอ่านไม่ออก จึงเขียนเป็นกฎไว้ในหัวข้อ "วิธีอ่าน" แทน
- 2026-10-20 · เพิ่มหัวข้อ "สิ่งที่ยังไม่ชัด" เรื่อง `problems.source_ref` ที่ไม่มี FK · spec ยังไม่บอกว่าชี้ไปตารางไหน จึงจดไว้ ไม่เดาเอง
- 2026-10-19 · แก้ ERD ก่อน ยังไม่แก้ schema · ผล P3 ยังไม่ออก (Jam รันต่อ 20 ต.ค.) ส่วน ERD ทำจาก schema ปัจจุบันได้เลย

## ผลเทียบ ERD กับ `0001_init.sql` (ขั้น 1 · 2026-10-20)

`0001_init.sql` มี 27 ตารางใน `public` · มี FK ไป `tenants` 26 ตัว (ทุกตารางยกเว้น `tenants` เอง) และ FK อื่นอีก 45 ตัว · ERD เดิมมี 24 ตัวจาก 45 · **ขาดไป 21 ตัว**

ตารางที่ไม่มีใน ERD: `user_stats`

FK ที่ขาด:

| ตาราง | column → ตาราง |
|---|---|
| `org_units` | `parent_id` → `org_units` (ชี้หาตัวเอง) |
| `memberships` | `org_unit_id` → `org_units` |
| `exam_preps` | `active_scope_version_id` → `scope_versions` (เพิ่มทีหลังด้วย `alter table` · วงกลับไปหา `exam_preps`) |
| `past_exam_questions` | `topic_id` → `topics`, `skill_id` → `topic_skills` |
| `scope_changes` | `topic_id` → `topics` |
| `tutor_sessions` | `user_id` → users, `scope_version_id` → `scope_versions` (ไม่มี `on delete`), `current_topic_id` → `topics` |
| `problems` | `topic_id` → `topics`, `skill_id` → `topic_skills` |
| `attempts` | `user_id` → users, `topic_id` → `topics`, `skill_id` → `topic_skills` |
| `topic_progress` | `user_id` → users, `exam_prep_id` → `exam_preps` |
| `user_stats` | `user_id` → users (PK · 1:1) |
| `buddy_events` | `topic_id` → `topics`, `message_id` → `messages` |
| `ai_calls` | `user_id` → users, `session_id` → `tutor_sessions` |

สิ่งที่ผิดหรือทำให้เข้าใจผิด:

- `tenants` ลากเส้นไปแค่ 3 ตาราง (`memberships`, `org_units`, `ai_calls`) ทั้งที่มี 26 ตาราง · ทำให้ดูเหมือน 3 ตารางนี้พิเศษ · แผนขั้น 2 คือเลิกลากเส้น `tenant_id` แล้วเขียนเป็นกฎแทน
- `users ||--|| profiles` ควรเป็น `||--o|` (`profiles.user_id` เป็น PK จึงมีได้ไม่เกิน 1 แถว แต่ DB ไม่ได้บังคับว่าต้องมี · trigger `handle_new_user` เป็นคนสร้าง)
- `tutor_profiles`, `buddy_profiles` เป็น `o{` ถูกแล้ว (ไม่มี unique บน `user_id`)
- ERD ไม่มีชื่อ column เลย · อ่านไม่ออกว่าเส้นไหนคือ FK column ไหน (เช่น `topics` → `tutor_sessions` มีแค่ `current_topic_id`)
- หัวข้อ "ERD (ตารางหลัก)" แต่จริงๆ มีเกือบทุกตาราง · ขั้น 2 จะเปลี่ยนเป็นครบทุกตาราง

## Next step

พิมพ์ `/work-done` เพื่อเปลี่ยน PR #30 จาก draft เป็น ready for review · ไม่ติ๊กข้อ D3 ใน checklist จนกว่าจะแก้ schema ตามผล P3 (ดูตาราง 5 ข้อใน `data-model.md` › "สิ่งที่อาจต้องแก้ใน schema จาก P3a")

## Waiting on

ไม่มี

## Notes for next time

- `data-model.md` อยู่ใน `specs/` แต่ D3 เป็นงานของ Junior (`roles.md`) · แก้แค่ภาพและคำอธิบาย ไม่เปลี่ยน behavior
