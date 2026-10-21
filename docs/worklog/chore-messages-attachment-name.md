# `messages.attachment_name` + สถานะ schema จาก P3a

| | |
|---|---|
| Owner | Junior |
| Branch | `chore/messages-attachment-name` |
| Checklist item | ปรับ `schema.sql` ตามที่เจอระหว่าง P3 + วาด ERD (D3) |
| Status | in progress · 2026-10-21 |

## Plan

- [x] 1. 🤖 `test_room_api_contract.py`: เพิ่ม `attachment_name` ในชุด field ของ `Message` (spec-driven จาก api.md v1.3 · Junior ดู diff แล้ว ok) → red 5 ตัว
- [x] 2. 🤖 `Message.attachment_name: str | None` ใน `app/models/room.py` + stub `app/stubs/room.json` → green
- [x] 3. 🤖 `guards.max_attachment_name_chars: 255` ใน `config/ai.yaml` + `GuardsConfig` (Junior บอกกลุ่มเรื่องไฟล์กลางเอง)
- [x] 4. 🤖 `supabase/migrations/0002_messages_attachment_name.sql` (ไม่แก้ 0001) · display-only ห้ามใช้ใน path ของ Storage
- [x] 5. 🤖 `data-model.md`: ERD รูป 3 เพิ่ม `attachment_path`, `attachment_name` · กฎการตัดชื่อ · สถานะ 5 ข้อของ P3a (รอผลทั้งหมด)
- [x] 6. 🤖 ตรวจ migration ผ่าน CI แทนการรัน Docker ในเครื่อง (Junior เลือก): job `api-integration` บน PR #43 รัน `supabase start` ซึ่ง apply migration ทุกไฟล์ ต้องเขียว · pytest + ruff ในเครื่องผ่านแล้ว · ไม่ `db push`
  - 2026-10-21 · run 39537119072 · log มี "Applying migration 0002_messages_attachment_name.sql..." · integration 3 passed · `api`, `web` เขียว · มี `toomanyrequests` ตอน pull image ของ Supabase แต่ retry แล้วผ่าน (ถ้า CI แดงเพราะเรื่องนี้ให้กด re-run)

## Definition of done

- migration ใหม่ apply บน local ได้ · ERD ตรงกับ schema · `/openapi.json` มี `Message.attachment_name` ตรงกับ api.md v1.3
- 5 ข้อ P3a มีสถานะพร้อมเหตุผลใน `data-model.md`
- test ผ่านทั้งหมด

## Decisions

- 2026-10-21 · ผล P3 ยังยืนยัน schema ไม่ได้สักข้อ: A6/A7 ไม่เคยรันผ่าน (503 + โควตาหมด) · ไม่มี report P3a ใน #37 · #39 (embedding) ไม่เกี่ยวกับ 5 ข้อ · migration จึงมีแค่ `attachment_name`
- 2026-10-21 · (Junior) ความยาวสูงสุดอยู่ที่ `config/ai.yaml` → `guards.max_attachment_name_chars: 255` ตรวจที่ API ไม่ใส่ `CHECK` ใน SQL (migration อ่าน config ไม่ได้)
- 2026-10-21 · (Junior) ชื่อยาวเกิน → ตัดให้สั้น **นับเป็น grapheme cluster ไม่ใช่ code point** (สระ/วรรณยุกต์ไทยต้องไม่ถูกตัดแยกจากพยัญชนะ) และเก็บนามสกุลไฟล์ไว้ · ไม่ตอบ 422
- 2026-10-21 · (Junior) ข้อความใน `api.md` เรื่องการตัดชื่อไปรวมกับ PR api.md ของข้อ 5 (หลัง May เลือก A/B) ไม่แยก PR
- 2026-10-21 · (Junior) PR นี้แก้ `Message` model + stub ด้วย เพราะ api.md v1.3 บน main มี `attachment_name` แล้ว stub จึงไม่ตรง spec และ `gen:api` ของ May จะขาด field · guard ตัดชื่อจริงรอ endpoint uploads ใน S3
- 2026-10-21 · stub `m8` เปลี่ยน `attachment_path` จาก `sessions/s1/วิธีทำ.jpg` เป็น path แบบ uuid + `attachment_name: "วิธีทำ.jpg"` · เพราะ v1.3 บอกว่า path เป็น uuid · ค่า `image_path` ใน request body ของ test API ไม่ต้องแก้ (เป็นแค่ string) · ฝั่ง web (`MessageList.test.tsx:109`, fixture `session-s15.json`) ยังเอาชื่อจากท้าย path ซึ่งเป็นงานของ May
- 2026-10-21 · (Junior) ค่า 255 ติดป้าย `[B]` เป็นเพดานการแสดงผลของชื่อไฟล์ที่ user เห็น นับเป็น grapheme cluster เก็บนามสกุลไว้ และไม่เคยใช้ใน path ของ Storage · **ไม่ใช่**ขีดจำกัดของระบบไฟล์ (ext4 นับ 255 byte ส่วน NTFS นับ 255 หน่วย UTF-16 แต่ตัวอักษรไทยใช้ 3 byte ใน UTF-8 และ `attachment_name` ไม่เคยลงระบบไฟล์)

## Next step

ครบทุกขั้นแล้ว · รัน `/work-done` เพื่อเปลี่ยน PR #43 เป็น ready for review · หลัง merge: Junior `npx supabase db push` ขึ้น `anyang-dev` และ May เปลี่ยนฝั่ง web ไปใช้ `attachment_name` (อยู่ใน PR description)

## Waiting on

ไม่มี

## Notes for next time

- `test_room_api_contract.py` เป็น test ที่ review แล้ว แก้ได้เฉพาะเมื่อ spec เปลี่ยนและ Junior เห็น diff ก่อน
