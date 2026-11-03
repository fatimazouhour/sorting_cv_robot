import cv2

ESP32_IP = "192.168.137.188"
STREAM_URL = f"http://{ESP32_IP}:81/stream"

print(f"Connecting to {STREAM_URL}...")

cap = cv2.VideoCapture(STREAM_URL)

if not cap.isOpened():
    print("❌ Could not connect to ESP32-CAM")
    exit()

print("✅ Connected to ESP32-CAM")

while True:
    ret, frame = cap.read()

    if not ret:
        print("❌ Failed to receive frame")
        break

    cv2.imshow("ESP32-CAM", frame)

    # Press Q to quit
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()