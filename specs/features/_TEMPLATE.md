# Feature: <ชื่อ feature>

| | |
|---|---|
| Area | scope / tutor / checker / planner / buddy / persona / voice / platform |
| Requirements | <ID เช่น SM-03, TM-16> |
| Owner | <ชื่อ> |
| Reviewer | <ชื่อ> |
| Status | draft / approved / implemented |
| Related system spec | <เช่น ai-orchestration.md §2.3.5, learning-model.md §2> |

## 1. Context

<2–4 ประโยค: feature นี้แก้ปัญหาอะไร อยู่ตรงไหนของ flow ใครเรียกใช้>

## 2. Behavior

<อธิบายการทำงานทีละขั้น ถ้ามีสูตรให้เขียนสูตรและอ้างถึง key ใน `config/learning.yaml` ห้ามใส่ตัวเลขลอยๆ>

## 3. Inputs and outputs

| | Type / schema | ตัวอย่าง |
|---|---|---|
| Input | | |
| Output | | |

## 4. Acceptance criteria

เขียนแบบ Given/When/Then ทุกข้อต้อง test ได้โดยไม่ใช้ AI model จริง และต้องมี ID ของ requirement

- **AC-1 (<REQ-ID>)** Given … When … Then …
- **AC-2 (<REQ-ID>)** Given … When … Then …
- **AC-boundary (<REQ-ID>)** ทดสอบที่ threshold − ε, = threshold, + ε
- **AC-tenant (SA-06)** ถ้าอ่านหรือเขียนข้อมูล: user ของ tenant อื่นมองไม่เห็น

## 5. Data changes

| Table | Column / index / policy | เพิ่ม / แก้ |
|---|---|---|

## 6. API / SSE changes

| Endpoint / event | Request | Response |
|---|---|---|

## 7. AI calls

| Purpose | Tier | Output schema | Prompt file |
|---|---|---|---|

(ถ้าไม่มีให้เขียน "ไม่มี")

## 8. Test plan

| Test | ระดับ (unit / integration / e2e / eval) | ครอบคลุม AC |
|---|---|---|

## 9. Out of scope

- 

## 10. Open questions

- 

## 11. Spec changes needed

<ถ้า feature นี้ต้องแก้ไฟล์ใน `specs/system/` หรือ `config/` ให้ระบุที่นี่ ให้ reviewer อนุมัติก่อน>
