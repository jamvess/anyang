# เตรียมของช่วง live ของ demo รวม (รูปลายมือข้อ 2 + ซ้อมจับเวลา)

| | |
|---|---|
| Owner | May |
| Branch | `chore/demo-prep-may` |
| Checklist item | เตรียมลำดับหน้าจอสำหรับ demo รวม (ส่วนเตรียมของช่วง 3 · ไม่ติ๊กจนทีมตกลงลำดับ) |
| Status | in progress · 2026-11-19 |

## Plan

อ้างอิง `docs/design/demo-flow.md` ช่วง 3 + ตาราง "สิ่งที่ต้องพร้อม" · ห้องเดโม่ `specs/features/tutor/demo-room.md` §3 (โจทย์ข้อ 2 = `demo-2` ลิมิต เฉลย `4`) และ §12 (วิธีเปิด) · รูปลายมือ**ไม่ขึ้น git** (เก็บในเครื่อง / Drive)

- [x] 1. 🙋 May เช็คว่าได้ role Vertex AI User จาก Jam หรือยัง · ถ้าได้: `gcloud auth application-default login` บนเครื่องตัวเอง · 2026-11-17 Jam ให้ role แล้ว · ติดตั้ง Google Cloud CLI (winget) + ADC login ผ่าน · `set-quota-project` ไม่ผ่าน (ไม่มี `serviceusage.services.use`) · ข้ามไปก่อน เพราะ gateway ส่ง project เองทุกคำขอ (`gemini.py` `vertex()`) · ถ้าขั้น 3 เจอ 403 → ขอ Jam เพิ่ม role Service Usage Consumer
- [x] 2. 🙋 May เขียนวิธีทำข้อ 2 ที่ผิด 1 บรรทัด (Claude ให้ตัวอย่าง) แล้วถ่ายรูปหรือแคปจาก tablet · เก็บนอก repo · 2026-11-17 เสร็จ (`Downloads/IMG_1011.webp` บนเครื่อง May · 29 KB ถูกบีบอัด ถ้าอ่านผิดให้ใช้ต้นฉบับ JPG)
- [ ] 3. 🙋 May เปิดห้องเดโม่ (AI จริงถ้ามีสิทธิ์ · ไม่งั้น AI จำลอง) แล้วไล่ขั้น 1–5 ของช่วง 3 ครั้งหนึ่ง พร้อมจับเวลาแต่ละขั้น · จดว่าการ์ดยืนยันอ่านลายมือถูกไหม และผลตรวจชี้บรรทัดที่ผิดถูกไหม · 2026-11-17 รอบ 1 ด้วย AI จริง (Vertex) ครบ 5 ขั้น May บอก "ดีหมด" (อ่านลายมือถูก ชี้บรรทัดผิดถูก) · **ยังไม่ได้จับเวลา**
- [ ] 4. 🤖 จดผลลง `demo-flow.md`: สถานะในตาราง "สิ่งที่ต้องพร้อม", เวลาที่ซ้อมได้เทียบ 5:30, ปัญหาที่เจอ
- [ ] 5. 🙋 May ตัดสิน 2 เรื่องที่เปิดไว้ (warm-up · รูปถูกสำรอง) จากที่ซ้อมจริง (Claude ถามเป็นตัวเลือก)

## Definition of done

- มีรูปข้อ 2 ที่ทดสอบผ่านห้องเดโม่แล้ว (ด้วย AI จริง ถ้ายังไม่มีสิทธิ์ให้จดว่ายังต้องทดสอบซ้ำ)
- ซ้อมช่วง 3 ครบ 1 รอบพร้อมเวลา และ `demo-flow.md` อัปเดตตามจริง

## Decisions

- 2026-11-12 · ใช้ type `chore` · งานเตรียม demo แก้แค่เอกสาร

## Next step

รีสตาร์ต API แล้วซ้อมขั้น 3 อีกรอบพร้อมจับเวลา (ทำพร้อมช่วงอัดวิดีโอ 21–22 พ.ย. ได้) → ขั้น 4 จดลง `demo-flow.md` · branch นี้ตามหลัง main มาก merge main ก่อนทำต่อ

## Waiting on

- ไม่มี (Jam ให้ role Vertex AI User แล้ว 2026-11-17)

## Notes for next time

- เปิดห้องเดโม่ AI จริงบน PowerShell: `$env:APP_ENV="local"; $env:AI_PROVIDER="live"; $env:AUTH_REQUIRED="false"; $env:GOOGLE_CLOUD_PROJECT="anyang-513006"; $env:GOOGLE_CLOUD_LOCATION="global"` แล้ว `uv run fastapi dev app/main.py`
- ห้องเดโม่จำโจทย์ปัจจุบันและความคืบหน้าข้าม session จนกว่าจะรีสตาร์ต API (`demo-room.md` §2 J) · ซ้อมเสร็จต้องรีสตาร์ต API ก่อนซ้อมรอบใหม่
