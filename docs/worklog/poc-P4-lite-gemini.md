# PoC P4-lite: TTFT และต้นทุนกับ Gemini จริง (Vertex)

| | |
|---|---|
| Owner | Jam (item of Junior) |
| Branch | `poc/P4-lite-gemini` |
| Checklist item | วัด TTFT และต้นทุนบน staging ร่วมกับ May (P4-lite) |
| Status | in progress · 2026-11-01 |

## Plan

- [x] 1. 🤖 เช็คของที่ต้องมี: ADC ของ Vertex (ok 1 พ.ย.) · `GOOGLE_CLOUD_PROJECT=anyang-513006`, location `global` (ok) · หาราคา `gemini-3.5-flash` บน Vertex (input/output ต่อ 1M token) จากหน้า pricing ของ Google พร้อม URL และวันที่ดู
- [x] 2. 🤖 รัน API ในเครื่อง `AI_PROVIDER=live AUTH_REQUIRED=false` (override env ไม่แก้ `.env`) เก็บ log `app.ai.calls` ลงไฟล์ · ยิง `poc/P4-lite/ttft.py --base http://127.0.0.1:8000 --n 50 --label local-vertex-low` (config ปัจจุบัน `thinking: low`) · เพิ่ม `poc/P4-lite/cost.py` อ่าน log → token ต่อข้อความ + ต้นทุน (บาท) + test ส่วน pure · ใช้ credit trial ราว 50 call
- [x] 3. 🙋 Jam ดูผลแล้วตัดสิน: ถ้า TTFT p95 ≥ 2 s ลองตัวไหนต่อ (เช่น ไม่ตั้ง max เดิม, `thinking` ระดับต่ำกว่า low ถ้า model รองรับ · ต้องแก้ `Literal` ใน settings · หรือ prompt สั้นลง) · ทดลองผ่าน `CONFIG_DIR` ชี้ไป copy ของ `config/` ใน scratchpad จึงไม่แตะ `config/ai.yaml` ระหว่างทดลอง
- [x] 4. 🤖 รันรอบทดลองตามที่ Jam เลือก (ถ้ามี) · label แยก
- [ ] 5. 🙋 Jam ตัดสินค่าใน `config/ai.yaml` (ไฟล์กลาง · บอกกลุ่ม) ถ้าจะเปลี่ยน
- [ ] 6. 🤖 อัปเดต `poc/P4-lite/README.md` + ร่าง `/poc-report P4-lite` (report ของ May + Junior · Jam ร่างช่วง solo) · เกณฑ์: TTFT p95 < 2 s · สลับ provider ด้วย config · มีตัวเลขต้นทุน
- [ ] 7. 🙋 Jam review report
- [ ] 8. 🤖 `/work-done`

## Definition of done

- มี TTFT p50/p95 จาก 50 ข้อความกับ Gemini จริง (เทียบเป้า `targets.ttft_p95_seconds`) และต้นทุนต่อข้อความ/ต่อ session (เทียบ `targets.cost_per_session_thb`) พร้อมที่มาของราคา
- ผลและคำสั่งรันซ้ำอยู่ใน `poc/P4-lite/` · report `specs/poc/reports/P4-lite.md` ตอบ 3 เกณฑ์ของ spec
- checklist ข้อของ Junior (และข้อ report ของ May) มีหมายเหตุว่าทำอะไรไป

## Decisions

- 2026-11-01 · Jam หยิบช่วง solo · วัดจากเครื่อง Jam (ไทย → Vertex `global`) แทน staging เพราะ staging ยังเปิด live ไม่ได้ (`AUTH_REQUIRED=false` · `infra/README.md` ⚠️)

- 2026-11-01 · รอบทดลอง: Jam เลือกข้อ 1 (`thinking: minimal` · ตอบ "ok" ตามข้อแนะนำ) · เพิ่ม `minimal` ใน `Literal` ของ `PurposeConfig.thinking` (`app/settings.py`) · ทดลองผ่าน `CONFIG_DIR` ชี้ copy ของ `config/` ใน scratchpad

## Next step

ขั้น 5: Jam ตัดสินว่า `config/ai.yaml` `purposes.tutor_reply.thinking` เปลี่ยน `low` → `minimal` ไหม (ไฟล์กลาง · bump version 1.8 · บอกกลุ่ม) · อ่านคำตอบ 3 ข้อใน `poc/P4-lite/results/quality-low-vs-minimal.json` ประกอบ

## Waiting on

- Junior + May: report P4-lite เป็นของทั้งคู่ · Jam ร่างให้ · ตัวเลขบน staging จริงวัดซ้ำได้ด้วยคำสั่งเดิมเมื่อเปิด live

## Notes for next time

- 1 พ.ย. ผลขั้น 4 (`local-vertex-minimal` · `thinking: minimal` · 50 ข้อความ ล้ม 0): **TTFT p50 0.86 s · p95 1.20 s** · min 0.46 · max 1.44 · total p95 2.01 · ข้อความแรก 7.43 s · out เฉลี่ย 78 token (max 116) · **0.0385 บาท/ข้อความ · 1.73 บาท/session (45)** · คำตอบจริง 3 ข้อ (`results/quality-low-vs-minimal.json`): minimal ถูกต้อง สอนแบบไม่เฉลย LaTeX ถูก · low ข้อ lim sin x/x ใช้ L'Hôpital (วนเหตุผล เพราะอนุพันธ์ของ sin ได้มาจาก limit นี้) และให้คำตอบเลย

- 1 พ.ย. ผลขั้น 2 (`local-vertex-low` · `thinking: low` · `ai.yaml` 1.7 · เครื่อง Jam → Vertex global · 50 ข้อความ ล้ม 0): **TTFT p50 2.65 s · p95 3.87 s · min 1.34 · max 4.37** (เป้า 2 s → ไม่ผ่าน) · ข้อความแรก 8.67 s (สร้าง client + ADC ครั้งแรก) · token in 311 · out เฉลี่ย 435 (median 465 · max 639 · รวม thinking) · **0.145 บาท/ข้อความ** · 45 ข้อความ/session = **6.51 บาท** (เป้า 5) · log บรรทัด `app.ai.calls` ออก stderr ครบ 50 บรรทัด (logging จาก #95 ใช้ได้จริง)

- 1 พ.ย. ราคาที่ใช้ (list price · ประมาณการ): `gemini-3.5-flash` Vertex global input **$1.50** / 1M (cached $0.15) จากหน้า pricing ของ Vertex (search 1 พ.ย. · https://docs.cloud.google.com/vertex-ai/generative-ai/pricing · WebFetch เปิดหน้าไม่ได้) · output **$9.00** / 1M (รวม thinking) จากตาราง CodeMender/AlphaEvolve บนหน้า Vertex pricing เดิม · ยังไม่เห็นในตารางหลัก → ยืนยันกับ Cloud Billing report (SKU) หลังรัน · อัตรา **33 บาท/USD** (ปัดจาก 32.65–33.78 ในช่วง ก.ค.–ส.ค. 2569 · ไม่มีค่าล่าสุดที่เชื่อได้) · เป้า 5 บาท/session ≈ $0.15

- `tokens_out` ใน `ai_calls` รวม thinking token แล้ว (`gemini.py` `_usage`) · thinking คิดเงินแบบ output
- smoke 31 ต.ค. (ค่า `ai.yaml` 1.5): TTFT 3.7 s ด้วย `thinking: low` · default thinking 5.2 s
