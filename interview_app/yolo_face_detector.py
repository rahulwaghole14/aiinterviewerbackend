# interview_app/yolo_face_detector.py
# Using PyTorch/ultralytics for YOLOv8m.pt model
# LAZY LOADING: Model loading happens only when detect_face_with_yolo() is called
import os
import numpy as np
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
_face_model = None
_object_model = None
_YOLO_AVAILABLE = None
_TORCH_AVAILABLE = None  # None = not checked yet, True/False = checked

# YOLOv8 detection thresholds
_FACE_CONFIDENCE_THRESHOLD = 0.50  # Higher threshold for face detection
_OBJECT_CONFIDENCE_THRESHOLD = 0.30  # Lower threshold for object detection
_IOU_THRESHOLD = 0.80

# Model configurations - Use yolov8n.pt for both ID verification and interview
_FACE_MODEL_CONFIG = {
    'model_file': 'yolov8n.pt',
    'img_size': 640,
    'conf_threshold': _FACE_CONFIDENCE_THRESHOLD,
    'iou_threshold': _IOU_THRESHOLD
}

_OBJECT_MODEL_CONFIG = {
    'model_file': 'yolov8n.pt',
    'img_size': 640,
    'conf_threshold': _OBJECT_CONFIDENCE_THRESHOLD,
    'iou_threshold': _IOU_THRESHOLD
}

class YOLOResult:
    """Mock YOLO result object to maintain compatibility with existing code"""
    def __init__(self, boxes):
        self.boxes = boxes

def _load_pytorch_model(model_config):
    """
    Lazy load YOLOv8n PyTorch model for both ID verification and interview.
    This prevents worker timeout during Django startup.
    Uses local model files for better performance.
    """
    global _face_model, _object_model, _YOLO_AVAILABLE, _TORCH_AVAILABLE
    
    # If already checked, return cached result
    if _YOLO_AVAILABLE is not None:
        return _YOLO_AVAILABLE
    
    # First, try to import torch (required for PyTorch models)
    if _TORCH_AVAILABLE is None:
        try:
            import torch
            _TORCH_AVAILABLE = True
            print("✅ torch imported successfully (lazy load)")
        except ImportError as e:
            print(f"ℹ️ torch not installed; YOLOv8 detection unavailable: {e}")
            print("ℹ️ Install with: pip install torch torchvision")
            _TORCH_AVAILABLE = False
            _YOLO_AVAILABLE = False
            return False
        except Exception as e:
            print(f"⚠️ Error importing torch: {e}")
            _TORCH_AVAILABLE = False
            _YOLO_AVAILABLE = False
            return False
    
    if not _TORCH_AVAILABLE:
        _YOLO_AVAILABLE = False
        return False
    
    import torch
    
    try:
        # Load yolov8n.pt model (same for both face and object detection)
        model_path = Path(settings.BASE_DIR) / model_config['model_file']
        print(f"🔍 Loading {model_config['model_file']} from: {model_path}")
        print(f"🔍 BASE_DIR: {settings.BASE_DIR}")
        print(f"🔍 Model path exists: {model_path.exists()}")
        
        if model_path.exists():
            # Load local model file
            model = torch.hub.load('ultralytics/yolov8', 'custom', path=str(model_path), pretrained=True)
            print(f"✅ {model_config['model_file']} loaded from local file: {model_path}")
        else:
            # Fallback: download model
            print(f"⚠️ {model_config['model_file']} not found at {model_path}, downloading from internet...")
            model = torch.hub.load('ultralytics/yolov8', model_config['model_file'].replace('.pt', ''), pretrained=True)
            print(f"✅ {model_config['model_file']} downloaded and loaded")
        
        # Set model to evaluation mode and configure
        model.eval()
        model.conf = model_config['conf_threshold']
        model.iou = model_config['iou_threshold']
        
        # Since both models use the same file, store in both globals
        if model_config['model_file'] == 'yolov8n.pt':
            _face_model = model
            _object_model = model
            print(f"✅ YOLOv8n model configured for both ID verification and interview: imgsz={model_config['img_size']}, conf={model_config['conf_threshold']}")
        
        _YOLO_AVAILABLE = True
        return True
        
    except Exception as e:
        print(f"⚠️ Could not load {model_config['model_file']}: {e}")
        import traceback
        traceback.print_exc()
        _YOLO_AVAILABLE = False
        return False

def _load_face_model():
    """Load face detection model"""
    return _load_pytorch_model(_FACE_MODEL_CONFIG)

def _load_object_model():
    """Load object detection model"""
    return _load_pytorch_model(_OBJECT_MODEL_CONFIG)

def detect_face_with_yolo(image_input):
    """
    Single person detection for ID verification using yolov8n.pt (imgsz=640).
    Ensures only one person is detected for ID verification.
    Returns YOLO detection results with person-specific configuration.
    Falls back gracefully if YOLO is not available.
    Uses Haar cascade as final fallback for face detection.
    Always returns a list for consistency.
    
    Model is loaded lazily on first call to prevent startup timeout.
    """
    global _face_model, _YOLO_AVAILABLE
    
    if not CV2_AVAILABLE or cv2 is None:
        raise ValueError("OpenCV not available. Image processing features are disabled.")
    
    if isinstance(image_input, str):
        img = cv2.imread(image_input)
    else:
        img = image_input

    if img is None:
        raise ValueError("Image not found or invalid format.")

    original_shape = img.shape
    
    # Lazy load face model on first use
    if _YOLO_AVAILABLE is None:
        _load_face_model()
    
    # Try person detection model first if available
    if _YOLO_AVAILABLE and _face_model is not None:
        try:
            print(f"🔍 Running single person detection with yolov8n.pt (imgsz=640) for ID verification")
            
            # Run inference with person model (PyTorch handles preprocessing internally)
            results = _face_model(img, imgsz=640)
            
            print(f"🔍 Person model detected {len(results[0])} objects")
            
            # Filter for only person detections and ensure single person
            if len(results[0]) > 0 and len(results[0].boxes) > 0:
                # Get detected classes and boxes
                boxes = results[0].boxes
                labels = [results[0].names[int(cls)] for cls in boxes.cls]
                
                # Count only person detections
                person_count = labels.count('person')
                
                if person_count == 1:
                    print(f"✅ Single person detected for ID verification - SUCCESS")
                    return results
                elif person_count == 0:
                    print("⚠️ No person detected, falling back to Haar cascade")
                else:
                    print(f"⚠️ Multiple persons detected ({person_count}), ID verification requires single person")
                    # For multiple persons, still return results but let calling code handle validation
                    return results
            else:
                print("⚠️ Person model detected 0 persons, falling back to Haar cascade")
        except Exception as e:
            print(f"⚠️ Person model detection error: {e}")
            import traceback
            traceback.print_exc()
    
    # Fallback to Haar cascade for face detection
    print("🔄 Using Haar cascade fallback for face detection")
    try:
        # Load Haar cascade classifier
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        face_cascade = cv2.CascadeClassifier(cascade_path)
        
        if face_cascade.empty():
            print("⚠️ Haar cascade not available")
            empty_obj = type('obj', (object,), {'boxes': []})()
            return [empty_obj]
        
        # Convert to grayscale for face detection
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        
        print(f"🔍 Haar cascade detected {len(faces)} faces")
        
        # Convert Haar cascade format to YOLO-compatible format
        class MockBox:
            def __init__(self, x, y, w, h):
                # Haar returns (x, y, w, h), convert to (x1, y1, x2, y2)
                self.xyxy = np.array([[x, y, x + w, y + h]], dtype=np.float32)
                self.conf = 1.0
                self.cls = 0  # Face class
        
        class MockBoxes:
            def __init__(self, boxes_list):
                self.boxes_list = boxes_list
            
            def __len__(self):
                return len(self.boxes_list)
            
            def __getitem__(self, idx):
                return self.boxes_list[idx]
        
        boxes_list = [MockBox(x, y, w, h) for (x, y, w, h) in faces]
        boxes = MockBoxes(boxes_list)
        
        result = YOLOResult(boxes)
        return [result]
        
    except Exception as e:
        print(f"⚠️ Haar cascade detection error: {e}")
        import traceback
        traceback.print_exc()
        # Return empty results on error as a list
        empty_obj = type('obj', (object,), {'boxes': []})()
        return [empty_obj]

def detect_objects_with_yolo(image_input):
    """
    Object detection for proctoring warnings using yolov8n.pt (imgsz=640).
    Detects: person, cell phone, mobile phone for proctoring warnings.
    Uses the same model as ID verification for consistency.
    Returns YOLO detection results with object-specific configuration.
    Falls back gracefully if YOLO is not available.
    Always returns a list for consistency.
    
    Model is loaded lazily on first call to prevent startup timeout.
    """
    global _object_model, _YOLO_AVAILABLE
    
    if not CV2_AVAILABLE or cv2 is None:
        raise ValueError("OpenCV not available. Image processing features are disabled.")
    
    if isinstance(image_input, str):
        img = cv2.imread(image_input)
    else:
        img = image_input

    if img is None:
        raise ValueError("Image not found or invalid format.")

    original_shape = img.shape
    
    # Lazy load object model on first use
    if _YOLO_AVAILABLE is None:
        _load_object_model()
    
    # Try object detection model if available
    if _YOLO_AVAILABLE and _object_model is not None:
        try:
            print(f"🔍 Running object detection with yolov8n.pt (imgsz=640) for interview proctoring")
            
            # Run inference with object model (PyTorch handles preprocessing internally)
            results = _object_model(img, imgsz=640)
            
            print(f"🔍 Object model detected {len(results[0])} objects")
            
            # If we got results, return them
            if len(results[0]) > 0:
                return results
            else:
                print("⚠️ Object model detected 0 objects")
                return []
        except Exception as e:
            print(f"⚠️ Object model detection error: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    print("⚠️ Object detection model not available")
    return []
