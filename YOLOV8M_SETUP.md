# YOLOv8m Model Setup Guide

This guide explains how to set up YOLOv8m (medium) model for identity verification and proctoring detection.

## Overview

The system has been upgraded from YOLOv8n (nano) to YOLOv8m (medium) for better detection accuracy. The medium model provides:
- Better accuracy for person detection
- Better phone detection
- Better multiple people detection
- More reliable identity verification

## Files Required

1. **yolov8m.pt** - PyTorch model file (source, for reference)
2. **yolov8m.onnx** - ONNX Runtime model file (used at runtime)

## Step 1: Download YOLOv8m Model

### Option A: Download Pre-trained Model
```bash
# Using ultralytics (if you have it installed)
pip install ultralytics
python -c "from ultralytics import YOLO; model = YOLO('yolov8m.pt'); print('Model downloaded')"
```

### Option B: Download Directly
Download from: https://github.com/ultralytics/assets/releases
- Look for `yolov8m.pt` in the releases

## Step 2: Convert yolov8m.pt to yolov8m.onnx

You need to convert the PyTorch model to ONNX format for runtime use:

```bash
# Install ultralytics if not already installed
pip install ultralytics

# Convert yolov8m.pt to yolov8m.onnx
yolo export model=yolov8m.pt format=onnx imgsz=640
```

Or using Python:
```python
from ultralytics import YOLO

# Load the model
model = YOLO('yolov8m.pt')

# Export to ONNX
model.export(format='onnx', imgsz=640)
```

This will create `yolov8m.onnx` in the same directory.

## Step 3: Add Files to Repository

Place both files in the **project root directory** (same level as `manage.py`):

```
aiinterviewerbackend/
├── manage.py
├── yolov8m.pt          ← Add this file
├── yolov8m.onnx        ← Add this file
├── Dockerfile
├── requirements.txt
└── ...
```

## Step 4: Commit and Push to GitHub

```bash
# Add the model files
git add yolov8m.pt yolov8m.onnx

# Commit
git commit -m "Add YOLOv8m model files (pt and onnx)"

# Push to repository
git push origin main
```

## Step 5: Verify Dockerfile

The Dockerfile has been updated to copy both files:
```dockerfile
COPY yolov8m.pt /app/yolov8m.pt || true
COPY yolov8m.onnx /app/yolov8m.onnx || true
```

## Where YOLOv8m is Used

1. **Identity Verification** (`yolo_face_detector.py`)
   - Detects person in ID verification frame
   - Used during interview setup phase

2. **Proctoring Detection** (`simple_real_camera.py`)
   - Phone detection
   - Multiple people detection
   - No person detection
   - Low concentration (motion-based)
   - Used during technical and coding interviews

3. **Browser Frame Detection** (`views.py` - `detect_yolo_browser_frame`)
   - Accepts browser camera frames
   - Runs YOLO detection server-side
   - Returns detection results

## Model Size Comparison

- **YOLOv8n (nano)**: ~6MB - Fast but less accurate
- **YOLOv8m (medium)**: ~50MB - Better accuracy, still fast
- **YOLOv8l (large)**: ~87MB - Best accuracy but slower

## Troubleshooting

### Model Not Found Error
If you see: `⚠️ YOLOv8m ONNX model not found`
- Ensure `yolov8m.onnx` is in the project root directory
- Check that the file was copied correctly in Docker build
- Verify file permissions

### Conversion Issues
If conversion fails:
- Ensure `ultralytics` package is installed: `pip install ultralytics`
- Check that `yolov8m.pt` is a valid YOLOv8 model file
- Try the Python conversion method instead of CLI

### Cloud Run Deployment
After pushing to GitHub:
- Cloud Build will automatically rebuild the Docker image
- The model files will be included in the container
- Check Cloud Run logs for: `✅ YOLOv8m ONNX model loaded successfully`

## Notes

- The `.pt` file is kept for reference and potential re-conversion
- The `.onnx` file is what's actually used at runtime (lighter, faster)
- Both files should be committed to the repository
- The Dockerfile uses `|| true` so the build won't fail if files are missing (but detection won't work)

