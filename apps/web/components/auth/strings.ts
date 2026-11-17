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
  // Sign-up page and the links between the two pages (specs/features/platform/web-signup.md §2.5).
  signupTitle: "สมัครสมาชิก",
  confirmPassword: "ยืนยันรหัสผ่าน",
  signupSubmit: "สมัครสมาชิก",
  signupSubmitting: "กำลังสมัคร…",
  passwordMismatch: "รหัสผ่านทั้งสองช่องไม่ตรงกัน",
  emailTaken: "อีเมลนี้มีบัญชีแล้ว",
  weakPassword: "รหัสผ่านสั้นหรือง่ายเกินไป ลองตั้งใหม่",
  emailInvalid: "อีเมลนี้ใช้สมัครไม่ได้",
  signupDisabled: "ตอนนี้ปิดรับสมัครอยู่",
  signupFailed: "สมัครไม่ได้ตอนนี้ ลองใหม่อีกครั้ง",
  checkEmail: "สมัครแล้ว เปิดอีเมลเพื่อยืนยันก่อนเข้าสู่ระบบ",
  haveAccount: "มีบัญชีแล้ว?",
  toLogin: "เข้าสู่ระบบ",
  noAccount: "ยังไม่มีบัญชี?",
  toSignup: "สมัครสมาชิก",
} as const;
