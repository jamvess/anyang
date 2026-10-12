# evals/

Golden sets และ script วัดผล AI ใช้ทั้งใน PoC และใน CI (รันเมื่อ prompt หรือ model เปลี่ยน)

```
evals/
├─ handwriting/        # P1
│  ├─ raw/             # รูปจริง (gitignored ถ้าเป็นลายมือเพื่อน · เก็บใน Drive ทีม)
│  └─ labels.jsonl
├─ answers/            # P2
│  └─ labels.jsonl
├─ topics/             # P3
│  └─ <subject>/labels.json
└─ run_eval.py         # uv run python evals/run_eval.py --purpose extract_answer --prompt v1
```

## รูปแบบ label

**handwriting/labels.jsonl** (1 บรรทัด = 1 รูป)

```json
{"id": "hw_001", "image": "raw/hw_001.jpg", "problem": "x^2-5x+6", "lines": ["x^2-5x+6", "(x-2)(x-3)"], "labeled_by": "May"}
```

**answers/labels.jsonl**

```json
{"id": "ans_001", "problem": "Factor x^2-5x+6", "answer_format": "factored", "reference": "(x-2)(x-3)",
 "lines": ["x^2-5x+6", "(x-2)(x+3)"], "verdict": "incorrect", "error_type": "sign", "first_wrong_line": 2, "labeled_by": "Jam"}
```

**topics/<subject>/labels.json**

```json
{"topics": [{"name": "การแยกตัวประกอบพหุนาม", "stars": 3, "skills": ["ดึงตัวร่วม", "ผลต่างกำลังสอง"]}],
 "question_map": {"midterm-2567:Q3": "การแยกตัวประกอบพหุนาม"}}
```

## กฎ

- คน label ไม่ใช่คนทำ PoC ตัวนั้น
- ขอความยินยอมก่อนใช้ลายมือของเพื่อน และไม่ commit รูปลง repo สาธารณะ
- เป้าหมายของแต่ละ eval อยู่ใน `specs/poc/README.md`
