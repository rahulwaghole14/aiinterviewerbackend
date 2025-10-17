# 🎤 MICROPHONE NOT WORKING - FIX GUIDE

## ⚠️ PROBLEM:
Your browser is receiving **SILENT audio** (RMS: 0.000007) from the microphone.
This means the microphone is either:
- Muted
- Not selected as default
- Blocked by Windows privacy settings
- Not working properly

## ✅ SOLUTION - FOLLOW THESE STEPS:

### **STEP 1: Check Windows Microphone Privacy**

1. Press **Windows Key + I** to open Settings
2. Go to **Privacy & Security** → **Microphone**
3. Make sure **"Microphone access"** is **ON**
4. Make sure **"Let apps access your microphone"** is **ON**
5. Make sure **"Let desktop apps access your microphone"** is **ON**
6. Scroll down and make sure **Chrome/Edge** is **allowed**

### **STEP 2: Check Microphone is Not Muted**

1. Press **Windows Key + I** to open Settings
2. Go to **System** → **Sound**
3. Under **Input**, select **"Microphone Array (Realtek Audio)"**
4. Make sure the **volume slider is at 100%**
5. Click **"Test your microphone"**
6. **SPEAK LOUDLY** - you should see a blue bar moving
7. If the blue bar moves = microphone works in Windows!
8. If the blue bar doesn't move = microphone is muted or broken

### **STEP 3: Advanced Microphone Settings**

1. Right-click the **speaker icon** in the taskbar (bottom-right)
2. Click **"Open Sound settings"**
3. Scroll down and click **"More sound settings"**
4. Go to the **"Recording"** tab
5. Find **"Microphone Array (Realtek Audio)"**
6. **Right-click** on it → **"Properties"**
7. Go to **"Levels"** tab:
   - Set **Microphone** to **100**
   - Set **Microphone Boost** to **+20dB** or **+30dB** (if available)
   - Make sure the **🔇 mute button is NOT pressed**
8. Click **"OK"**
9. In the Recording tab, **speak** - you should see **green bars** moving

### **STEP 4: Check Browser Microphone Permissions**

1. Open **Chrome**
2. Go to **chrome://settings/content/microphone**
3. Make sure microphone is **"Allowed"** (not blocked)
4. Make sure **"Microphone Array (Realtek Audio)"** is selected as default
5. Clear any blocked sites

### **STEP 5: Restart Browser**

1. **Close ALL Chrome/Edge windows**
2. **Reopen browser**
3. Test again

---

## 🧪 QUICK TEST:

After following the steps above, test your microphone:

1. Open this link: `http://127.0.0.1:8000/static/test_mic_windows.html`
2. Click "Start Test"
3. **Speak loudly**: "Hello, testing, one two three"
4. **You should see:**
   - ✅ Green bar moving up and down
   - ✅ "MICROPHONE WORKING!" message
   - ✅ RMS value > 0.01 when speaking

---

## 🆘 IF STILL NOT WORKING:

**Check these:**
1. Is your microphone physically connected?
2. Is there a hardware mute button on your microphone/headset?
3. Try using a different microphone (headset, webcam mic, etc.)
4. Try in a different browser (Edge, Firefox)
5. Restart your computer

---

## ✅ ONCE MICROPHONE WORKS:

When the test shows "MICROPHONE WORKING!", the interview STT will work automatically!

The code is already perfect - we just need audio input! 🎤

