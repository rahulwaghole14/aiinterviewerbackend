
# interview_app/yolo_face_detector.py
# Safe import with fallback if ultralytics is not installed
import os
from pathlib import Path
from django.conf import settings

try:
    from ultralytics import YOLO
    import cv2
    # Load the YOLOv8 model specialized for face detection.
    # Use absolute path from BASE_DIR to ensure it works in production
    # Path: BASE_DIR/yolov8n.pt (project root: aiinterviewerbackend/yolov8n.pt)
    try:
        # Use Path object for better cross-platform compatibility
        model_path = Path(settings.BASE_DIR) / 'yolov8n.pt'
        print(f"🔍 Looking for YOLOv8 model at: {model_path}")
        print(f"🔍 BASE_DIR: {settings.BASE_DIR}")
        print(f"🔍 Model path exists: {model_path.exists()}")
        
        if model_path.exists():
            model = YOLO(str(model_path))
            print(f"✅ YOLOv8 model loaded successfully from: {model_path}")
            YOLO_AVAILABLE = True
        else:
            # Fallback: try current directory
            fallback_path = Path('yolov8n.pt')
            print(f"🔍 Trying fallback path: {fallback_path} (exists: {fallback_path.exists()})")
            if fallback_path.exists():
                model = YOLO(str(fallback_path))
                print(f"✅ YOLOv8 model loaded from fallback path: {fallback_path}")
                YOLO_AVAILABLE = True
            else:
                print(f"⚠️ YOLOv8 model not found at {model_path} or {fallback_path}")
                print(f"⚠️ Please ensure yolov8n.pt is in the project root directory")
                model = None
                YOLO_AVAILABLE = False
    except Exception as e:
        print(f"⚠️ Could not load YOLOv8 model: {e}")
        import traceback
        traceback.print_exc()
        model = None
        YOLO_AVAILABLE = False
except ImportError:
    print("ℹ️ ultralytics not installed; YOLOv8 face detection unavailable")
    print("ℹ️ Install with: pip install ultralytics==8.1.28")
    model = None
    YOLO_AVAILABLE = False
    import cv2  # cv2 might still be needed for image processing

def detect_face_with_yolo(image_input):
    """
    Takes a file path or numpy array and returns YOLO detection results.
    Falls back gracefully if YOLOv8 is not available.
    Always returns a list for consistency.
    """
    if not YOLO_AVAILABLE or model is None:
        # Return empty results as a list if YOLO is not available
        empty_obj = type('obj', (object,), {'boxes': []})()
        return [empty_obj]
    
    if isinstance(image_input, str):
        img = cv2.imread(image_input)
    else:
        img = image_input

    if img is None:
        raise ValueError("Image not found or invalid format.")

    try:
        results = model(img)
        # Ensure results is always a list
        if not isinstance(results, list):
            # If YOLO returns a single result object, wrap it in a list
            return [results] if results else [type('obj', (object,), {'boxes': []})()]
        return results
    except Exception as e:
        print(f"⚠️ YOLO detection error: {e}")
        # Return empty results on error as a list
        empty_obj = type('obj', (object,), {'boxes': []})()
        return [empty_obj]