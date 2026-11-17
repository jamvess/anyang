# ลองเส้นจริงของ demo ขั้น 3 (หน้าอัปโหลด #142 + API จริง #140)

| | |
|---|---|
| Owner | Jam (item of May) |
| Branch | `docs/demo-step3-check` |
| Checklist item | ⭐ demo ขั้น 3: หน้าอัปโหลดหลายไฟล์ + สถานะรายไฟล์ (CM-03, CM-07) |
| Status | in progress · 2026-11-17 |

## Plan

ข้อนี้ยังไม่ติ๊กเพราะตอน #142 ลองได้แค่บน stub · ตอนนี้ #140 merge แล้ว · `0008`, `0009` ขึ้น `anyang-dev` แล้ว (Junior 17 พ.ย.) · สัญญาตรงกับหน้าเว็บ (ไม่มี `X-Stub` · `PUT` ไป `upload_url` ได้เลยไม่ต้องมี token · `materials-db.md` §2 ข้อ 6, §10 ข้อ 7)

- [x] 1. 🙋 (17 พ.ย.) รีสตาร์ต API ในเครื่อง (ให้ใช้โค้ดของ #140) + `pnpm dev`
- [x] 2. 🙋 (17 พ.ย. · ผ่านในรอบที่ 4) ลองในเบราว์เซอร์ด้วยบัญชีทดสอบของ Jam: สร้าง prep → เลือก PDF ของ MTH10101 2–3 ไฟล์ → ส่ง → ประเภทที่ AI เดา → ยืนยัน → หน้ารออ่าน → หน้า scope · Claude ให้ขั้นตอนทีละคลิก
- [x] 3. 🤖 (ปัญหาทั้งหมดเป็นการตั้งค่าในเครื่อง · งานต่อจดใน Findings) ถ้าเจอปัญหา: หาสาเหตุ แล้วเสนอวิธีแก้ (แก้ใน PR นี้ถ้าเล็ก · ใหญ่แยก PR)
- [x] 4. 🤖 จดผลลง `upload-page.md` §8 · ติ๊ก checklist ของ May พร้อมบรรทัดย่อย

## Definition of done

- เส้นจริงตั้งแต่เลือกไฟล์จนถึงหน้า scope ผ่านในเบราว์เซอร์บน `anyang-dev` · หรือมีรายการปัญหาที่ต้องแก้พร้อมเจ้าของ
- ผลอยู่ใน `upload-page.md` §8 · checklist ติ๊กเมื่อผ่าน

## Decisions

- 2026-11-17 · Jam เลือกข้อ 1 ของ `/work-start Jam` · checklist เป็นของ May แต่หน้าเว็บ Jam ทำใน #142

## Next step

ทุกข้อเสร็จ · พิมพ์ `/work-done` (ติ๊ก checklist ของ May ตอนนั้น)

## Waiting on

ไม่มี

## Findings

- 17 พ.ย. รอบแรก: เลือกไฟล์ + อัปโหลดเข้า Storage + `/uploaded` ผ่าน (`200`, `202`) · AI ดูไฟล์ค้างที่ "AI กำลังดูไฟล์…" · สาเหตุ: `SUPABASE_SERVICE_ROLE_KEY` ใน `.env` ของ Jam ไม่ใช่ key ของ `anyang-dev` (`Unregistered API key` · ตัวเดียวกับที่ทำให้ integration test ในเครื่องล้ม) · ไม่ใช่บั๊กของ #140 หรือ #142
- งานต่อ (ไฟล์ของ Jam): `classify_material` อ่านแถวและตั้ง job ก่อน `try` · DB ล้มตรงนั้น → ไฟล์ค้าง `uploaded` ตลอด ไม่มี error ให้ผู้ใช้และไม่มีทางลองใหม่ (`/uploaded` ซ้ำได้ `409`, `/retry` รับแต่ `failed`)
- รอบ 2–3: `AI_PROVIDER` ใน `.env` เป็น fake (fake provider ไม่มีคำตอบตั้งต้นของ `classify_material` · งานต่อ) · ADC login ด้วย `vessapoo.sawa@gmail.com` ซึ่งไม่มีสิทธิ์ใน `anyang-513006` → `403` · แก้: ADC เป็น `jamsadog@gmail.com` + `set-quota-project anyang-513006` · รอบ 4 ผ่าน
- Next.js 16.4.3 ขึ้นคำถาม upgrade policy `security` (มี advisory · แนะนำ 16.4.6) · ยังไม่อัปเกรด · งานต่อ: PR อัปเกรดแยก (ไฟล์ของ May · บอกกลุ่ม)

## Notes for next time

- ใช้เว็บที่พอร์ต 3000 ไม่ใช่ 8000 (API)
