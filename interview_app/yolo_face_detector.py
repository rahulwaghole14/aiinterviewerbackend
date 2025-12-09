
# interview_app/yolo_face_detector.py
# Safe import with fallback if ultralytics is not installed
try:
    from ultralytics import YOLO
    import cv2
    # Load the YOLOv8 model specialized for face detection.
    # You can also use the generic 'yolov8n.pt' if a specialized one isn't available,
    # but a face-specific model is generally better.
    # Let's use the generic one for simplicity as it's already part of the project.
    try:
        model = YOLO('yolov8n.pt')
        YOLO_AVAILABLE = True
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