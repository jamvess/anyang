# ตรวจ architecture.md ให้ตรงกับที่ตั้งจริง (D2)

| | |
|---|---|
| Owner | Jam (item of Junior) |
| Branch | `docs/architecture-d2` |
| Checklist item | ตรวจ `specs/system/architecture.md` ให้ตรงกับที่ตั้งจริง (D2) |
| Status | in progress · 2026-11-01 |

## Plan

- [ ] 1. 🤖 เทียบ `architecture.md` v1.1 (12 ต.ค.) กับของจริง: `infra/README.md`, `infra/*.yaml`, `.github/workflows/`, `config/ai.yaml`, `apps/api/app/` (gateway, providers, auth), `docs/team/setup.md`, report PoC · จดทุกจุดที่ไม่ตรงพร้อมหลักฐาน
- [ ] 2. 🤖 แก้ `architecture.md` เป็น v1.2: แผนภาพ (provider `vertex`/`gemini`/`fake`, Claude เป็นแผน, API ตรวจ JWT กับ Supabase Auth, `ai_calls` + Cloud Logging), tech stack ที่ PoC ตัดสินแล้ว, environments จริง (`anyang-dev`, `anyang-staging`, `api-staging`, Vercel), flow deploy จริง, ตาราง "สร้างแล้ว / ยังเป็นแผน"
- [ ] 3. 🙋 Jam อ่านทวน (Junior ดูย้อนหลังได้)
- [ ] 4. 🤖 checklist: เพิ่มบรรทัดความคืบหน้าใต้ข้อ S4 "อัปเดต architecture และ data model ตามผล PoC (D2, D3)"

## Definition of done

- ทุกแถวใน `architecture.md` ตรงกับ `infra/README.md`, `config/ai.yaml`, workflow ใน `.github/` และ report PoC · ของที่ยังไม่สร้างเขียนชัดว่าเป็นแผน
- ไม่มีตัวเลขหรือชื่อ resource ที่ขัดกับไฟล์ต้นทาง

## Decisions

- 2026-11-01 · ไม่แก้ไฟล์ต้นทาง (`infra/README.md`, `ai.yaml`) ใน PR นี้ · ถ้าเจอว่าต้นทางผิด จดไว้ใน Notes แล้วแยก PR

## Next step

ขั้น 1: จดจุดที่ไม่ตรงพร้อมหลักฐาน

## Waiting on

ไม่มี (Junior ดูย้อนหลังหลัง merge)

## Notes for next time

- 
