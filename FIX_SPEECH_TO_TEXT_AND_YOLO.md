# 🔧 Fix Speech-to-Text and YOLO Movement Detection

## Issues Identified

### 1. Speech-to-Text (Deepgram) Not Working
**Problem:**
- Portal connects directly to Deepgram API instead of Django proxy
- WebSocket URL might not work correctly on Cloud Run
- Deepgram API key might not be set in environment

**Solution:**
- Use Django WebSocket proxy (`/dg_ws`) instead of direct Deepgram connection
- Ensure Deepgram API key is set in Cloud Run environment variables
- Fix WebSocket URL construction for Cloud Run

### 2. YOLO Model Not Detecting Movements
**Problem:**
- YOLO model file (`yolov8n.onnx`) might not be present in Cloud Run container
- Movement detection logic might not be running
- Warnings might not be displayed in UI

**Solution:**
- Ensure YOLO model file is included in Docker image
- Verify `activate_yolo_proctoring()` is called when technical interview starts
- Check movement detection loop is running
- Ensure warnings are logged and displayed

---

## Fix 1: Speech-to-Text - Use Django Proxy

### Current Code (portal.html line 3120):
```javascript
const wsUrl = `wss://api.deepgram.com/v1/listen?token=${DEEPGRAM_API_KEY}&model=nova-3&language=en-IN&encoding=linear16&sample_rate=${sampleRate}&channels=1&interim_results=true&punctuate=false&smart_format=false`;
deepgramWS = new WebSocket(wsUrl);
```

### Fixed Code:
```javascript
// Use Django WebSocket proxy instead of direct Deepgram connection
const wsProto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
const wsUrl = `${wsProto}//${window.location.host}/dg_ws`;
deepgramWS = new WebSocket(wsUrl);
deepgramWS.binaryType = 'arraybuffer';

deepgramWS.onopen = () => {
    console.log('✅ Connected to Django Deepgram proxy');
    // Send config first
    const config = {
        sample_rate: sampleRate,
        model: 'nova-3',
        language: 'en-IN'
    };
    deepgramWS.send(JSON.stringify(config));
};

deepgramWS.onmessage = (event) => {
    handleDeepgramMessage(event);
};
```

---

## Fix 2: YOLO Model - Ensure Model File and Detection

### Step 1: Add YOLO Model to Dockerfile

```dockerfile
# Copy YOLO model file if it exists
COPY yolov8n.onnx /app/yolov8n.onnx
# Or download it during build
RUN if [ ! -f /app/yolov8n.onnx ]; then \
    echo "⚠️ YOLO model not found, will use Haar cascade fallback"; \
fi
```

### Step 2: Verify Movement Detection Loop

The movement detection should be running in `_capture_and_detect_loop()` method. Check if it's being called.

### Step 3: Check Warning Display

Ensure warnings are being fetched and displayed in the UI via `/status/` endpoint.

---

## Fix 3: Environment Variables

Ensure these are set in Cloud Run:

```bash
DEEPGRAM_API_KEY=your-deepgram-api-key
```

---

## Testing

### Test Speech-to-Text:
1. Start technical interview
2. Speak into microphone
3. Check browser console for WebSocket connection
4. Check for transcript appearing in UI

### Test YOLO Detection:
1. Start technical interview
2. Move around or have multiple people in frame
3. Check logs for YOLO detection messages
4. Check `/status/` endpoint for warnings
5. Verify warnings appear in UI

---

## Quick Fixes to Apply

1. **Update portal.html** - Change WebSocket URL to use Django proxy
2. **Add YOLO model to Dockerfile** - Include `yolov8n.onnx` file
3. **Verify environment variables** - Set `DEEPGRAM_API_KEY` in Cloud Run
4. **Check logs** - Verify YOLO is loading and detecting

---

**Last Updated**: 2025-01-27

