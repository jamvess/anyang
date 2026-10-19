# ตรวจ `config/learning.yaml` ว่าทุกค่ามีป้ายที่มา

| | |
|---|---|
| Owner | Jam |
| Branch | `chore/learning-config-sources` |
| Checklist item | ตรวจ `config/learning.yaml` ว่าทุกค่ามีป้ายที่มา |
| Status | in progress · 2026-10-19 |

## Plan

- [x] 1. 🤖 ตรวจทุก key ใน `config/learning.yaml`: มีป้าย [A]/[B]/[calc]/[C] ไหม · [A]/[B] มีที่มาที่อ้างได้ไหม · [C] บอกวิธีและเวลา calibrate ไหม · มีแถวใน `learning-model.md` และค่าตรงกันไหม → สรุปเป็นรายการ
- [x] 2. 🙋 Jam: ตัดสินป้ายและที่มาของค่าที่ขาด (Claude เสนอให้ทีละข้อ)
- [x] 3. 🤖 แก้ comment ใน `learning.yaml` + เพิ่มแถวใน `learning-model.md` §"ที่มาของตัวเลข" (ไม่เปลี่ยนค่า) · รัน `uv run pytest` (test_settings โหลด config)

## Definition of done

- ทุกค่าที่เป็นตัวเลขใน `learning.yaml` มีป้าย · [C] ทุกตัวบอกว่าวัดอย่างไรและเมื่อไร
- ทุกค่ามีแถวใน `learning-model.md` และค่าตรงกัน
- ไม่มีค่าไหนเปลี่ยน · test ผ่าน · ติ๊ก checklist

## Decisions

- 2026-10-19 · ทำระหว่างรอโควตา Gemini ของ `poc/P3` · ผล P3 เรื่อง `three_star_min_r` ยังไม่ใส่ใน PR นี้ จะใส่ใน PR config หลัง P3
- 2026-10-19 · (Jam ok ทุกข้อที่เสนอ) ค่าที่ไม่มีป้าย 5 ตัวได้ [calc]: three_star_final_difficulty, tight_mode_two_star_difficulty, min_gap_days, prerequisite_of_three_star_gets, final_mode_days_left · [C] ที่ไม่บอกวิธี 6 ตัวเติมวิธีและเวลา: min_independent_correct_per_skill, default_session_minutes, triage_days_left, min_user_turns_between, encourage_fail_streak, idle_minutes_to_end · เปลี่ยนป้าย 2 ตัว: sympy_timeout_seconds [B]→[calc] (ไม่ใช่มาตรฐาน), max_generate_retries [B]→[C] (ไม่มีอ้างอิง)
- 2026-10-19 · ค่าที่ไม่ใช่ตัวเลข (bool, list, ชื่อ method) ไม่ติดป้าย แต่ใส่ว่าอ้างจากหัวข้อไหนใน spec แทน เพราะเป็นกติกาการออกแบบ
- 2026-10-19 · เพิ่มแถวใน `learning-model.md` ครบทุกค่าที่ยังไม่มี (§3, §4, §2, §6, §8) · ตรวจแล้วว่าค่าใน yaml ไม่เปลี่ยนเลย (diff หลังตัด comment ว่าง) · คำนวณ BKT ซ้ำแล้ว ถูก 3 ข้อติดได้ 0.986 ตรงกับ §1

## Next step

ทุกขั้นเสร็จแล้ว · พิมพ์ `/work-done`

## Waiting on

ไม่มี

## Notes for next time

- งานที่พักไว้: `poc/P3` (PR #15) รอโควตา ≈ 14:00 น. 2026-10-19 · `chore/handwriting-photos` (PR #11) รอรูป
