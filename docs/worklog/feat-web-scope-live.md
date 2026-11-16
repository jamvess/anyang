# หน้า scope ต่อ API จริง + ยืนยัน (demo ขั้น 5)

| | |
|---|---|
| Owner | Jam (item of May) |
| Branch | `feat/web-scope-live` |
| Checklist item | ⭐ demo ขั้น 5: หน้า scope ต่อ API จริง + ยืนยัน (SM-09) |
| Status | in progress · 2026-11-16 |

## Plan

สิ่งที่มีแล้ว: หน้า `/preps/[id]/scope` (`ScopeReview.tsx`) เรียกผ่าน `apiFetch` (#138) · API อ่าน/ยืนยันบน DB แล้ว (#137 · `scope-db.md`) · รูปร่าง response ตรงกับ type ที่หน้าเว็บเขียนเอง · การ์ดขั้น `scope` ในหน้ารายการลิงก์มาหน้านี้ (#139)

ที่ขาด (เจอตอนเทียบ `scope-review.md` กับ `scope-db.md`):
- `GET /scope` ตอบ `409 scope_not_ready` (ยังอ่านไฟล์ไม่เสร็จ) → หน้าเว็บตอนนี้ขึ้น "โหลดขอบเขตไม่สำเร็จ" + ลองใหม่
- ยืนยันซ้ำ → `409 scope_already_confirmed` → หน้าเว็บขึ้น "ยืนยันไม่สำเร็จ" ทั้งที่ยืนยันแล้ว
- `401` ขึ้นข้อความ error ระหว่างที่ `apiFetch` กำลังพาไปหน้า login (แบบเดียวกับที่แก้ใน #139)
- Next 16 เก็บหน้าที่ซ่อนไว้พร้อม state (`cacheComponents`): กลับมาหน้า scope หลังยืนยัน ต้องโหลดใหม่ให้เห็นแบบอ่านอย่างเดียว
- type ยังเขียนเอง ทั้งที่ OpenAPI มี `Scope`, `TopicSources` แล้ว (spec §6 บอกให้เปลี่ยนเมื่อมี)
- ยังไม่มี prep ขั้น `scope` บน `anyang-dev` ให้ลองในเบราว์เซอร์ (ingestion จริงต้องรออัปโหลดของ #140)

- [x] 1. 🤖 อัปเดต spec `specs/features/scope/scope-review.md` (spec ของ May): OQ 5–8 ตัดสินแล้วใน api.md v1.20 (#137) · เพิ่ม §2 "ต่อ API จริง" + AC-21 ถึง AC-24 (409 ยังไม่พร้อม · 409 ยืนยันแล้ว → ไปห้องติว · 401 ไม่แสดง error · หน้าที่ถูกซ่อนแล้วกลับมาโหลดใหม่) · ใช้ type ที่ generate → 🙋 Jam review spec
- [x] 2. 🤖 `/spec-to-tests`: test ใหม่ใน `tests/scope/scopeLive.test.tsx` (ไม่แตะ `ScopeReview.test.tsx` ที่ review แล้ว) → 🙋 Jam review test
- [x] 3. 🤖 `/implement-feature` จน green · lint · typecheck · build · test ทั้งชุด
- [x] 4. 🤖 + 🙋 (16 พ.ย. · Jam รันแล้ว seed ครบ) ทำ prep ขั้น `scope` บน `anyang-dev` ในบัญชีทดสอบของ Jam (ไม่ใช่บัญชี demo): สคริปต์เขียนผล ingestion ของ MTH10101 (`poc/P3/results/apps-api-ingestion/` + `poc/P3/out/pages`) ลง `materials`, `material_pages`, `topics`, `topic_sources`, `past_exam_questions` ของ prep ที่ระบุ · ต้องใช้ `SUPABASE_SERVICE_ROLE_KEY` ใน `.env` ของ Jam (Claude ไม่อ่าน `.env` · Jam เช็คเองว่ามี) · วิธีละเอียดตัดสินตอนถึงขั้นนี้
- [ ] 5. 🙋 ลองในเบราว์เซอร์บน `anyang-dev` (API ในเครื่อง `AUTH_REQUIRED=true` + `pnpm dev`): รายการ → การ์ด "รอตรวจขอบเขต" → หัวข้อจริง + ดาว + ที่มา → เปิดรายละเอียด → ยืนยัน → ห้องติว → กลับมาหน้า scope เห็น "ยืนยันขอบเขตแล้ว" · Claude ให้ขั้นตอนทีละคลิกตอนถึงขั้นนี้
- [ ] 6. 🤖 จดผลลง spec §8 · อัปเดตตาราง demo ใน `sprint-checklists.md` ตอน `/work-done`

## Definition of done

- หน้า scope แสดงหัวข้อจริงจาก `anyang-dev` (ชื่อ ดาว ที่มา) และกดดูที่มาได้ · ยืนยันแล้วบันทึก `scope_versions` + ไปห้องติว (SM-09) · ผ่านการลองในเบราว์เซอร์
- AC-21 ถึง AC-24 มี test และผ่าน · test เดิมของหน้า scope ผ่านโดยไม่แก้
- lint, typecheck, build, CI เขียว

## Decisions

- 2026-11-16 · ทำงานของ May ช่วง solo (Jam เลือกข้อ 2 ของ `/work-start ALL`) · May บอกไว้แล้วว่าจัดการได้ เดี๋ยวมา review ทีหลัง

## Next step

ข้อ 5: Jam ลองในเบราว์เซอร์กับ prep `MTH10101 seed` (บัญชีทดสอบของ Jam) · รายการ → scope → รายละเอียด → ยืนยัน → ห้องติว → back เห็น "ยืนยันขอบเขตแล้ว" → การ์ด "พร้อมติว"

## Waiting on

ไม่มี (ข้อ 4 อาจรอ Junior ถ้าเครื่อง Jam ไม่มี service role key ของ `anyang-dev`)

## Notes for next time

- เทส web ทั้งชุดบนเครื่องนี้ใช้ `npx vitest run --maxWorkers=2` (ค่า default timeout ตอนเครื่องโหลดหนัก)
