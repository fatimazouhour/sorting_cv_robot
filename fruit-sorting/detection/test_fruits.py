
import cv2
from importlib import import_module

try:
    YOLO = import_module("ultralytics").YOLO
except ModuleNotFoundError as exc:
    if exc.name != "ultralytics":
        raise
    raise ModuleNotFoundError(
        "The 'ultralytics' package is not installed. Install it with "
        "'python -m pip install ultralytics'."
    ) from exc

CAMERA_URL = "http://192.168.137.188:81/stream"

# Pretrained model: detects common fruit types, but not ripeness reliably
model = YOLO("yolo26n.pt")

cap = cv2.VideoCapture(CAMERA_URL)

if not cap.isOpened():
    raise RuntimeError(
        "Cannot connect to ESP32-CAM. Check that your laptop hotspot "
        "is active and the camera IP is correct."
    )

print("Camera connected. Press Q to quit.")

while True:
    ret, frame = cap.read()

    if not ret:
        print("Failed to read camera frame.")
        break

    results = model.predict(
        source=frame,
        device="cpu",
        imgsz=416,
        conf=0.25,
        verbose=False
    )

    annotated = results[0].plot()
    cv2.imshow("Fruit Detection - YOLO26n", annotated)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
