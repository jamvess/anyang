# Feature: ห้องติว · ตอบด้วยเสียง

| | |
|---|---|
| Area | voice (หน้าเว็บ) |
| Requirements | TM-07 · TM-06 (ช่องทางตอบที่ 3 · ไม่มีปุ่มตัวเลือก) · TM-21 (ขีดจำกัดจาก config) |
| Owner | May |
| Reviewer | Junior (OQ 5–8 · api.md) |
| Status | approved by May 2026-10-28 (owner · OQ 1–4) · รอ Junior ตอบ OQ 5–8 (api.md) และ config/ai.yaml `guards.min_audio_seconds` |
| Related system spec | ai-orchestration.md §2.2.5 (กดค้างอัด ≤ 60 วินาที → Storage → STT → ช่องพิมพ์ · ไม่ auto-send), §2.8 (STT th-TH, ลบไฟล์เสียงหลัง 7 วัน), §2.9 Limits, §2.10 (STT ใช้ไม่ได้ → พิมพ์แทน) · api.md "ห้องติว" (`POST /sessions/{id}/uploads`, `POST /sessions/{id}/transcribe`, `Room.limits`) · `config/ai.yaml` → `guards.max_audio_seconds` · use-cases.md UC-03 A3, UC-04 A3 · wireframe S18 (`VOICEDRAFT`) · `chat-room-ui.md` §2 (Composer) |

## 1. Context

ผู้ใช้ตอบได้ 3 ทาง: พิมพ์ พูด และถ่ายรูป (TM-06) · ตอนนี้ Composer มีแค่พิมพ์กับแนบรูป · feature นี้เพิ่มปุ่ม 🎤 แบบกดค้างอัดเสียง ปล่อยแล้วส่งเสียงไปแปลงเป็นข้อความ (STT) แล้วใส่ข้อความ**ในช่องพิมพ์** ให้ผู้ใช้แก้แล้วกดส่งเอง ระบบไม่ส่งให้ เพราะคณิตที่พูดออกมา STT มักฟังพลาด ถ้าตรวจผิดเพราะฟังผิดผู้ใช้จะเลิกเชื่อระบบ (ai-orchestration §2.2.5, §2.2.10 ข้อ 4)

## 2. Behavior

**ปุ่มไมค์**

- Composer มีปุ่ม 🎤 (`aria-label` "กดค้างเพื่อพูด") อยู่ก่อนปุ่ม 📷 ตาม wireframe S18 · ปุ่มแสดงเมื่อห้องได้ `transcribe` มา (ห้องที่ไม่มี transport เสียง เช่น fixture ของ S2 ไม่มีปุ่ม · test เดิมที่นับปุ่มของ Composer และห้องจึงไม่ต้องแก้)
- **กดค้าง = อัด** (pointer down เริ่ม, pointer up หรือ pointer ลากออกจากปุ่ม = หยุด) · keyboard: Space หรือ Enter กดค้างที่ปุ่ม = อัด ปล่อย = หยุด (accessibility · apps/web/CLAUDE.md)
- ขอสิทธิ์ไมค์ครั้งแรกที่กด (`navigator.mediaDevices.getUserMedia({audio: true})`) · อัดด้วย `MediaRecorder`
- ระหว่างอัด: ปุ่มเปลี่ยนสถานะ (`aria-pressed="true"`) และมีตัวนับเวลา "0:05 / 1:00" ใต้ช่องพิมพ์ (`role="status"`) · ค่าสูงสุดมาจาก API (OQ 5)
- อัดครบ `max_audio_seconds` → หยุดเองเหมือนปล่อยปุ่ม (ส่งเสียงที่อัดได้ไปแปลง) · ใช้ค่าจาก API ห้าม hard-code 60 (TM-21)
- อัดสั้นกว่า `min_audio_seconds` จาก API → ไม่ส่ง ไม่มีข้อความ error (กดพลาด · ตัดสินแล้ว OQ 3)

**แปลงเสียงเป็นข้อความ**

- ปล่อยปุ่ม → เรียก `transcribe(audio, signal)` ของ transport (HTTP: อัปโหลดผ่าน `/uploads` แล้ว `POST /transcribe` · OQ 6) · ระหว่างรอ: ปุ่ม 🎤 กดไม่ได้ และมีข้อความ "กำลังแปลงเสียง…" (`role="status"`)
- ได้ข้อความกลับมา → **ต่อท้าย**ข้อความที่มีอยู่ในช่องพิมพ์ (ถ้าช่องไม่ว่างคั่นด้วยช่องว่าง 1 ตัว · ตัดสินแล้ว OQ 2) แล้ว focus ช่องพิมพ์ · **ไม่เรียก `onSend`**
- ใต้ช่องพิมพ์แสดง "🎤 ข้อความจากเสียง · แก้ได้ก่อนกดส่ง ระบบไม่ส่งเอง" (wireframe S18 `vnote`) จนกว่าจะส่งหรือลบข้อความจนว่าง
- ข้อความยาวเกิน `max_message_chars` หลังต่อท้าย → ใช้กติกาเดิมของ Composer (ขึ้น "ข้อความยาวเกิน …" และปุ่มส่งกดไม่ได้ · chat-room-ui.md)
- ได้ข้อความว่าง (ไม่ได้ยินอะไร) → ช่องพิมพ์ไม่เปลี่ยน และขึ้น "ไม่ได้ยินเสียง ลองพูดใหม่อีกทีนะ"
- ส่งข้อความที่มาจากเสียง: ใช้ `onSend` เดิม · `input_mode` ของข้อความ user ในห้อง = `voice` ถ้าข้อความมาจากเสียง (แม้จะแก้แล้ว) · API จะรู้ได้ยังไงต้องถาม Junior (OQ 7)

**ใช้ไม่ได้**

- ไม่ให้สิทธิ์ไมค์ หรือเบราว์เซอร์ไม่มี `MediaRecorder` → ขึ้น "ใช้ไมค์ไม่ได้ พิมพ์คำตอบมาแทนนะ" (`role="alert"`) · ปุ่ม 🎤 ยังอยู่ กดใหม่ได้ (ผู้ใช้อาจเปิดสิทธิ์ทีหลัง)
- แปลงเสียงไม่สำเร็จ (network, non-2xx, `error`) → ขึ้น "แปลงเสียงไม่สำเร็จ ลองพูดใหม่หรือพิมพ์แทนนะ" · ช่องพิมพ์ไม่เปลี่ยน (degrade §2.10)
- ปุ่ม 🎤 ใช้ได้ระหว่างที่ติวเตอร์กำลังตอบ (เหมือนพิมพ์ร่างได้ · chat-streaming.md) แต่ส่งได้เมื่อตอบจบ
- ยังไม่มี `/transcribe` จริง (ห้องที่ต่อ API ตอนนี้) → ปุ่มทำแบบเดียวกับ 📷 ตอนที่ยังไม่มี `/uploads`: กดแล้วขึ้น "ตอนนี้ยังพูดตอบไม่ได้ พิมพ์คำตอบมาก่อนนะ" (prop `voiceEnabled` · room-http.md §2 แบบ `imagesEnabled`)
- ออกจากห้องระหว่างอัดหรือรอแปลง → หยุดอัด ปิดไมค์ (`track.stop()`) และยกเลิกคำขอ

## 3. Inputs and outputs

| | Type / schema | ตัวอย่าง |
|---|---|---|
| Input (limits) | `Room.limits.max_audio_seconds`, `Room.limits.min_audio_seconds` (ยังไม่มีใน API · OQ 5) | `60`, `1` |
| Input (เสียง) | `Blob` จาก `MediaRecorder` (`audio/webm` ใน Chrome) | — |
| Transport | `transcribe(audio: Blob, signal) → Promise<{text: string}>` | `{text: "สองเอ็กซ์ลบห้า คูณ สองเอ็กซ์บวกห้า"}` |
| Output | ข้อความในช่องพิมพ์ (ไม่ส่ง) | ช่องพิมพ์ = "สองเอ็กซ์ลบห้า คูณ สองเอ็กซ์บวกห้า" |

## 4. Acceptance criteria

ใช้ `MediaRecorder` และ `getUserMedia` จำลอง กับ `transcribe` จำลองทุกข้อ ไม่ใช้ไมค์หรือ STT จริง · `LIMIT` = `max_audio_seconds` จาก fixture ของห้อง (ไม่ hard-code 60)

**กดค้าง → ข้อความในช่องพิมพ์**

- **AC-1 (TM07)** Given ห้องที่ `voiceEnabled` When กดค้างปุ่ม "กดค้างเพื่อพูด" Then ขอ `getUserMedia({audio: true})` 1 ครั้ง, `MediaRecorder.start` ถูกเรียก, ปุ่ม `aria-pressed="true"` และมีตัวนับเวลา
- **AC-2 (TM07)** Given กำลังอัด 3 วินาที When ปล่อยปุ่ม Then `stop` ถูกเรียก, `transcribe` ได้ `Blob` 1 ครั้ง, ระหว่างรอมี "กำลังแปลงเสียง…" และปุ่ม 🎤 กดไม่ได้ · When `transcribe` คืน `{text: "สองเอ็กซ์ลบห้า"}` Then ช่องพิมพ์ = "สองเอ็กซ์ลบห้า", มีข้อความ "ข้อความจากเสียง · แก้ได้ก่อนกดส่ง ระบบไม่ส่งเอง" และ **`onSend` ไม่ถูกเรียก**
- **AC-3 (TM07)** Given ช่องพิมพ์มี "ข้อ 2" When พูดแล้วได้ "เอ็กซ์เท่ากับสาม" Then ช่องพิมพ์ = "ข้อ 2 เอ็กซ์เท่ากับสาม" (ต่อท้าย · ตัดสินแล้ว OQ 2)
- **AC-4 (TM07)** Given ข้อความจากเสียงอยู่ในช่องพิมพ์ When แก้แล้วกดส่ง Then `onSend` ได้ข้อความที่แก้แล้ว และ bubble user ในห้องมี `input_mode = voice` (OQ 7)
- **AC-5 (TM07)** Given ข้อความจากเสียงอยู่ในช่องพิมพ์ When ลบจนว่าง Then ข้อความ "ข้อความจากเสียง…" หายไป · ข้อความที่พิมพ์ใหม่หลังจากนั้นส่งเป็น `input_mode = text`

**เวลา (AC-boundary · TM21)**

- **AC-6 (TM21)** Given `LIMIT` When อัดถึง `LIMIT − 1` วินาที Then ยังอัดอยู่ · When ถึง `LIMIT` วินาที Then หยุดเองและเรียก `transcribe` (ไม่ต้องปล่อยปุ่ม) · ไม่มีการอัดเกิน `LIMIT` (`LIMIT + 1` ไม่เกิดขึ้น)
- **AC-7 (TM21)** Given fixture ห้องที่ `max_audio_seconds = 5` Then หยุดเองที่ 5 วินาที และตัวนับแสดง "/ 0:05" (ค่ามาจาก API ไม่ใช่ 60)
- **AC-8 (TM07)** Given `min_audio_seconds` จาก fixture When กดแล้วปล่อยก่อน `min_audio_seconds` (− ε) Then ไม่เรียก `transcribe` และไม่มี alert · Given ปล่อยที่ `min_audio_seconds` พอดี Then เรียก `transcribe`

**ใช้ไม่ได้**

- **AC-9 (TM07)** Given `getUserMedia` reject (`NotAllowedError`) When กดปุ่ม Then มี alert "ใช้ไมค์ไม่ได้ พิมพ์คำตอบมาแทนนะ", ไม่อัด, ปุ่มยังกดได้
- **AC-10 (TM07)** Given เบราว์เซอร์ไม่มี `MediaRecorder` When กดปุ่ม Then alert เดียวกับ AC-9
- **AC-11 (TM07)** Given `transcribe` reject When ปล่อยปุ่ม Then alert "แปลงเสียงไม่สำเร็จ ลองพูดใหม่หรือพิมพ์แทนนะ", ช่องพิมพ์ไม่เปลี่ยน, ปุ่ม 🎤 กดได้อีก
- **AC-12 (TM07)** Given `transcribe` คืน `{text: ""}` หรือช่องว่างล้วน Then ช่องพิมพ์ไม่เปลี่ยน และขึ้น "ไม่ได้ยินเสียง ลองพูดใหม่อีกทีนะ"
- **AC-13 (TM07)** Given ห้องที่ `voiceEnabled = false` **หรือ** `limits` ไม่มี `max_audio_seconds` / `min_audio_seconds` When กดปุ่ม 🎤 Then ไม่ขอไมค์ และขึ้น "ตอนนี้ยังพูดตอบไม่ได้ พิมพ์คำตอบมาก่อนนะ"
- **AC-14 (TM07)** Given กำลังอัดหรือรอแปลง When ออกจากห้อง (unmount) Then track ของไมค์ถูก `stop()`, `signal` ของ `transcribe` ถูก abort และไม่มี React error

**ของเดิมและ accessibility**

- **AC-15 (TM07)** Given ติวเตอร์กำลังตอบ (ห้อง busy) When พูดแล้วได้ข้อความ Then ข้อความขึ้นในช่องพิมพ์ แต่ปุ่มส่งกดไม่ได้จน stream จบ (chat-streaming.md)
- **AC-16 (TM07)** Given focus ที่ปุ่ม 🎤 When กด Space ค้างแล้วปล่อย Then อัดและหยุดเหมือนกดด้วยเมาส์
- **AC-17 (TM06)** ปุ่มในห้องที่กดได้: เดิม + "กดค้างเพื่อพูด" · ไม่มีปุ่มตัวเลือกคำตอบ · test เดิมทั้งหมดผ่าน

**AC-tenant (SA-06):** หน้าเว็บไม่อ่านหรือเขียน DB · ไฟล์เสียงไปที่ Storage ผ่าน signed URL ของ session ของผู้ใช้ (backend · OQ 6)

## 5. Data changes

ไม่มีในหน้าเว็บ · backend เก็บไฟล์เสียงใน Storage 7 วัน (`retention.audio_days`) และเก็บแค่ transcript (ai-orchestration §2.8)

## 6. API / SSE changes

| Endpoint / field | Request | Response |
|---|---|---|
| `Room.limits.max_audio_seconds` | — | integer · **ยังไม่มีใน `Limits`** (ค่าอยู่ใน `config/ai.yaml` → `guards`) · OQ 5 |
| `POST /sessions/{id}/uploads` | **ยังไม่กำหนด** (ชนิดไฟล์, ขนาด) | signed URL + path · OQ 6 |
| `POST /sessions/{id}/transcribe` | **ยังไม่กำหนด** · ข้อเสนอ `{audio_path}` | ข้อเสนอ `{text}` · OQ 6 |
| `POST /sessions/{id}/messages` | ข้อความที่มาจากเสียงบอก `input_mode: "voice"` ยังไง · OQ 7 | — |

## 7. AI calls

ไม่มีในหน้าเว็บ · STT (V1) เป็น Google Cloud Speech-to-Text ฝั่ง backend ผ่าน gateway

## 8. Test plan

| Test | ระดับ | ครอบคลุม AC |
|---|---|---|
| `tests/chat/VoiceButton.test.tsx` (ใหม่) | unit (Composer + MediaRecorder จำลอง + fake timers) | AC-1 ถึง AC-3, AC-5 ถึง AC-13, AC-16 |
| `tests/chat/ChatRoomVoice.test.tsx` (ใหม่) | integration | AC-4, AC-14, AC-15 |
| test เดิม | — | AC-17 |

## 9. Out of scope

- TTS / อ่านออกเสียง (TM-09 · ปุ่ม 🔊 ใน wireframe S16)
- แสดงคลื่นเสียงหรือระดับเสียงระหว่างอัด
- พูดในหน้าแก้ขอบเขต (SM-06 · หน้า scope ยังไม่มี)
- phrase hints จากชื่อหัวข้อ (backend · §2.8)
- เล่นเสียงที่อัดกลับมาฟัง

## 10. Open questions

ตัดสินแล้ว (May · 2026-10-28)

1. **วิธีอัด:** กดค้างอัด ปล่อยหยุด ตาม UC และ ai-orchestration §2.2.5
2. **ช่องพิมพ์มีข้อความอยู่แล้ว:** ต่อท้าย (AC-3)
3. **อัดสั้นเกิน:** สั้นกว่า `min_audio_seconds` ไม่ส่ง (AC-8) · เสนอ `guards.min_audio_seconds: 1` ใน `config/ai.yaml` (ไฟล์ร่วม · §11) และส่งมากับ `Room.limits` เหมือน `max_audio_seconds` (OQ 5) · **จนกว่า API จะส่งทั้งสองค่า** หน้าเว็บถือว่ายังพูดตอบไม่ได้ (เหมือน `voiceEnabled = false` · AC-13) เพราะห้าม hard-code
4. **bubble ของข้อความที่มาจากเสียง:** เหมือนข้อความพิมพ์ทุกอย่าง (`input_mode` ยังส่งเป็น `voice` ให้ backend · OQ 7)

ให้ Junior ตอบ (api.md · ไฟล์ร่วม)

5. **`max_audio_seconds` ใน `Limits`:** เพิ่ม field นี้ใน `Room.limits` แบบเดียวกับ `max_image_mb` ได้ไหม
6. **`/uploads` และ `/transcribe`:** body และ response · ข้อเสนอ: `/uploads` `{kind: "audio", content_type}` → `{upload_url, path}` · `/transcribe` `{audio_path}` → `{text}` · error code เมื่อเสียงยาวเกินหรือ STT ล่ม
7. **`input_mode: voice`:** `SendMessageRequest` มีแค่ `{text, image_path}` · ข้อเสนอ: เพิ่ม `input_mode?: "text" | "voice"` หรือ `audio_path` ของเสียงที่แปลงแล้ว (ให้ backend เก็บคู่กับ transcript)
8. **รูปแบบไฟล์:** Chrome อัดเป็น `audio/webm;codecs=opus` · Google STT รับ `WEBM_OPUS` ได้ · Safari อัดเป็น `audio/mp4` · backend รับทั้งสองแบบไหม

## 11. Spec changes needed

- **api.md** (Junior): OQ 5, 6, 7, 8
- **config/ai.yaml** (ไฟล์ร่วม): `guards.min_audio_seconds` ถ้า May เลือก OQ 3 (ก)
- **chat-room-ui.md** §2: รายการปุ่มที่กดได้ในห้องเพิ่ม "กดค้างเพื่อพูด"
- **room-http.md** §2: `voiceEnabled` แบบเดียวกับ `imagesEnabled`
