
# interview_app/yolo_face_detector.py
# Safe import with fallback if ultralytics is not installed
# LAZY LOADING: Model is loaded only when detect_face_with_yolo() is called, not at import time
# This prevents worker timeout during Django startup
import os
from pathlib import Path
from django.conf import settings

# Global variables for lazy loading
_model = None
_YOLO_AVAILABLE = None
_YOLO_CLASS_AVAILABLE = False

try:
    from ultralytics import YOLO
    import cv2
    _YOLO_CLASS_AVAILABLE = True
except ImportError:
    print("ℹ️ ultralytics not installed; YOLOv8 face detection unavailable")
    print("ℹ️ Install with: pip install ultralytics==8.1.28")
    _YOLO_CLASS_AVAILABLE = False
    import cv2  # cv2 might still be needed for image processing

def _load_yolo_model():
    """
    Lazy load YOLOv8 model only when needed.
    This prevents worker timeout during Django startup.
    """
    global _model, _YOLO_AVAILABLE
    
    # If already checked, return cached result
    if _YOLO_AVAILABLE is not None:
        return _YOLO_AVAILABLE
    
    if not _YOLO_CLASS_AVAILABLE:
        _YOLO_AVAILABLE = False
        return False
    
    try:
        # Use Path object for better cross-platform compatibility
        model_path = Path(settings.BASE_DIR) / 'yolov8n.pt'
        print(f"🔍 Loading YOLOv8 model from: {model_path}")
        print(f"🔍 BASE_DIR: {settings.BASE_DIR}")
        print(f"🔍 Model path exists: {model_path.exists()}")
        
        if model_path.exists():
            _model = YOLO(str(model_path))
            print(f"✅ YOLOv8 model loaded successfully from: {model_path}")
            _YOLO_AVAILABLE = True
            return True
        else:
            # Fallback: try current directory
            fallback_path = Path('yolov8n.pt')
            print(f"🔍 Trying fallback path: {fallback_path} (exists: {fallback_path.exists()})")
            if fallback_path.exists():
                _model = YOLO(str(fallback_path))
                print(f"✅ YOLOv8 model loaded from fallback path: {fallback_path}")
                _YOLO_AVAILABLE = True
                return True
            else:
                print(f"⚠️ YOLOv8 model not found at {model_path} or {fallback_path}")
                print(f"⚠️ Please ensure yolov8n.pt is in the project root directory")
                _model = None
                _YOLO_AVAILABLE = False
                return False
    except Exception as e:
        print(f"⚠️ Could not load YOLOv8 model: {e}")
        import traceback
        traceback.print_exc()
        _model = None
        _YOLO_AVAILABLE = False
        return False

def detect_face_with_yolo(image_input):
    """
    Takes a file path or numpy array and returns YOLO detection results.
    Falls back gracefully if YOLOv8 is not available.
    Always returns a list for consistency.
    
    Model is loaded lazily on first call to prevent startup timeout.
    """
    global _model, _YOLO_AVAILABLE
    
    # Lazy load model on first use
    if _YOLO_AVAILABLE is None:
        _load_yolo_model()
    
    if not _YOLO_AVAILABLE or _model is None:
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
        results = _model(img)
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