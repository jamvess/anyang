# ซ้อมเส้นวิดีโอบนเครื่อง May (go/no-go ฉาก 3)

| | |
|---|---|
| Owner | May |
| Branch | `chore/video-rehearsal` |
| Checklist item | เตรียมลำดับหน้าจอสำหรับ demo รวม (ส่วนวิดีโอ: ซ้อมเส้นจริงบนเครื่อง May · go/no-go ฉาก 3 ภายใน ศ. 20 พ.ย. 18:00 · `docs/design/demo-video.md`) |
| Status | in progress · 2026-11-17 |

## Plan

- [ ] 1. 🙋 เตรียม: `SUPABASE_SERVICE_ROLE_KEY` ของ `anyang-dev` ใน `.env` ที่ root (setup.md A5) · ไฟล์ชีท MTH10101 จาก Jam · ใช้บัญชีทดสอบที่สมัครไว้แล้ว (`may.test1…`) ไม่ต้องขอ Junior เปิดรับสมัคร (ฉาก 1 ลองแล้วใน #144)
- [ ] 2. 🙋 เปิด API (`fastapi run` · AI จริง · `AUTH_REQUIRED=true`) + เว็บ · ซ้อมฉาก 2–6 ครั้งเดียว จับเวลาแต่ละฉาก · จดสิ่งที่พังหรือแปลก
- [ ] 3. 🤖 จดผลใน `demo-video.md`: go/no-go ฉาก 3 · เวลาจริงเทียบแผน · ปัญหา + เจ้าของ
- [ ] 4. 🤖 `/work-done`

## Definition of done

- ซ้อมฉาก 2–6 บนเครื่อง May ครบ 1 รอบ · มีเวลาจริงต่อฉาก · ตัดสิน go/no-go ฉาก 3 แล้ว · ผลอยู่ใน `demo-video.md`

## Decisions

- 2026-11-17 · ใช้บัญชีทดสอบเดิม (ไม่ใช่อีเมลของวิดีโอ · demo-video.md "ก่อนอัด")

## Next step

ขั้น 1: May ใส่ key + รอไฟล์จาก Jam

## Waiting on

- Jam: ไฟล์ชีท MTH10101 (ชุดเดียวกับ P3)

## Notes for next time

- `fastapi run` ไม่ใช่ `dev` (งานอ่านไฟล์เบื้องหลังหายเมื่อ reload)
