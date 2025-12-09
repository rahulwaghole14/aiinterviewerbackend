
# interview_app/yolo_face_detector.py
# Safe import with fallback if ultralytics is not installed
# LAZY LOADING: Both ultralytics import AND model loading happen only when detect_face_with_yolo() is called
# This prevents worker timeout during Django startup (PyTorch/ultralytics are very heavy to import)
import os
from pathlib import Path
from django.conf import settings

# Try to import cv2 at module level (lightweight, needed for image processing)
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    cv2 = None
    CV2_AVAILABLE = False
    print("⚠️ Warning: opencv-python not available. Image processing features will be disabled.")

# Global variables for lazy loading
_model = None
_YOLO_AVAILABLE = None
_YOLO_CLASS_AVAILABLE = None  # None = not checked yet, True/False = checked
_YOLO_CLASS = None  # Store the YOLO class once imported

def _load_yolo_model():
    """
    Lazy load YOLOv8 model only when needed.
    This prevents worker timeout during Django startup.
    Imports ultralytics and PyTorch only when actually needed.
    """
    global _model, _YOLO_AVAILABLE, _YOLO_CLASS_AVAILABLE, _YOLO_CLASS
    
    # If already checked, return cached result
    if _YOLO_AVAILABLE is not None:
        return _YOLO_AVAILABLE
    
    # First, try to import ultralytics (this will import PyTorch, which is heavy)
    if _YOLO_CLASS_AVAILABLE is None:
        try:
            from ultralytics import YOLO
            _YOLO_CLASS = YOLO  # Store the class for later use
            _YOLO_CLASS_AVAILABLE = True
            print("✅ ultralytics imported successfully (lazy load)")
        except ImportError as e:
            print(f"ℹ️ ultralytics not installed; YOLOv8 face detection unavailable: {e}")
            print("ℹ️ Install with: pip install ultralytics==8.1.28")
            _YOLO_CLASS_AVAILABLE = False
            _YOLO_AVAILABLE = False
            return False
        except Exception as e:
            print(f"⚠️ Error importing ultralytics: {e}")
            _YOLO_CLASS_AVAILABLE = False
            _YOLO_AVAILABLE = False
            return False
    
    if not _YOLO_CLASS_AVAILABLE or _YOLO_CLASS is None:
        _YOLO_AVAILABLE = False
        return False
    
    try:
        # Use Path object for better cross-platform compatibility
        model_path = Path(settings.BASE_DIR) / 'yolov8n.pt'
        print(f"🔍 Loading YOLOv8 model from: {model_path}")
        print(f"🔍 BASE_DIR: {settings.BASE_DIR}")
        print(f"🔍 Model path exists: {model_path.exists()}")
        
        if model_path.exists():
            _model = _YOLO_CLASS(str(model_path))
            print(f"✅ YOLOv8 model loaded successfully from: {model_path}")
            _YOLO_AVAILABLE = True
            return True
        else:
            # Fallback: try current directory
            fallback_path = Path('yolov8n.pt')
            print(f"🔍 Trying fallback path: {fallback_path} (exists: {fallback_path.exists()})")
            if fallback_path.exists():
                _model = _YOLO_CLASS(str(fallback_path))
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
    
    if not CV2_AVAILABLE or cv2 is None:
        raise ValueError("OpenCV not available. Image processing features are disabled.")
    
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