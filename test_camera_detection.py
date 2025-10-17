import cv2
import sys

print("🔍 Testing camera detection...")

# Test camera detection
for i in range(5):
    print(f"\n🎥 Testing camera {i}...")
    cap = cv2.VideoCapture(i)
    
    if cap.isOpened():
        ret, frame = cap.read()
        if ret and frame is not None:
            print(f"✅ Camera {i}: SUCCESS - {frame.shape}")
            cap.release()
            break
        else:
            print(f"❌ Camera {i}: Opened but can't read frames")
            cap.release()
    else:
        print(f"❌ Camera {i}: Cannot open")

print("\n🔍 Checking OpenCV version...")
print(f"OpenCV version: {cv2.__version__}")

print("\n🔍 Checking available backends...")
backends = [
    cv2.CAP_DSHOW,
    cv2.CAP_MSMF,
    cv2.CAP_ANY,
    cv2.CAP_V4L2,
    cv2.CAP_GSTREAMER
]

backend_names = ["DirectShow", "Microsoft Media Foundation", "Any", "Video4Linux", "GStreamer"]

for backend, name in zip(backends, backend_names):
    try:
        cap = cv2.VideoCapture(0, backend)
        if cap.isOpened():
            print(f"✅ {name}: Available")
            cap.release()
        else:
            print(f"❌ {name}: Not available")
    except Exception as e:
        print(f"❌ {name}: Error - {e}")

print("\n🔍 Testing DirectShow specifically...")
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
if cap.isOpened():
    print("✅ DirectShow backend works!")
    ret, frame = cap.read()
    if ret:
        print(f"✅ Frame captured: {frame.shape}")
    else:
        print("❌ Cannot capture frame")
    cap.release()
else:
    print("❌ DirectShow backend failed")
