# PoC P4-lite · TTFT และต้นทุนของห้องติวผ่าน SSE

spec: `specs/poc/README.md` P4-lite · เป้า NFR-P1: TTFT p95 < 2 วินาที (`config/ai.yaml` → `targets.ttft_p95_seconds`) · report: `specs/poc/reports/P4-lite.md`

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

## ส่วนแรก · AI จำลองบน staging (May · จากเครื่องในไทย → Cloud Run `asia-southeast1`)

| | 28 ต.ค. · stub (`staging-fake`) | 31 ต.ค. · หลัง #93 ผ่าน gateway (`staging-fake-gateway`) |
|---|---|---|
| ข้อความ | 50 · ล้ม 0 | 50 · ล้ม 0 |
| เปิด session | 0.13 s | 0.27 s |
| ข้อความแรก | 0.11 s | 0.14 s |
| TTFT p50 / p95 (49 ข้อความ) | **0.12 s / 0.15 s** | **0.12 s / 0.15 s** |
| TTFT ต่ำสุด / สูงสุด | 0.10 s / 0.15 s | 0.10 s / 0.16 s |

- รอบ 31 ต.ค. response ไม่มี header `X-Stub` แล้ว แปลว่า staging รันโค้ดของ #93 (`tutor_reply` ผ่าน `ai.call` กับ provider `fake`) · overhead ของ gateway กับ provider จำลองแทบไม่เพิ่ม
- **Cold start: 6.06 s** (31 ต.ค. · staging ไม่มีคนเรียก 3 วัน · `curl` ไป `/health` ครั้งแรก รวม TLS) · วัดด้วย `/health` ไม่ใช่สคริปต์ เพราะ request นี้ปลุก instance ก่อนสคริปต์จะรัน · cold start จึงเป็นเวลาที่ผู้ใช้คนแรกหลังว่างนานรอเพิ่ม ไม่ใช่ TTFT ปกติ · ทางแก้ที่มีอยู่แล้วคือ `--min-instances=1` ก่อน demo (`infra/README.md`)

**ในเบราว์เซอร์** (May เปิด demo link บน Vercel ใน Edge DevTools → Network · 28 ต.ค.): ส่ง 1 ข้อความเห็น 2 request ไป `api-staging` คือ **preflight 165 ms** (CORS `OPTIONS` เพราะคนละ origin และส่ง `Content-Type: application/json`) แล้วจึง **fetch 50 ms** · preflight ถูก cache ตาม `max_age` ของ `CORSMiddleware` (ค่าเริ่มต้นของ Starlette 600 s · `apps/api/app/cors.py` ไม่ได้ตั้ง) จึงจ่ายเฉพาะข้อความแรก หรือหลังเว้นนานเกิน 10 นาที · ข้อความแรกในเบราว์เซอร์จึงช้ากว่าที่สคริปต์วัดประมาณ 0.17 s

**อ่านผล:** overhead ของ Cloud Run + SSE + เน็ตจากไทยไปสิงคโปร์อยู่ที่ประมาณ 0.15 s ที่ p95 · เหลือเวลาให้ LLM ประมาณ 1.85 s ภายในเป้า 2 s · ยังตอบไม่ได้ว่าผ่าน NFR-P1 จนกว่าจะวัดกับ Gemini จริง

## ข้อจำกัด

- **ไม่มี LLM จริง:** รอบ 28 ต.ค. เป็น stub ที่ส่ง `app/stubs/tutor_reply.sse` ทั้งก้อน · รอบ 31 ต.ค. ผ่าน `ai.call` แต่ provider เป็น `fake` · TTFT ≈ total ทั้งสองรอบ · ตัวเลขนี้คือ overhead ของ infra + gateway เท่านั้น
- **cold start วัดครั้งเดียว** ด้วย `curl /health` (ไม่ใช่ SSE) · ไม่ได้วัดซ้ำหลายครั้ง
- วัดจากเครื่องเดียว เน็ตบ้านเดียว · ส่งทีละข้อความ ไม่ได้วัดตอนหลายคนใช้พร้อมกัน
- สคริปต์วัดที่ client (Python `httpx`) ซึ่งไม่มี CORS preflight · ในเบราว์เซอร์ข้อความแรกมี preflight เพิ่ม 1 รอบ (ดู "ในเบราว์เซอร์" ด้านบน · วัดครั้งเดียวจาก DevTools)

## ส่วนที่สอง · Gemini จริงบน Vertex (1 พ.ย. · Jam ช่วง solo)

staging ยังเปิด live ไม่ได้ (`infra/README.md` ⚠️ · `AUTH_REQUIRED=false`) จึงรัน API ในเครื่อง Jam ด้วย Gemini จริง · ต้องมี ADC + `GOOGLE_CLOUD_PROJECT` (`docs/team/setup.md` A5) · ใช้ trial credit

```bash
cd apps/api
# terminal 1: API ด้วย Gemini จริง · stderr คือ log JSON (บรรทัด app.ai.calls ทุก AI call)
AI_PROVIDER=live AUTH_REQUIRED=false uv run fastapi run app/main.py --port 8000 2> api.log
# terminal 2
uv run python ../../poc/P4-lite/ttft.py --base http://127.0.0.1:8000 --n 50 --label <label>
uv run python ../../poc/P4-lite/cost.py api.log --label <label>              # ต้นทุนจาก log
uv run python ../../poc/P4-lite/ask_samples.py http://127.0.0.1:8000 a.json  # คำตอบ 3 ข้อไว้อ่าน
```

ลองค่าอื่นของ config โดยไม่แก้ `config/`: copy โฟลเดอร์ `config/` ไปที่อื่น แก้ `ai.yaml` ใน copy แล้วรัน API ด้วย `CONFIG_DIR=<copy>`

| | `local-vertex-low` (`ai.yaml` 1.7 · `thinking: low`) | `local-vertex-minimal` (`thinking: minimal` · ใช้ใน 1.8) |
|---|---|---|
| ข้อความ | 50 · ล้ม 0 | 50 · ล้ม 0 |
| ข้อความแรก (สร้าง client + ADC) | 8.67 s | 7.43 s |
| **TTFT p50 / p95** (49) | 2.65 s / **3.87 s** | 0.86 s / **1.20 s** |
| TTFT ต่ำสุด / สูงสุด | 1.34 / 4.37 s | 0.46 / 1.44 s |
| total p95 | 4.22 s | 2.01 s |
| token in / out เฉลี่ย (out รวม thinking) | 311 / 435 (max 639) | 311 / 78 (max 116) |
| **บาท/ข้อความ** | 0.145 | **0.039** |
| บาท/session (สมมติ 45 ข้อความ) | 6.51 | **1.73** |

- เครื่อง Jam ในไทย → Vertex `global` · `gemini-3.5-flash` · prompt `tutor_reply/v1` · ข้อความ `P4-lite ttft N` (แบบเดียวกับส่วนแรก)
- ราคา (list price · ประมาณการ): input $1.50 / output $9.00 ต่อ 1M token · 33 บาท/USD · ที่มาอยู่ใน `cost.py` · output ยังไม่เห็นในตารางหลักของหน้า Vertex pricing → เทียบกับ Cloud Billing (SKU) อีกที
- **คุณภาพคำตอบ** (`results/quality-low-vs-minimal.json` · คำถามจริง 3 ข้อ · Jam อ่าน): minimal ถูกทั้ง 3 ข้อ สอนโดยไม่เฉลย LaTeX ถูก · low ข้อ lim sin x/x ใช้ L'Hôpital (วนเหตุผล) และเฉลยเลย · 3 ข้อน้อยเกินจะบอกว่าดีกว่า บอกได้แค่ไม่เห็นว่าแย่ลง
- **TTFT บน staging โดยประมาณ** = p95 ในเครื่อง + overhead ของ Cloud Run จากส่วนแรก (~0.15 s) ≈ 1.35 s (minimal) · ยังไม่ได้วัดจริงบน staging

## ยังต้องทำต่อ

- วัดซ้ำบน staging ด้วย `--label staging-gemini` เมื่อเปิด live ได้ (หลังหน้าเว็บส่ง token + `AUTH_REQUIRED=true` · `infra/README.md`)
- เทียบต้นทุนกับ Cloud Billing report

## Test

```bash
cd apps/api && uv run pytest ../../poc/P4-lite -q
```

ทดสอบเฉพาะส่วนที่ไม่ใช้เน็ต: หา event ใน SSE, percentile แบบ nearest-rank, อ่าน log และคิดต้นทุน (`test_cost.py`)
