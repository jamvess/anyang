# ตัดสินเรื่องค้างของหน้าที่ Jam ทำให้ (login · รายการ · อัปโหลด · scope)

| | |
|---|---|
| Owner | May |
| Branch | `docs/may-ui-decisions` |
| Checklist item | (ข้อย่อยของ S4: "May: ดูหน้าตาและข้อความ" ใน ⭐ demo ขั้น 1, 2, 3, 5) |
| Status | in progress · 2026-11-17 |

## Plan

- [x] 1. 🙋 May ตัดสินผ่านตัวเลือก: `prep-list-page.md` §10 ข้อ 1–2 · `upload-page.md` §10 ข้อ 2–6 · `scope-review.md` OQ 9 · ข้อความใน `components/{auth,preps,materials,scope}/strings.ts`
- [x] 2. 🤖 จดผลใน §10 ของแต่ละ spec · แก้ข้อความที่ May เปลี่ยน (เช็คก่อนว่า test ที่ review แล้วอ้างข้อความนั้นไหม)
- [x] 3. 🤖 (ไม่ต้อง · ไม่ได้แก้ข้อความ) test + lint + typecheck (ถ้าแก้ข้อความ)
- [ ] 4. 🤖 `/work-done`

## Definition of done

- ทุกข้อ "(May)" ใน §10 ของ 3 spec มีคำตอบ · ข้อความที่ May อยากแก้แก้แล้ว · ติ๊ก/จดใน checklist

## Decisions

- 2026-11-17 · May: วันที่เหลือไม่แสดงจนสร้างเสร็จ · หลังสร้างไปหน้าอัปโหลด (ยืนยันของ Jam) · "มั่นใจ n%" ตามเดิม · ข้อความทุกหน้าโอเค ไม่แก้

## Next step

`/work-done`

## Waiting on

ไม่มี

## Notes for next time

- หน้าเหล่านี้จะอยู่ในวิดีโอ 23 พ.ย. · แก้ข้อความก่อนอัด
