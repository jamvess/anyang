// Text of the exam prep list and the create form (spec: specs/features/exam-prep/prep-list-page.md
// §2.3). One place, so May can review and change the wording. Every number comes from the API.
export const prepStrings = {
  title: "การเตรียมสอบของฉัน",
  loading: "กำลังโหลด…",
  loadFailed: "โหลดรายการไม่สำเร็จ",
  retry: "ลองอีกครั้ง",
  empty: "ยังไม่มีการเตรียมสอบ",
  create: "สร้างการเตรียมสอบ",
  logout: "ออกจากระบบ",
  daysLeft: (n: number) => `อีก ${n} วัน`,
  examToday: "สอบวันนี้",
  examPassed: "สอบผ่านไปแล้ว",
  stage: {
    materials: "รออัปโหลดไฟล์",
    processing: "กำลังอ่านไฟล์",
    scope: "รอตรวจขอบเขต",
    tutoring: "พร้อมติว",
  },
  readiness: (percent: number) => `ความพร้อม ${percent}%`,
  notPassed: (n: number) => `ยังไม่ผ่าน ${n} หัวข้อ`,
  // The create form (S08)
  formTitle: "สร้างการเตรียมสอบ",
  name: "ชื่อการสอบ",
  examDate: "วันสอบ",
  dailyMinutes: "เวลาต่อวัน (นาที)",
  submit: "สร้าง",
  submitting: "กำลังสร้าง…",
  cancel: "ยกเลิก",
  examDatePast: "วันสอบต้องไม่ก่อนวันนี้",
  invalid: "ตรวจชื่อ วันสอบ และเวลาต่อวันอีกครั้ง",
  saveFailed: "บันทึกไม่ได้ตอนนี้ ลองใหม่อีกครั้ง",
} as const;
