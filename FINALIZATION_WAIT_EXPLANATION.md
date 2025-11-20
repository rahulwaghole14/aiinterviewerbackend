# 📝 Explanation: `FINALIZATION_WAIT = 1000` (1 second)

## 🎯 **What is FINALIZATION_WAIT?**

`FINALIZATION_WAIT` is a timing constant that represents **1 second (1000 milliseconds)** - the amount of time the system waits for Deepgram to send the final transcript before submitting the answer to the server.

## 🔍 **Why is it needed?**

### **The Problem:**
When a user finishes speaking and clicks "Done" or the system moves to review phase, Deepgram might still be processing the last few words of speech. Deepgram needs time to:
1. Process the final audio chunks
2. Finalize the last utterance (after 500ms of silence based on `endpointing=500`)
3. Send the final transcript result

### **The Solution:**
Wait 1 second before checking for the final transcript to ensure Deepgram has had enough time to process and send all final results.

## 📍 **Where it's used in the code:**

### **Location 1: `sendAudioToServer()` function**

```javascript
async function sendAudioToServer() {
    // Get current transcript
    let answerText = getFullTranscript();
    
    // If no transcript yet, wait for Deepgram to finalize
    if (!answerText.trim()) {
        console.log('⏳ Waiting for final transcript...');
        await new Promise(resolve => setTimeout(resolve, 1000)); // ← FINALIZATION_WAIT
        answerText = getFullTranscript(); // Check again after wait
    }
    
    // Submit to server
    // ...
}
```

**Purpose:** Ensures we capture the final transcript even if Deepgram is still processing when submission starts.

### **Location 2: `moveToReviewPhase()` function**

```javascript
function moveToReviewPhase() {
    const currentTranscript = getFullTranscript();
    
    if (!currentTranscript && isRecordingActive) {
        // No transcript yet - wait for Deepgram to finalize
        console.log('⏳ Waiting for Deepgram to finalize transcript (1 second)...');
        setTimeout(() => {
            const finalTranscript = getFullTranscript();
            // Process transcript...
            stopRecordingAndProcessing();
            sendAudioToServer();
        }, 1000); // ← FINALIZATION_WAIT
        return;
    }
    
    // Continue with normal flow...
}
```

**Purpose:** Gives Deepgram time to send the final transcript when the user moves to review phase immediately after speaking.

## ⏱️ **Timing Breakdown:**

```
User stops speaking
    ↓
Deepgram detects silence (500ms based on endpointing)
    ↓
Deepgram finalizes utterance
    ↓
Deepgram sends final transcript (may take 100-500ms)
    ↓
[FINALIZATION_WAIT: 1000ms] ← Wait to ensure we receive it
    ↓
Check for final transcript
    ↓
Submit to server
```

## 🎯 **Why 1 second (1000ms)?**

1. **Deepgram endpointing:** 500ms (time to detect silence)
2. **Deepgram processing:** ~100-300ms (time to process and send)
3. **Network latency:** ~50-100ms (time for message to arrive)
4. **Safety buffer:** ~200-400ms (extra time for edge cases)

**Total:** ~850-1300ms → **1000ms is a safe middle ground**

## 📊 **What happens during the wait:**

### **Scenario 1: Transcript arrives during wait**
```
0ms:  Wait starts
200ms: Deepgram sends final transcript → accumulatedTranscript updated
1000ms: Wait ends → getFullTranscript() returns complete transcript ✅
```

### **Scenario 2: No transcript after wait**
```
0ms:  Wait starts
1000ms: Wait ends → getFullTranscript() still empty
→ Shows "No speech was detected" message
```

## 🔧 **Current Implementation:**

**Note:** The constant `FINALIZATION_WAIT` is mentioned in documentation but **not actually defined** in the code. The code uses hardcoded `1000` milliseconds.

**Recommended:** Define it as a constant for better maintainability:

```javascript
const FINALIZATION_WAIT = 1000;  // 1 second

// Then use it:
await new Promise(resolve => setTimeout(resolve, FINALIZATION_WAIT));
setTimeout(() => { ... }, FINALIZATION_WAIT);
```

## ✅ **Benefits:**

1. **Prevents data loss:** Ensures final words aren't missed
2. **Handles edge cases:** Works even if user clicks "Done" immediately
3. **Network resilience:** Accounts for network delays
4. **User experience:** Smooth transition without missing words

## ⚠️ **Important Notes:**

- This wait **does NOT** delay the UI unnecessarily
- It only waits if **no transcript is found initially**
- If transcript already exists, no wait occurs
- The wait is **asynchronous** (doesn't block the UI)

---

## 📋 **Summary:**

`FINALIZATION_WAIT = 1000ms` (1 second) is the time the system waits for Deepgram to send the final transcript before submitting the answer. This ensures complete transcription capture, especially when users finish speaking and immediately click "Done" or move to review phase.

