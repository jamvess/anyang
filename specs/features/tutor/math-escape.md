# Feature: ห้องติว · `\$` แสดงเป็นเครื่องหมาย $ (TM-08)

| | |
|---|---|
| Area | tutor |
| Requirements | TM-08 |
| Owner | May |
| Reviewer | Junior |
| Status | approved by May 2026-10-21 (owner) · รอ Junior review ใน PR |
| Related system spec | api.md v1.3 Conventions "สมการในข้อความ" · `chat-room-ui.md` AC-7 ถึง AC-10 · `chat-streaming.md` §2 (ซ่อน `$` ที่ยังไม่ปิด), AC-9 ถึง AC-11b |

## 1. Context

api.md v1.3 (May ตัดสิน 2026-10-21 · PR #36) กำหนดว่าใน `messages.content` และ `token.text` สมการเขียนเป็น `$…$` และ `$$…$$` ส่วนเครื่องหมาย $ ที่ไม่ใช่สมการเขียนเป็น `\$` · ตอนนี้ `components/chat/MessageText.tsx` ยังไม่รู้จัก `\$` จึงแสดง backslash ออกมา และ `$` ตัวนั้นยังถูกนับเป็นตัวเปิดสมการ เช่น "ราคา \$5 และ \$10" กลายเป็นสมการ `5 และ \` · feature นี้ทำให้หน้าเว็บทำตาม contract

## 2. Behavior

- **นอกสมการ:** `\$` แสดงเป็น "$" (ตัด backslash ทิ้ง) และไม่นับเป็นตัวเปิดหรือปิดสมการ
- **ในสมการ:** `\$` ไม่ปิดสมการ และส่งต่อให้ KaTeX ตามเดิม (KaTeX แสดง `\$` เป็นเครื่องหมาย $ อยู่แล้ว) เช่น `$\$5 + x$` เป็นสมการเดียว
- **ระหว่าง stream** (chat-streaming.md §2): `\$` ไม่ใช่ `$` ที่ยังไม่ปิด จึงไม่ถูกซ่อน · ถ้า stream ตัดกลางระหว่าง `\` กับ `$` (token จบด้วย `\`) ให้ซ่อน `\` ตัวท้ายไว้ก่อนจนกว่า token ถัดไปจะมา เพื่อไม่ให้ backslash โผล่แล้วหายไป · หลัง stream จบแสดงตามกฎข้างบน
- **`$` ที่ไม่มีคู่** และไม่มี backslash ยังเป็นไปตามกฎเดิม: ระหว่าง stream ซ่อน หลังจบแสดงเป็นตัวอักษร (chat-streaming.md AC-11b)
- **backslash อื่น** นอกสมการ (เช่น `\n` ที่เป็นตัวอักษร หรือ `\frac` ที่อยู่นอก `$`) ไม่แตะ แสดงตามเดิม
- **นับ backslash ที่ติดกันหน้า `$`** (May ตัดสิน 2026-10-21): เลขคี่ (`\$`, `\\\$`) = เครื่องหมาย $ · เลขคู่ (`\\$`) = `$` จริงที่เปิดหรือปิดสมการ (เหมือน LaTeX ที่ `\\` คือขึ้นบรรทัดใหม่)

## 3. Inputs and outputs

| | Type / schema | ตัวอย่าง |
|---|---|---|
| Input | `content: string` (จาก `Message.content` หรือ token ที่ต่อกันแล้ว) · `streaming: boolean` | `"ราคา \$5 และ \$10"` |
| Output | ข้อความที่ render: text ธรรมดา + KaTeX | "ราคา $5 และ $10" (ไม่มี KaTeX) |

## 4. Acceptance criteria

- **AC-1 (TM08)** Given content `"ราคา \$5 และ \$10"` When render Then ข้อความคือ "ราคา $5 และ $10" และไม่มี KaTeX
- **AC-2 (TM08)** Given content `"จ่าย \$5 แล้วหา $x^2$"` When render Then มี KaTeX inline 1 ชิ้น (`x^2`) และข้อความ "จ่าย $5 แล้วหา" เป็น text
- **AC-3 (TM08)** Given content `"$\$5 + x$"` When render Then มี KaTeX inline 1 ชิ้น ที่ได้ source `\$5 + x` และไม่มีตัวอักษร `\` ในส่วน text
- **AC-4 (TM08)** Given content `"$$\$a$$"` When render Then มี KaTeX แบบ block 1 ชิ้น
- **AC-5 (TM08)** Given content `"ราคา \$5"` และ `streaming = true` When render Then เห็น "ราคา $5" (ไม่ถูกซ่อน)
- **AC-6 (TM08)** Given content `"ราคา \"` และ `streaming = true` When render Then เห็น "ราคา" และไม่มีตัวอักษร `\` · Given content เดียวกันและ `streaming = false` Then เห็น "ราคา \" (backslash ตัวท้ายแสดงตามเดิมเมื่อจบแล้ว)
- **AC-7 (TM08)** Given content `"\$5 แล้ว $x"` และ `streaming = true` When render Then เห็น "$5 แล้ว" และไม่เห็น `x` (`$` ที่ยังไม่ปิดยังถูกซ่อนตามเดิม)
- **AC-8 (TM08)** Given content `"เขียนว่า \frac ได้"` (ไม่มี `$`) When render Then เห็น "เขียนว่า \frac ได้" ตามเดิม
- **AC-10 (TM08)** Given content `"$a \\$"` (backslash 2 ตัวก่อน `$` ตัวท้าย) When render Then มี KaTeX inline 1 ชิ้น ที่ได้ source `a \\`
- **AC-11 (TM08)** Given content `"ราคา \\\$5"` (backslash 3 ตัว) When render Then ไม่มี KaTeX และ `$` ตัวนั้นไม่เปิดสมการ
- **AC-9 (TM08)** test เดิมของ MessageText (chat-room-ui.md AC-7 ถึง AC-10) และ ChatRoomStream (chat-streaming.md AC-9 ถึง AC-11b) ยังผ่านโดยไม่แก้

**AC-boundary:** ไม่มี threshold

**AC-tenant (SA-06):** ไม่เกี่ยว · แค่การแสดงผลในหน้าเว็บ ไม่อ่านหรือเขียน database

## 5. Data changes

ไม่มี

## 6. API / SSE changes

ไม่มี · ทำตาม api.md v1.3 Conventions ที่มีอยู่แล้ว

## 7. AI calls

ไม่มี (prompt `tutor_reply` ของ Jam ต้องเขียน `\$` ตาม api.md · อยู่นอก feature นี้)

## 8. Test plan

| Test | ระดับ | ครอบคลุม AC |
|---|---|---|
| `tests/chat/MessageText.test.tsx` (เพิ่ม test ใน describe ใหม่) | unit | AC-1 ถึง AC-8, AC-10, AC-11 |
| test เดิมทั้งหมด | — | AC-9 |

## 9. Out of scope

- เปลี่ยนตัวคั่นสมการเป็นแบบอื่น (`\(…\)`) · May เลือก `$` แล้ว
- prompt ของ AI ที่สร้าง `\$`
- ช่องพิมพ์ของ user (Composer) · ข้อความที่ user พิมพ์ส่งไปตามที่พิมพ์ · bubble ของ user ใช้ MessageText ตัวเดียวกันจึงได้กฎเดียวกัน

## 10. Open questions

ตัดสินแล้ว (May · 2026-10-21)

1. `\\$`: นับ backslash ที่ติดกัน เลขคี่ = เครื่องหมาย $ · เลขคู่ = `$` จริง (AC-10, AC-11)

ไม่มีคำถามเปิดที่เหลือ

## 11. Spec changes needed

ไม่มี · api.md v1.3 กำหนดไว้แล้ว
