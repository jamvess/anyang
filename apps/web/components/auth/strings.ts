// Text of the login and logout pages (spec: specs/features/platform/web-login.md §2.1 item 8).
// One place, so May can review and change the wording.
export const authStrings = {
  title: "เข้าสู่ระบบ",
  email: "อีเมล",
  password: "รหัสผ่าน",
  submit: "เข้าสู่ระบบ",
  submitting: "กำลังเข้าสู่ระบบ…",
  wrongCredentials: "อีเมลหรือรหัสผ่านไม่ถูกต้อง",
  failed: "เข้าสู่ระบบไม่ได้ตอนนี้ ลองใหม่อีกครั้ง",
  loading: "กำลังโหลด…",
  loggingOut: "กำลังออกจากระบบ…",
} as const;
