// Every Thai string of the tutor room, in one place for review (apps/web/CLAUDE.md).

export const roomStrings = {
  daysLeft: (n: number) => `สอบใน ${n} วัน`,
  exitRoom: "ออกจากห้องติว",
  you: "คุณ",
  inputLabel: "พิมพ์ตอบ",
  inputPlaceholder: "พิมพ์ตอบ...",
  attach: "แนบรูป",
  removePhoto: "เอารูปออก",
  send: "ส่ง",
  tooLong: (max: number) => `ข้อความยาวเกิน ${max} ตัวอักษร`,
  notImage: "แนบได้เฉพาะรูป",
  imageTooBig: (max: number) => `รูปใหญ่เกิน ${max} MB`,
  typing: "กำลังพิมพ์",
  sendFailed: "ส่งไม่สำเร็จ ลองส่งอีกทีนะ",
  imagesNotYet: "ตอนนี้ยังส่งรูปไม่ได้ พิมพ์คำตอบมาก่อนนะ",
  loading: "กำลังเปิดห้องติว…",
  loadFailed: "เปิดห้องติวไม่สำเร็จ",
  prepNotFound: "ไม่พบการเตรียมสอบนี้",
  retry: "ลองใหม่",
  backHome: "กลับหน้าหลัก",
} as const;
