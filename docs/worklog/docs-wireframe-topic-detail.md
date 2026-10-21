# Wireframe · ดูรายละเอียดหัวข้อในหน้าขอบเขต + map_note (UC-02 A4)

| | |
|---|---|
| Owner | May |
| Branch | `docs/wireframe-topic-detail` |
| Checklist item | ไม่มีข้อตรงใน checklist · ตามที่ May ตอบ Junior ใน PR #67 ข้อ 3: หน้าขอบเขตแสดง `map_note` ตอนกดดูหัวข้อ + กล่อง "ข้อสอบที่ไม่เข้าหัวข้อไหน" |
| Status | ready for work-done · 2026-10-21 |

## Plan

- [x] 1. 🤖 branch + worklog + draft PR
- [x] 2. 🤖 เพิ่มหน้า S38 ในบทที่ 6: กดหัวข้อใน S12 แล้วเห็นข้อความต้นฉบับจากชีท (SM-04 · UC-02 A4) + ข้อสอบเก่าที่อยู่ในหัวข้อนั้นพร้อม `map_note` ถ้ามี + กล่อง "ข้อสอบที่ไม่เข้าหัวข้อไหน" พร้อมเหตุผล · screenshot ตรวจ
- [x] 3. 🙋 May review หน้าตา
- [x] 4. 🤖 `use-cases.md` UC-02 A4 เพิ่ม `[S38]` และสิ่งที่แสดง

## Definition of done

- S38 อยู่ใน wireframe ตรงกับที่ตอบ Junior · script ไม่มี error · May approve

## Decisions

## Next step

รัน /work-done

## Waiting on

ไม่มี

## Notes for next time

- screenshot ของ wireframe ติด fade-in · ในสำเนาที่ใช้แคปให้ใส่ `*{animation:none!important;transition:none!important;opacity:1}` ก่อน `</style>`

- `map_note` มาจาก A7 `map_questions` (`note`) · Junior จะเพิ่ม `past_exam_questions.map_note` ใน #67 · API ของหน้า scope ยังไม่มีใน api.md
