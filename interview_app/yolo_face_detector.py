
# interview_app/yolo_face_detector.py
# Safe import with fallback if ultralytics is not installed
import os
from django.conf import settings

try:
    from ultralytics import YOLO
    import cv2
    # Load the YOLOv8 model specialized for face detection.
    # Use absolute path from BASE_DIR to ensure it works in production
    # Path: BASE_DIR/yolov8n.pt
    try:
        model_path = os.path.join(settings.BASE_DIR, 'yolov8n.pt')
        if os.path.exists(model_path):
            model = YOLO(model_path)
            print(f"✅ YOLOv8 model loaded from: {model_path}")
            YOLO_AVAILABLE = True
        else:
            # Fallback: try current directory
            fallback_path = 'yolov8n.pt'
            if os.path.exists(fallback_path):
                model = YOLO(fallback_path)
                print(f"✅ YOLOv8 model loaded from fallback path: {fallback_path}")
                YOLO_AVAILABLE = True
            else:
                print(f"⚠️ YOLOv8 model not found at {model_path} or {fallback_path}")
                model = None
                YOLO_AVAILABLE = False
    except Exception as e:
        print(f"⚠️ Could not load YOLOv8 model: {e}")
        model = None
        YOLO_AVAILABLE = False
except ImportError:
    print("ℹ️ ultralytics not installed; YOLOv8 face detection unavailable")
    model = None
    YOLO_AVAILABLE = False
    import cv2  # cv2 might still be needed for image processing

def detect_face_with_yolo(image_input):
    """
    Takes a file path or numpy array and returns YOLO detection results.
    Falls back gracefully if YOLOv8 is not available.
    """
    if not YOLO_AVAILABLE or model is None:
        # Return empty results if YOLO is not available
        return type('obj', (object,), {'boxes': []})()
    
    if isinstance(image_input, str):
        img = cv2.imread(image_input)
    else:
        img = image_input

    if img is None:
        raise ValueError("Image not found or invalid format.")

    try:
        results = model(img)
        return results
    except Exception as e:
        print(f"⚠️ YOLO detection error: {e}")
        # Return empty results on error
        return type('obj', (object,), {'boxes': []})()