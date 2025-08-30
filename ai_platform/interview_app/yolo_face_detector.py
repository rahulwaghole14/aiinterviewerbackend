
# interview_app/yolo_face_detector.py

# Make imports optional
try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    YOLO = None

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    cv2 = None

# Load the YOLOv8 model specialized for face detection.
# You can also use the generic 'yolov8n.pt' if a specialized one isn't available,
# but a face-specific model is generally better.
# Let's use the generic one for simplicity as it's already part of the project.
if YOLO_AVAILABLE:
    try:
        model = YOLO('yolov8n.pt')
    except Exception as e:
        print(f"Warning: Could not load YOLO model: {e}")
        model = None
else:
    model = None

def detect_face_with_yolo(image_input):
    """
    Takes a file path or numpy array and returns YOLO detection results.
    """
    if not CV2_AVAILABLE or not YOLO_AVAILABLE or model is None:
        print("Warning: CV2 or YOLO not available - face detection disabled")
        # Return a mock result object
        class MockResult:
            def __init__(self):
                self.boxes = []
        return MockResult()
    
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
        print(f"Error in face detection: {e}")
        # Return a mock result object
        class MockResult:
            def __init__(self):
                self.boxes = []
        return MockResult()