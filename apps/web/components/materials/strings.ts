// Every Thai string of the upload and reading pages, in one place for review (apps/web/CLAUDE.md).
// Spec: specs/features/exam-prep/upload-page.md (May reviews the wording · §10 item 6).

export const materialStrings = {
  loading: "กำลังโหลด…",
  loadFailed: "โหลดไฟล์ไม่สำเร็จ",
  retry: "ลองใหม่",
  notFound: "ไม่พบการเตรียมสอบนี้",
  backHome: "กลับหน้าหลัก",

  // S09
  uploadTitle: "ใส่สิ่งที่จะใช้สอบ",
  uploadSubtitle: "ใส่ชีท ข้อสอบเก่า หรือรูปโน้ตได้หลายไฟล์พร้อมกัน",
  choose: "เลือกไฟล์",
  remove: "เอาออก",
  send: "ส่งทั้งหมดให้ AI อ่าน",
  back: "ย้อนกลับ",
  uploading: "กำลังอัปโหลด…",
  uploaded: "อัปโหลดแล้ว",
  unsupported: "ไฟล์ชนิดนี้ยังไม่รองรับ",
  tooLarge: "ไฟล์ใหญ่เกินไป",
  uploadFailed: "อัปโหลดไม่สำเร็จ",
  kb: (n: number) => `${n} KB`,
  mb: (n: string) => `${n} MB`,

  // S10 (short)
  kindsTitle: "AI เดาไว้แบบนี้",
  kindsSubtitle: "ตรวจแล้วกดยืนยันเพื่อเริ่มอ่านไฟล์",
  classifying: "AI กำลังดูไฟล์…",
  kind: {
    sheet: "ชีทเรียน",
    slides: "สไลด์",
    past_exam: "ข้อสอบเก่า",
    notes: "โน้ต",
    other: "อื่นๆ",
  },
  sure: (percent: number) => `มั่นใจ ${percent}%`,
  unreadable: "อ่านไฟล์นี้ไม่ได้",
  confirm: "ยืนยันแล้วเริ่มประมวลผล",
  confirmFailed: "เริ่มอ่านไฟล์ไม่สำเร็จ ลองอีกครั้งนะ",
  noneReadable: "ไม่มีไฟล์ที่อ่านได้",
  startOver: "ใส่ไฟล์ใหม่",

  // S11
  progressTitle: "กำลังอ่านไฟล์ของคุณ",
  progressSubtitle: "หน้านี้ไปต่อเอง ไม่ต้องกดอะไร",
  progressFailed: "โหลดความคืบหน้าไม่สำเร็จ",
  readFailed: "อ่านไฟล์นี้ไม่สำเร็จ",
  nothingSent: "ยังไม่มีไฟล์ที่ส่งให้อ่าน",
  addFiles: "ใส่ไฟล์",
  // "ลองใหม่" on a failed file or step (ingestion-retry.md §2.1 · May 19 Nov)
  retryFile: (fileName: string) => `ลองอ่าน ${fileName} ใหม่`,
  retryStep: (label: string) => `ลองขั้น ${label} ใหม่`,
  retryFailed: "ลองใหม่ไม่สำเร็จ ลองอีกครั้งได้",
  status: {
    queued: "รอ",
    pending: "รอ",
    running: "กำลังอ่าน",
    done: "เสร็จแล้ว",
    failed: "ไม่สำเร็จ",
  },
} as const;
