# PoC P4-lite · TTFT ของห้องติวผ่าน SSE (ส่วนแรก · AI จำลอง)

spec: `specs/poc/README.md` P4-lite · เป้า NFR-P1: TTFT p95 < 2 วินาที (`config/ai.yaml` → `targets.ttft_p95_seconds`) · worklog: `docs/worklog/poc-P4-lite-ttft.md`

## รัน

ไม่ต้องใช้ secret · `api-staging` ตอนนี้ใช้ `AI_PROVIDER=fake` จึงไม่เสีย credit (`infra/README.md`)

```bash
cd apps/api
uv run python ../../poc/P4-lite/ttft.py \
    --base https://api-staging-659706857266.asia-southeast1.run.app \
    --n 50 --label staging-fake
```

- เปิด session 1 ครั้ง (`POST /exam-preps/{id}/sessions`) แล้วส่ง `--n` ข้อความทีละข้อความ (`POST /sessions/{id}/messages`) เว้น `--pause` วินาที
- **TTFT** = ส่ง request → event `token` แรก · **total** = ส่ง request → `done`
- `session_open` และข้อความแรก (`first`) แยกไว้ เพราะ Cloud Run อาจต้องเปิด instance ใหม่ (cold start) · p50/p95 คิดจากข้อความที่ 2–n
- ผลอยู่ใน `results/<label>.json` (ตัวเลขและเวลาทุกข้อความ ไม่มีข้อมูลผู้ใช้)
- **เมื่อเปิด Gemini บน staging แล้ว** รันคำสั่งเดิมด้วย `--label staging-gemini` เพื่อเทียบ

## ผล (28 ต.ค. 2569 · จากเครื่องของ May ในไทย → Cloud Run `asia-southeast1`)

| | ค่า |
|---|---|
| ข้อความ | 50 · ล้ม 0 |
| เปิด session | 0.13 s |
| ข้อความแรก | 0.11 s |
| TTFT p50 / p95 (49 ข้อความ) | **0.12 s / 0.15 s** |
| TTFT ต่ำสุด / สูงสุด | 0.10 s / 0.15 s |

**ในเบราว์เซอร์** (May เปิด demo link บน Vercel ใน Edge DevTools → Network · 28 ต.ค.): ส่ง 1 ข้อความเห็น 2 request ไป `api-staging` คือ **preflight 165 ms** (CORS `OPTIONS` เพราะคนละ origin และส่ง `Content-Type: application/json`) แล้วจึง **fetch 50 ms** · preflight ถูก cache ตาม `max_age` ของ `CORSMiddleware` (ค่าเริ่มต้นของ Starlette 600 s · `apps/api/app/cors.py` ไม่ได้ตั้ง) จึงจ่ายเฉพาะข้อความแรก หรือหลังเว้นนานเกิน 10 นาที · ข้อความแรกในเบราว์เซอร์จึงช้ากว่าที่สคริปต์วัดประมาณ 0.17 s

**อ่านผล:** overhead ของ Cloud Run + SSE + เน็ตจากไทยไปสิงคโปร์อยู่ที่ประมาณ 0.15 s ที่ p95 · เหลือเวลาให้ LLM ประมาณ 1.85 s ภายในเป้า 2 s · ยังตอบไม่ได้ว่าผ่าน NFR-P1 จนกว่าจะวัดกับ Gemini จริง

## ข้อจำกัด

- **ไม่มี LLM:** stub ส่ง `app/stubs/tutor_reply.sse` ทั้งก้อนทันที ไม่ผ่าน `ai.call` · TTFT ≈ total · ตัวเลขนี้คือ overhead ของ infra อย่างเดียว
- **ไม่เจอ cold start:** instance ยังตื่นอยู่ตอนวัด (เปิด session 0.13 s) · ถ้าต้องการตัวเลข cold start ให้รันหลังไม่มีคนเรียก staging นานพอให้ Cloud Run ปิด instance (service ตั้ง `--min-instances=0` ไว้ · `infra/README.md`)
- วัดจากเครื่องเดียว เน็ตบ้านเดียว · ส่งทีละข้อความ ไม่ได้วัดตอนหลายคนใช้พร้อมกัน
- สคริปต์วัดที่ client (Python `httpx`) ซึ่งไม่มี CORS preflight · ในเบราว์เซอร์ข้อความแรกมี preflight เพิ่ม 1 รอบ (ดู "ในเบราว์เซอร์" ด้านบน · วัดครั้งเดียวจาก DevTools)

## ยังต้องทำต่อ (report P4-lite · ร่วมกับ Junior)

- TTFT p50/p95 กับ Gemini จริงบน staging (Junior ต้องเช็ค JWT ทุก endpoint ก่อนเปิด `AI_PROVIDER=live`)
- ต้นทุนต่อข้อความจาก `ai_calls` (เป้า `targets.cost_per_session_thb`)
- สลับ `AI_PROVIDER=fake` ↔ จริงด้วย config แล้ว test ผ่านโดยไม่แก้โค้ด
- เขียน report ด้วย `/poc-report P4-lite`

## Test

```bash
cd apps/api && uv run pytest ../../poc/P4-lite -q
```

ทดสอบเฉพาะส่วนที่ไม่ใช้เน็ต: หา event ใน SSE และ percentile แบบ nearest-rank
