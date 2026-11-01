# PoC P4-lite · Chat AI ที่ stream ได้ · report

| | |
|---|---|
| Owner | May (web) + Junior (api) · ร่างและวัด Gemini โดย Jam ช่วง solo 1 พ.ย. |
| Sprint | S3 (เริ่มก่อนกำหนด 28 ต.ค.) |
| Date | 1 พ.ย. 2569 |
| Code | หน้าแชท `apps/web` (#32, #42 · May) · endpoint SSE + `ai.stream` (#93) · log `ai_calls` (#95) · วัดผล `poc/P4-lite/` (#85 May, #99 Jam) · คำสั่งรันซ้ำอยู่ใน `poc/P4-lite/README.md` ("รัน" = AI จำลองบน staging · "ส่วนที่สอง" = Gemini จริง) · ผล: `poc/P4-lite/results/` |

## 1. คำถาม

stream คำตอบผ่าน SSE บน Cloud Run เร็วพอไหม และสลับผู้ให้บริการ AI ได้ไหม

## 2. วิธีทดสอบ

- **ส่วนแรก (May · 28 + 31 ต.ค.):** `poc/P4-lite/ttft.py` เปิด session แล้วส่ง 50 ข้อความทีละข้อความไป `POST /sessions/{id}/messages` บน `api-staging` (Cloud Run `asia-southeast1`) จากเครื่องในไทย · AI จำลอง (`AI_PROVIDER=fake`) จึงวัดได้แค่ overhead ของ Cloud Run + SSE + เน็ต · ดู preflight ใน DevTools ของเบราว์เซอร์ 1 ครั้ง
- **ส่วนที่สอง (Jam · 1 พ.ย.):** สคริปต์เดิม 50 ข้อความ แต่ยิงไป API ในเครื่อง Jam ที่รันด้วย Gemini จริง (`AI_PROVIDER=live` · Vertex `global` · `gemini-3.5-flash` · prompt `tutor_reply/v1`) 2 รอบ: `thinking: low` (ค่าใน `ai.yaml` 1.7) และ `thinking: minimal` · ต้นทุนคิดจาก log `app.ai.calls` ของ gateway (`poc/P4-lite/cost.py` · token out รวม thinking) ด้วย list price · ถามคำถามคณิตจริง 3 ข้อทั้ง 2 ค่าให้ Jam อ่านคุณภาพ (`ask_samples.py`)
- **สลับ provider:** CI รัน test ทั้งหมดด้วย `AI_PROVIDER=fake` (`.github/workflows/ci.yml`) · ส่วนที่สองใช้โค้ดเดียวกันโดยเปลี่ยนแค่ env เป็น `live`
- **สิ่งที่ไม่ได้ทดสอบ:** Gemini จริง**บน staging** (ยังเปิด live ไม่ได้: หน้าเว็บยังไม่ส่ง token · `infra/README.md` ⚠️) · หลายคนใช้พร้อมกัน · ข้อความส่งรูป (ยังเป็น stub) · คุณภาพคำตอบแบบมีเกณฑ์ (มีแค่ 3 ข้อให้คนอ่าน) · ยอดเงินจริงจาก Cloud Billing · ข้อความทดสอบเป็น `P4-lite ttft N` ไม่ใช่คำถามจริง (ความยาวคำตอบอาจต่างจากใช้งานจริง)

## 3. ผล

| Metric | เกณฑ์ผ่าน | ผล | PASS / FAIL |
|---|---|---|---|
| TTFT p95 (`targets.ttft_p95_seconds`) | < 2 s | `minimal`: **1.20 s** ในเครื่อง (49 ข้อความ) + overhead Cloud Run ~0.15 s (ส่วนแรก) ≈ **1.35 s** โดยประมาณ · `low`: 3.87 s ❌ | **PASS (ประมาณการ)** ด้วย `thinking: minimal` · ต้องวัดซ้ำบน staging |
| สลับ provider ด้วย config | ไม่แก้โค้ด | CI ทุก run ใช้ `fake` · Gemini จริงด้วย env `AI_PROVIDER=live` อย่างเดียว · ค่า `minimal` เพิ่มใน `Literal` ของ settings 1 บรรทัด (เป็นค่าใหม่ของ config ไม่ใช่การสลับ provider) | **PASS** |
| มีตัวเลขต้นทุน (`targets.cost_per_session_thb` 5 บาท) | มีตัวเลข | `minimal`: **0.039 บาท/ข้อความ** → 1.73 บาท/session ถ้า 45 ข้อความ · `low`: 0.145 → 6.51 | **PASS** (มีตัวเลข · ต่ำกว่าเป้าด้วย `minimal`) |

**รายละเอียด**

| | AI จำลอง · staging (May) | Gemini · `low` | Gemini · `minimal` |
|---|---|---|---|
| TTFT p50 / p95 | 0.12 / 0.15 s | 2.65 / 3.87 s | 0.86 / 1.20 s |
| ข้อความแรก | 0.14 s | 8.67 s | 7.43 s |
| token out เฉลี่ย (รวม thinking) | — | 435 | 78 |
| คุณภาพ 3 ข้อ (Jam อ่าน) | — | ข้อ lim sin x/x ใช้ L'Hôpital (วนเหตุผล) และเฉลยเลย | ถูกทั้ง 3 ข้อ สอนโดยไม่เฉลย LaTeX ถูก |

- ข้อความแรกของ Gemini ช้า 7–9 s เพราะสร้าง client และขอ token ของ ADC ครั้งแรก · บน Cloud Run จะเกิดกับ request แรกของ instance ใหม่ ซ้อนกับ cold start (6.06 s ที่ May วัด) · ทางแก้ที่มีแล้วคือ `--min-instances=1` ตอน demo
- ในเบราว์เซอร์ข้อความแรกมี CORS preflight +0.17 s (cache 10 นาที)

## 4. การตัดสินใจ

**ผ่าน (ประมาณการ)** · ใช้ `thinking: minimal` กับ `tutor_reply` (Jam ตัดสิน 1 พ.ย. · `config/ai.yaml` 1.8 · prompt/model เป็นเรื่องที่ Jam ตัดสินตาม `roles.md`)

- `low` ไม่ผ่านทั้ง TTFT (3.87 s) และต้นทุน (6.51 บาท/session) · thinking token เป็นส่วนใหญ่ของทั้งเวลาก่อน token แรกและเงิน
- `minimal` เร็วขึ้น 3 เท่าที่ p95 และถูกลง 3.8 เท่า · คำตอบ 3 ข้อที่อ่านไม่แย่ลง
- ไม่ต้องย้าย model หรือย่อ prompt · stage machine, planner, buddy ยังอยู่เทอม 2 ตาม spec
- เป็นผลประมาณการเพราะยังไม่ได้วัด Gemini บน staging · วัดซ้ำด้วย `ttft.py --label staging-gemini` เมื่อเปิด live

## 5. สิ่งที่ต้องแก้ใน spec / config

- [x] `config/ai.yaml` → `purposes.tutor_reply.thinking`: `low` → `minimal` (1.7 → 1.8 · PR #99)
- [x] `apps/api/app/settings.py` → `PurposeConfig.thinking` รับ `minimal` (PR #99)
- [x] `specs/poc/README.md` §P4-lite: บรรทัด "ผล" (PR #99)
- [x] `specs/system/ai-orchestration.md` §3.6 แถว "TTFT และต้นทุน": ใส่ผล (PR #99)
- ไม่ต้องแก้ `config/learning.yaml`

## 6. ความเสี่ยงที่เหลือ

- **ยังไม่ได้วัดบน staging:** เส้นทางจริงคือ เบราว์เซอร์ → Cloud Run → Vertex (ใน GCP) ซึ่งน่าจะเร็วกว่าไทย → Vertex แต่ยังไม่ได้วัด · ต้องรอหน้าเว็บส่ง token + `AUTH_REQUIRED=true` + env Supabase ของ api-staging (Junior, May)
- **ต้นทุนต่อ session เป็นค่าสมมติ:** 45 ข้อความ/session (1 ข้อความต่อนาที) และนับแค่ `tutor_reply` · design เต็ม (§2.2) มี 2–4 AI call ต่อ turn (router, checker, generate) ซึ่งจะเพิ่มต้นทุน · ราคา output $9.00 ยังไม่เห็นในตารางหลักของหน้า Vertex pricing → เทียบกับ Cloud Billing
- **คุณภาพของ `minimal` วัดแค่ 3 ข้อ:** เมื่อมี eval ของ tutor behavior (§2.11 · LLM-as-judge) ควรเทียบ `minimal` กับ `low` อีกครั้ง
- **ข้อความแรกช้า 7–9 s:** ถ้าเป็นปัญหาตอน demo ให้ warm up client ตอน start (lifespan) หรือใช้ `--min-instances=1`
