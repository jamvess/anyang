# gateway รอ 429 นานขึ้น (A) · room_problems ไม่สร้างโจทย์ซ้ำเมื่อโดน 429 (B)

| | |
|---|---|
| Owner | Junior |
| Branch | `fix/gateway-429-backoff` |
| Checklist item | ทั้งทีม S4 (เพิ่ม 13 พ.ย.): "⭐ demo end to end: ต่อทุกขั้นในเครื่องเดียว พฤ. 19 พ.ย. · ซ้อม ศ. 20 · อัดวิดีโอ 21–22 · ส่ง จ. 23 พ.ย." · บั๊ก 1 จาก journey 17 พ.ย. |
| Status | in progress · 2026-11-19 |

## Plan

- [x] 1. 🤖 spec `specs/features/ai/gateway-rate-limit-backoff.md` (NFR-R1, AM-11)
- [x] 2. 🙋 Junior review spec + ตอบ §10 ข้อ 1–2 (19 พ.ย.)
- [x] 3. 🤖 `/spec-to-tests`: test แดงของ AC-1 ถึง AC-10 (`tests/unit/test_gateway_rate_limit.py` + `tests/unit/test_room_problems_rate_limit.py`)
- [ ] 4. 🙋 Junior review tests
- [ ] 5. 🤖 implement: `config/ai.yaml` (2 key ใหม่ · v bump) + `GatewayConfig` + `_with_retries` + `AIRateLimitedError` + `room_problems` · แก้ §2.10 ของ ai-orchestration.md ถ้า §10 ข้อ 1 ok · ruff + pytest ทั้งชุด
- [ ] 6. 🙋 บอกกลุ่ม (แก้ `config/ai.yaml` ซึ่งเป็น shared file + ไฟล์ของ Jam) · `/work-done` → **ถาม Junior ก่อน merge**
- [ ] 7. 🙋 เย็นนี้: journey เต็มบน `main` หลัง merge (งานข้อ 4 ของ work-start) · Claude ไล่ `ai_calls` + log 429

## Definition of done

- 429 ของ call ที่ไม่ใช่ stream รอ `[5, 15, 30]` s, stream รอ `[5]` s ก่อนยอมแพ้ · ค่าอยู่ใน `config/ai.yaml` ไม่มีตัวเลขในโค้ด
- error อื่นยัง retry ตาม `gateway.retries` เดิม · test เดิมทั้งหมดผ่านโดยไม่แก้
- `room_problems` ไม่ลองสร้างโจทย์ใหม่เมื่อ gateway ยอมแพ้เพราะ 429
- PR แยกบน `main` · Jam เป็น reviewer · CI เขียว

## Decisions

- 2026-11-19 · Jam ให้ Junior ตัดสิน · PR แยกจาก #146 (merge แล้ว) · ไม่ทำ C (ข้อความระหว่างรอ) และ D (fallback model) ก่อนวิดีโอ
- 2026-11-19 · #146 ไม่แตะ `_with_retries` · PR นี้แก้เฉพาะ `_with_retries` + 3 จุดที่เรียก (spec §9)
- 2026-11-19 · Junior: แก้ ai-orchestration.md §2.10 ใน PR นี้ แล้วบอก Jam ในคำอธิบาย PR
- 2026-11-19 · Junior: 429 รอ `max(slot, retry_after)` · ยอมแพ้เมื่อ `retry_after > max(table)` (30 s / 5 s) · `max_retry_wait_seconds` ใช้กับ error อื่นเท่านั้น · test เดิม 2 ตัวขัด (spec §10 ข้อ 3) รอ Junior ตัดสินก่อนแก้

## Next step

Junior review test แดง (ข้อ 4) + ตัดสิน test เดิม 2 ตัวใน spec §10 ข้อ 3 → แล้ว `/implement-feature`

## Waiting on

ไม่มี

## Notes for next time

- Jam เป็นเจ้าของ `app/ai/gateway.py`, `app/services/room_problems.py`, `ai-orchestration.md` · ระบุในคำอธิบาย PR ว่าแตะอะไร
