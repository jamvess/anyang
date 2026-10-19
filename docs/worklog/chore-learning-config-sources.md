# ตรวจ `config/learning.yaml` ว่าทุกค่ามีป้ายที่มา

| | |
|---|---|
| Owner | Jam |
| Branch | `chore/learning-config-sources` |
| Checklist item | ตรวจ `config/learning.yaml` ว่าทุกค่ามีป้ายที่มา |
| Status | in progress · 2026-10-19 |

## Plan

- [ ] 1. 🤖 ตรวจทุก key ใน `config/learning.yaml`: มีป้าย [A]/[B]/[calc]/[C] ไหม · [A]/[B] มีที่มาที่อ้างได้ไหม · [C] บอกวิธีและเวลา calibrate ไหม · มีแถวใน `learning-model.md` และค่าตรงกันไหม → สรุปเป็นรายการ
- [ ] 2. 🙋 Jam: ตัดสินป้ายและที่มาของค่าที่ขาด (Claude เสนอให้ทีละข้อ)
- [ ] 3. 🤖 แก้ comment ใน `learning.yaml` + เพิ่มแถวใน `learning-model.md` §"ที่มาของตัวเลข" (ไม่เปลี่ยนค่า) · รัน `uv run pytest` (test_settings โหลด config)

## Definition of done

- ทุกค่าที่เป็นตัวเลขใน `learning.yaml` มีป้าย · [C] ทุกตัวบอกว่าวัดอย่างไรและเมื่อไร
- ทุกค่ามีแถวใน `learning-model.md` และค่าตรงกัน
- ไม่มีค่าไหนเปลี่ยน · test ผ่าน · ติ๊ก checklist

## Decisions

- 2026-10-19 · ทำระหว่างรอโควตา Gemini ของ `poc/P3` · ผล P3 เรื่อง `three_star_min_r` ยังไม่ใส่ใน PR นี้ จะใส่ใน PR config หลัง P3

## Next step

ขั้น 2: Jam ตอบข้อเสนอป้ายในแชท

## Waiting on

Jam

## Notes for next time

- งานที่พักไว้: `poc/P3` (PR #15) รอโควตา ≈ 14:00 น. 2026-10-19 · `chore/handwriting-photos` (PR #11) รอรูป
