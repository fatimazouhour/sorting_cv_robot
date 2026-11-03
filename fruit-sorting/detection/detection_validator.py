
import cv2
from collections import deque
from ultralytics import YOLO

CAMERA_URL = "http://192.168.137.181:81/stream"
MODEL_PATH = "yolo11n.pt"

TARGET_FRUITS = {"apple", "orange"}
CONFIDENCE_THRESHOLD = 0.60
STABILITY_WINDOW = 5
MIN_VALID_FRAMES = 3

model = YOLO(MODEL_PATH)
history = deque(maxlen=STABILITY_WINDOW)

# Prevent repeated commands for the same fruit
pick_sent = False


def send_pick_command(fruit_type, confidence):
    """
    Integration point for the robot teammate.

    Replace this function with the agreed communication
    mechanism (ROS, socket, HTTP, etc.).
    """
    print(f"[PICK] fruit={fruit_type}, confidence={confidence:.2f}")


cap = cv2.VideoCapture(CAMERA_URL)

if not cap.isOpened():
    raise RuntimeError("Cannot connect to ESP32-CAM stream")

while True:
    ret, frame = cap.read()
    if not ret:
        print("Camera frame unavailable")
        break

    results = model.predict(
        frame,
        conf=CONFIDENCE_THRESHOLD,
        device="cpu",
        verbose=False
    )

    result = results[0]
    detections = []

    for box in result.boxes:
        cls_id = int(box.cls[0])
        fruit = model.names[cls_id]
        confidence = float(box.conf[0])

        if fruit in TARGET_FRUITS:
            detections.append((fruit, confidence))

            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cv2.rectangle(frame, (x1, y1), (x2, y2),
                          (0, 255, 0), 2)
            cv2.putText(
                frame,
                f"{fruit}: {confidence:.2f}",
                (x1, max(y1 - 10, 20)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6, (0, 255, 0), 2
            )

    # For now, process only when exactly one target fruit
    # is detected in the camera frame.
    if len(detections) == 1:
        fruit, confidence = detections[0]
        history.append(fruit)
    else:
        history.append(None)

    stable_fruit = None

    for fruit_type in TARGET_FRUITS:
        if history.count(fruit_type) >= MIN_VALID_FRAMES:
            stable_fruit = fruit_type
            break

    if stable_fruit and not pick_sent:
        confidence = next(
            (conf for name, conf in detections
             if name == stable_fruit),
            CONFIDENCE_THRESHOLD
        )
        send_pick_command(stable_fruit, confidence)
        pick_sent = True

    # Re-arm only after the target fruit has disappeared
    # for an entire stability window.
    if all(item is None for item in history):
        pick_sent = False

    status = "PICK SENT" if pick_sent else "VALIDATING"

    cv2.putText(
        frame, status, (20, 35),
        cv2.FONT_HERSHEY_SIMPLEX, 0.8,
        (0, 255, 255), 2
    )

    cv2.imshow("Fruit Detection Validation", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
