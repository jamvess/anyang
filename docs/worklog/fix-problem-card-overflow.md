# โจทย์ยาวล้นการ์ดโจทย์ (ก่อนอัดวิดีโอ)

| | |
|---|---|
| Owner | May |
| Branch | `fix/problem-card-overflow` |
| Checklist item | ⭐ Priority: demo end to end · วิดีโอ 23 พ.ย. (`demo-video.md` ผลซ้อม 20 พ.ย. ข้อ 3: "ข้อความโจทย์ยาวล้นการ์ดด้านขวา (May · หลังวิดีโอ)" · May เลือกแก้ก่อนอัด 22 พ.ย.) |
| Status | in progress · 2026-11-22 |

## Plan

- [ ] 1. 🤖 แก้ CSS ของการ์ดโจทย์ (`components/chat/ProblemCard.tsx` + CSS ของ KaTeX ในการ์ด): สูตรยาวขึ้นบรรทัดใหม่ที่จุดตัดของ KaTeX (เครื่องหมาย =, +, − ฯลฯ) และชิดซ้าย · ส่วนที่ยังยาวเกินการ์ด (เช่นข้อความไทยยาวใน `	ext{}`) เลื่อนซ้ายขวาในการ์ด ไม่ล้นออกนอกการ์ด · ไม่แตะ logic, ไม่แตะ test ที่ review แล้ว (`ProblemCard.test.tsx` ต้องการ display block 1 อัน)
- [ ] 2. 🤖 จด `problem-card.md` (ของ May) ว่าโจทย์ยาวต้องไม่ล้นการ์ด · lint, typecheck, test, build
- [ ] 3. 🙋 May ดูในเบราว์เซอร์: ห้องติวของบัญชีทดสอบ (ไม่ใช่บัญชีวิดีโอ) → การ์ดโจทย์ไม่ล้น
- [ ] 4. 🤖 `/work-done` → merge ก่อนอัด

## Definition of done

- โจทย์ยาวอยู่ในการ์ด ไม่ล้นออกด้านขวา · test เดิมผ่าน · CI เขียว · merge ก่อนอัด 22 พ.ย.

## Decisions

- 2026-11-22 · May เลือกแก้ก่อนอัด (ข้อ 2) · แก้แค่ CSS เพราะต้องอัดวันนี้ · test ที่ review แล้วล็อกว่าโจทย์เป็น display block 1 อัน จึงไม่แยกข้อความไทยออกจากสูตร (ทางที่ wrap ได้ดีกว่า แต่เปลี่ยน test · ทำหลังวิดีโอได้)

## Next step

ขั้น 1

## Waiting on

ไม่มี

## Notes for next time

- `text_latex` มาจาก `generate_problem` เป็น LaTeX บรรทัดเดียว คำไทยอยู่ใน `	ext{…}` (`prompts/generate_problem/v2.md` ข้อ 5) · KaTeX แบบ display ไม่ตัดบรรทัดเอง จึงล้น
