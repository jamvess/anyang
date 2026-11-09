# ยืนยัน check ของ `0003` แล้ว db push ขึ้น anyang-dev และ anyang-staging

| | |
|---|---|
| Owner | Junior |
| Branch | `chore/db-push-0003` |
| Checklist item | ปรับ `schema.sql` ตามที่เจอระหว่าง P3 + วาด ERD (D3) · ส่วน "⚠️ Junior ยืนยัน check ก่อน แล้วค่อย `db push` ขึ้น `anyang-dev` และ `anyang-staging`" |
| Status | in progress · 2026-11-09 |

## Plan

- [x] 1. 🤖 อัปเดต docs: `data-model.md` (ข้อ 1 "รอ Junior ยืนยัน" → ยืนยันแล้ว), note ใต้ข้อ D3 ใน `sprint-checklists.md`
- [x] 2. `anyang-dev`: 🙋 Junior `npx supabase login` (ถ้าต้อง) + `npx supabase link --project-ref <ref>` ใน Git Bash · 🤖 `db push --dry-run` → โชว์ output → 🙋 ok → 🤖 `db push` → `migration list` → query เช็ค RLS ของ `topic_sources` + คอลัมน์ `map_note` → `unlink`
- [ ] 3. `anyang-staging` (`sfapuygntxuelsxsgkay`): แบบเดียวกับขั้น 2
- [ ] 4. 🤖 อัปเดต `infra/README.md` (migration ที่ขึ้นแล้วของแต่ละ project) + ร่างข้อความกลุ่ม → `/work-done`

## Definition of done

- `npx supabase migration list` ของทั้ง `anyang-dev` และ `anyang-staging` แสดง `0003` ทั้ง Local และ Remote
- `topic_sources` มี RLS เปิดบนทั้งสอง project
- docs ไม่มีคำว่า "รอ Junior ยืนยัน" ของ check นี้แล้ว และไม่มี project ไหนยัง link ค้าง

## Decisions

- 2026-11-09 · เก็บ `check (page_from >= 1 and page_to >= page_from)` ตามที่ Jam เสนอ · Junior ยืนยัน ไม่ต้องมี `0004`
- 2026-11-09 · แบ่งงาน: Junior ทำแค่ login + link (CLI ใช้ login token ไม่ถาม DB password) · Claude รัน dry-run / push (หลัง Junior ok) / ตรวจ / unlink · ให้ Junior เห็น dry-run ก่อนทุกครั้ง

## Next step

ขั้น 3: รอ `anyang-staging` ขึ้น `ACTIVE_HEALTHY` (Junior กด Restore ใน Dashboard แล้ว) → link → `migration list --remote` → dry-run → Junior ok → push → ตรวจ → `unlink` · จากนั้นไปข้อ 2 ของ /work-start (เปิด live บน api-staging + วัด TTFT)

## Waiting on

ไม่มี

## Notes for next time

- 2026-11-09 · `anyang-dev`: push ครั้งก่อนไม่ได้รัน (`0003` ไม่มีบน Remote) · push แล้ว · `migration list --remote` มี `0001`–`0003` ครบ · `topic_sources` RLS เปิด, policy 1 · `map_note` มีแล้ว · ตาราง public ที่ไม่มี RLS = 0 · link ยังค้างที่ dev ไว้ unlink ตอนจบ
- CLI เวอร์ชันนี้ใช้ local stack เป็นค่า default: `migration list`, `db push`, `db query` ต้องใส่ `--remote` ไม่อย่างนั้นจะยิงไปที่ `127.0.0.1:54322` · push ที่รันโดย agent ต้องใส่ `--yes` (หลัง Junior ok dry-run แล้ว)

- `db push` ทำได้เฉพาะ Junior · หลัง push ต้อง `npx supabase unlink` ทุกครั้ง (`infra/README.md`)
