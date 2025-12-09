# interview_app/yolo_face_detector.py
# Using ONNX Runtime instead of ultralytics for lower memory usage
# ONNX Runtime is much lighter (~50MB) compared to PyTorch/ultralytics (~500MB+)
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
_model = None
_onnx_session = None
_YOLO_AVAILABLE = None
_ONNX_AVAILABLE = None  # None = not checked yet, True/False = checked
_input_name = None
_output_names = None

# YOLOv8 input/output details
_MODEL_INPUT_SIZE = 640  # YOLOv8n expects 640x640 input
_CONFIDENCE_THRESHOLD = 0.25
_IOU_THRESHOLD = 0.45

class YOLOResult:
    """Mock YOLO result object to maintain compatibility with existing code"""
    def __init__(self, boxes):
        self.boxes = boxes

def _load_onnx_model():
    """
    Lazy load YOLOv8 ONNX model only when needed.
    This prevents worker timeout during Django startup.
    ONNX Runtime is much lighter than PyTorch/ultralytics.
    """
    global _onnx_session, _YOLO_AVAILABLE, _ONNX_AVAILABLE, _input_name, _output_names
    
    # If already checked, return cached result
    if _YOLO_AVAILABLE is not None:
        return _YOLO_AVAILABLE
    
    # First, try to import onnxruntime (lightweight, ~50MB)
    if _ONNX_AVAILABLE is None:
        try:
            import onnxruntime as ort
            _ONNX_AVAILABLE = True
            print("✅ onnxruntime imported successfully (lazy load)")
        except ImportError as e:
            print(f"ℹ️ onnxruntime not installed; YOLOv8 face detection unavailable: {e}")
            print("ℹ️ Install with: pip install onnxruntime")
            _ONNX_AVAILABLE = False
            _YOLO_AVAILABLE = False
            return False
        except Exception as e:
            print(f"⚠️ Error importing onnxruntime: {e}")
            _ONNX_AVAILABLE = False
            _YOLO_AVAILABLE = False
            return False
    
    if not _ONNX_AVAILABLE:
        _YOLO_AVAILABLE = False
        return False
    
    import onnxruntime as ort
    
    try:
        # Use Path object for better cross-platform compatibility
        # Look for .onnx file first, then fallback to .pt (for conversion)
        model_path = Path(settings.BASE_DIR) / 'yolov8n.onnx'
        print(f"🔍 Loading YOLOv8 ONNX model from: {model_path}")
        print(f"🔍 BASE_DIR: {settings.BASE_DIR}")
        print(f"🔍 Model path exists: {model_path.exists()}")
        
        if not model_path.exists():
            # Fallback: try current directory
            fallback_path = Path('yolov8n.onnx')
            print(f"🔍 Trying fallback path: {fallback_path} (exists: {fallback_path.exists()})")
            if fallback_path.exists():
                model_path = fallback_path
            else:
                print(f"⚠️ YOLOv8 ONNX model not found at {Path(settings.BASE_DIR) / 'yolov8n.onnx'} or {fallback_path}")
                print(f"⚠️ Please ensure yolov8n.onnx is in the project root directory")
                print(f"ℹ️ You can convert yolov8n.pt to .onnx using: yolo export model=yolov8n.pt format=onnx")
                _onnx_session = None
                _YOLO_AVAILABLE = False
                return False
        
        # Create ONNX Runtime session
        # Use CPU provider for compatibility (no CUDA required)
        providers = ['CPUExecutionProvider']
        _onnx_session = ort.InferenceSession(str(model_path), providers=providers)
        
        # Get input/output names
        _input_name = _onnx_session.get_inputs()[0].name
        _output_names = [output.name for output in _onnx_session.get_outputs()]
        
        print(f"✅ YOLOv8 ONNX model loaded successfully from: {model_path}")
        print(f"   Input: {_input_name}, Outputs: {_output_names}")
        print(f"⚠️ NOTE: Standard YOLOv8n (COCO) detects 'person' class, not faces specifically.")
        print(f"⚠️ For face detection, you may need a face-specific YOLOv8 model.")
        _YOLO_AVAILABLE = True
        return True
        
    except Exception as e:
        print(f"⚠️ Could not load YOLOv8 ONNX model: {e}")
        import traceback
        traceback.print_exc()
        _onnx_session = None
        _YOLO_AVAILABLE = False
        return False

def _preprocess_image(img, input_size=640):
    """Preprocess image for YOLOv8 ONNX model"""
    # Resize image to model input size (640x640)
    img_resized = cv2.resize(img, (input_size, input_size))
    # Convert BGR to RGB
    img_rgb = cv2.cvtColor(img_resized, cv2.COLOR_BGR2RGB)
    # Normalize to [0, 1]
    img_normalized = img_rgb.astype(np.float32) / 255.0
    # Transpose to CHW format (channels, height, width)
    img_transposed = np.transpose(img_normalized, (2, 0, 1))
    # Add batch dimension
    img_batch = np.expand_dims(img_transposed, axis=0)
    return img_batch

def _postprocess_output(outputs, img_shape, input_size=640, conf_threshold=0.25, iou_threshold=0.45):
    """
    Post-process ONNX model outputs to get bounding boxes.
    YOLOv8 ONNX output format: [batch, features, anchors] = [1, 84, 8400]
    where 84 = 4 (bbox coords) + 80 (class scores), 8400 = anchor points
    """
    if len(outputs) == 0:
        return []
    
    predictions = outputs[0]  # Shape: [1, 84, 8400] for YOLOv8n
    
    # Handle different output shapes
    if len(predictions.shape) == 3:
        # Standard YOLOv8 format: [batch, features, anchors]
        # Transpose to [anchors, features] for easier processing
        predictions = predictions[0].transpose(1, 0)  # [8400, 84]
    elif len(predictions.shape) == 2:
        # Already in [anchors, features] format
        predictions = predictions
    else:
        print(f"⚠️ Unexpected output shape: {predictions.shape}")
        return []
    
    # Extract boxes and scores
    boxes = []
    scores = []
    
    # YOLOv8 format: [x_center, y_center, width, height, class_scores...]
    # Coordinates are normalized (0-1) relative to input_size
    for pred in predictions:
        if len(pred) < 5:
            continue
        
        # Get box coordinates (normalized, center format)
        x_center, y_center, width, height = pred[0:4]
        
        # Get class scores (rest of the array)
        class_scores = pred[4:]
        max_score = np.max(class_scores)
        max_class = np.argmax(class_scores)
        
        # Filter by confidence threshold
        if max_score < conf_threshold:
            continue
        
        # Convert from normalized center coordinates to corner coordinates
        # Scale to original image size
        img_h, img_w = img_shape[:2]
        scale_x = img_w / input_size
        scale_y = img_h / input_size
        
        # Convert center format to corner format
        x1 = (x_center - width / 2) * input_size * scale_x
        y1 = (y_center - height / 2) * input_size * scale_y
        x2 = (x_center + width / 2) * input_size * scale_x
        y2 = (y_center + height / 2) * input_size * scale_y
        
        # Ensure coordinates are within image bounds
        x1 = max(0, min(x1, img_w))
        y1 = max(0, min(y1, img_h))
        x2 = max(0, min(x2, img_w))
        y2 = max(0, min(y2, img_h))
        
        boxes.append([x1, y1, x2, y2, max_score, max_class])
        scores.append(max_score)
    
    # Apply Non-Maximum Suppression (NMS)
    if len(boxes) == 0:
        return []
    
    boxes_array = np.array(boxes, dtype=np.float32)
    scores_array = np.array(scores, dtype=np.float32)
    
    # Use OpenCV's NMS
    try:
        indices = cv2.dnn.NMSBoxes(
            boxes_array[:, :4].tolist(),
            scores_array.tolist(),
            conf_threshold,
            iou_threshold
        )
        
        if indices is None or len(indices) == 0:
            return []
        
        # Handle both numpy array and list formats
        if isinstance(indices, np.ndarray):
            indices = indices.flatten()
        else:
            indices = [int(i) for i in indices]
    except Exception as e:
        print(f"⚠️ NMS error: {e}")
        return []
    
    # Create mock boxes object compatible with ultralytics format
    class MockBox:
        def __init__(self, box_data):
            self.data = box_data  # [x1, y1, x2, y2, conf, cls]
            self.xyxy = np.array([box_data[:4]], dtype=np.float32)  # Bounding box coordinates
            self.conf = float(box_data[4])  # Confidence
            self.cls = int(box_data[5])  # Class
    
    class MockBoxes:
        def __init__(self, boxes_list):
            self.boxes_list = boxes_list
        
        def __len__(self):
            return len(self.boxes_list)
        
        def __getitem__(self, idx):
            return self.boxes_list[idx]
    
    filtered_boxes = MockBoxes([MockBox(boxes_array[i]) for i in indices])
    
    return filtered_boxes

def detect_face_with_yolo(image_input):
    """
    Takes a file path or numpy array and returns YOLO detection results.
    Falls back gracefully if YOLOv8 ONNX is not available.
    Uses Haar cascade as fallback for face detection.
    Always returns a list for consistency.
    
    Model is loaded lazily on first call to prevent startup timeout.
    """
    global _onnx_session, _YOLO_AVAILABLE, _input_name, _output_names
    
    if not CV2_AVAILABLE or cv2 is None:
        raise ValueError("OpenCV not available. Image processing features are disabled.")
    
    if isinstance(image_input, str):
        img = cv2.imread(image_input)
    else:
        img = image_input

    if img is None:
        raise ValueError("Image not found or invalid format.")
    
    original_shape = img.shape
    
    # Lazy load model on first use
    if _YOLO_AVAILABLE is None:
        _load_onnx_model()
    
    # Try ONNX YOLO first if available
    if _YOLO_AVAILABLE and _onnx_session is not None:
        try:
            # Preprocess image
            img_preprocessed = _preprocess_image(img, _MODEL_INPUT_SIZE)
            print(f"🔍 Preprocessed image shape: {img_preprocessed.shape}, original: {original_shape}")
            
            # Run inference
            outputs = _onnx_session.run(_output_names, {_input_name: img_preprocessed})
            print(f"🔍 ONNX output shapes: {[o.shape for o in outputs]}")
            
            # Post-process outputs
            boxes = _postprocess_output(
                outputs,
                original_shape,
                _MODEL_INPUT_SIZE,
                _CONFIDENCE_THRESHOLD,
                _IOU_THRESHOLD
            )
            
            print(f"🔍 Detected {len(boxes)} boxes after post-processing")
            
            # If we got results, return them
            if len(boxes) > 0:
                result = YOLOResult(boxes)
                return [result]
            else:
                print("⚠️ YOLO detected 0 boxes, falling back to Haar cascade")
        except Exception as e:
            print(f"⚠️ YOLO ONNX detection error: {e}")
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
