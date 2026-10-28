# อัปเดต test strategy ให้ตรงกับสถานะ 28 ต.ค.

| | |
|---|---|
| Owner | Jam |
| Branch | `docs/test-strategy-refresh` |
| Checklist item | ไม่มีข้อตรง · ต่อจาก "Test strategy 1 หน้าใน `specs/system/`" (Jam · S4 · ติ๊กแล้ว PR #55) |
| Status | in progress · 2026-10-28 |

## Plan

- [x] 1. 🤖 นับ test จริงบน `main` (`b4a6cfa`) แล้วแก้คอลัมน์ "ตอนนี้" ใน §2 และตัวเลขใน §5 ของ `specs/system/test-strategy.md` · หลักการ (§1, §3, §4) ไม่แก้
- [x] 2. 🙋 Jam เช็คตัวเลขในตาราง §2

## Definition of done

- ตัวเลขใน §2 และ §5 ตรงกับ `pytest --co` / `pnpm test` บน `main` ณ วันที่เขียน · version ขึ้นเป็น v1.1

## Decisions

- 2026-10-28 · นับจาก `main` ไม่รวม PR ที่ยังไม่ merge (#80 เพิ่ม test อีก: pipeline 17, model 12, sign flip 8, `evals/` 5) · เขียนอ้างไว้ในตาราง
- 2026-10-28 · แบ่ง `tests/unit/` 291 ตัวตามชั้น: domain 25 (merge rules) · math 43 (SymPy) · gateway + schema 108 (gateway 51, `scope_ai_models` 40, `vision_extract_pages` 6, Gemini 11) · API contract 115 (ที่เหลือ)

## Next step

ครบทุกขั้น · รัน `/work-done`

## Waiting on

ไม่มี

## Notes for next time

- `poc/P3/test_p3.py` เก็บ test ไม่ได้ (ImportError) · ไม่ได้แก้ในงานนี้ จดไว้ใน §5
