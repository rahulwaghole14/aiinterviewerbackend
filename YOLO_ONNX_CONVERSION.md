# YOLOv8 ONNX Conversion Guide

## Why ONNX Runtime?

We've switched from `ultralytics` (PyTorch-based) to `onnxruntime` for YOLOv8 inference because:

- **Much lower memory usage**: ~50MB vs ~500MB+ for PyTorch
- **Faster startup**: No heavy PyTorch/CUDA dependencies
- **Better for cloud deployment**: Works on CPU-only servers (like Render)
- **Same accuracy**: ONNX is just a different format, not a different model

## Converting yolov8n.pt to yolov8n.onnx

You need to convert your existing `yolov8n.pt` model to ONNX format. Here's how:

### Option 1: Using ultralytics CLI (Recommended)

If you have `ultralytics` installed locally:

```bash
# Install ultralytics if not already installed
pip install ultralytics

# Convert the model
yolo export model=yolov8n.pt format=onnx imgsz=640
```

This will create `yolov8n.onnx` in the same directory.

### Option 2: Using Python script

Create a conversion script:

```python
from ultralytics import YOLO

# Load the PyTorch model
model = YOLO('yolov8n.pt')

# Export to ONNX
model.export(format='onnx', imgsz=640)
```

### Option 3: Download pre-converted model

You can also download a pre-converted ONNX model from:
- [ONNX Model Zoo](https://github.com/onnx/models)
- Or use ultralytics export functionality

## File Locations

After conversion, place the `yolov8n.onnx` file in:

```
aiinterviewerbackend/yolov8n.onnx
```

This is the project root directory (same location as `yolov8n.pt`).

## Model Paths

The code looks for the model in this order:
1. `BASE_DIR/yolov8n.onnx` (project root)
2. `./yolov8n.onnx` (current directory fallback)

## Verification

After placing `yolov8n.onnx` in the project root, the application will:
- Load the ONNX model lazily (only when needed)
- Use much less memory than PyTorch
- Work on CPU-only servers

## Notes

- The ONNX model uses the same weights as the PyTorch model, just in a different format
- Face detection accuracy remains the same
- Proctoring features (person detection, phone detection) work the same way
- The model expects 640x640 input images (automatically resized)

## Troubleshooting

If you see errors about the model not being found:
1. Ensure `yolov8n.onnx` exists in the project root
2. Check file permissions
3. Verify the file is not corrupted (should be ~6-7MB)

If conversion fails:
- Make sure you have `ultralytics` installed: `pip install ultralytics`
- Try using a different YOLOv8 model variant (yolov8s, yolov8m, etc.)
- Check ultralytics documentation for latest export options

