"""
Detection test with YOLO11s and the computer's webcam.

Installation:
    pip install ultralytics opencv-python

Usage:
    python yolo.py
    python yolo.py --camera 1 --conf 0.4
    python yolo.py --esp32 192.168.1.50          # ESP32-CAM stream (http://<ip>:81/stream)
    python yolo.py --esp32 http://192.168.1.50:81/stream

ESP32-CAM:
    Flash the "CameraWebServer" example (Arduino IDE > Examples > ESP32 > Camera),
    open the serial monitor to read the board's IP, and make sure the PC is on the
    same Wi-Fi network. The MJPEG stream is served at http://<ip>:81/stream.

Keys:
    q or ESC : quit
    s        : save the current frame (with detections) to the captures/ folder
    a        : toggle between "target classes only" and "all 80 classes"
    + / -    : increase / decrease the confidence threshold
"""

import argparse
import os
import time

import cv2
from ultralytics import YOLO

# COCO IDs: 32 = sports ball, 46 = banana, 47 = apple, 49 = orange
TARGET_CLASSES = [32, 46, 47, 49]


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--camera", type=int, default=0, help="webcam index (0, 1, ...)")
    p.add_argument("--esp32", default=None,
                   help="ESP32-CAM IP or stream URL; if set, replaces the PC webcam")
    p.add_argument("--model", default="yolo11s.pt", help="model weights")
    p.add_argument("--conf", type=float, default=0.5, help="initial confidence threshold")
    p.add_argument("--width", type=int, default=1280)
    p.add_argument("--height", type=int, default=720)
    return p.parse_args()


def esp32_stream_url(value):
    """Accept a bare IP/host or a full URL and return the MJPEG stream URL."""
    if value.startswith(("http://", "https://", "rtsp://")):
        return value
    return f"http://{value}:81/stream"


def main():
    args = parse_args()

    model = YOLO(args.model)  # downloads the weights automatically the first time

    if args.esp32:
        url = esp32_stream_url(args.esp32)
        print(f"Connecting to ESP32-CAM at {url}...")
        cap = cv2.VideoCapture(url)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # keep latency low
        if not cap.isOpened():
            raise SystemExit(f"Could not open the ESP32-CAM stream at {url}. "
                             "Check the IP, the Wi-Fi network and that no other client is connected.")
    else:
        cap = cv2.VideoCapture(args.camera)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)
        if not cap.isOpened():
            raise SystemExit(f"Could not open camera {args.camera}. Try --camera 1.")

    os.makedirs("captures", exist_ok=True)

    conf = args.conf
    target_only = True
    last_time = time.time()
    fps = 0.0

    print("Camera opened. Keys: q = quit, s = save, a = all classes, +/- = confidence")

    while True:
        ok, frame = cap.read()
        if not ok:
            print("Failed to read frame from camera.")
            break

        results = model(
            frame,
            classes=TARGET_CLASSES if target_only else None,
            conf=conf,
            verbose=False,
        )[0]

        image = results.plot()

        # List the detections in the terminal
        detections = []
        for box in results.boxes:
            name = model.names[int(box.cls)]
            confidence = float(box.conf)
            cx, cy = box.xywh[0][:2].tolist()
            detections.append(f"{name} {confidence:.2f} ({cx:.0f},{cy:.0f})")
        if detections:
            print(" | ".join(detections))

        # Smoothed FPS
        now = time.time()
        fps = 0.9 * fps + 0.1 * (1.0 / max(now - last_time, 1e-6))
        last_time = now

        mode = "target classes" if target_only else "all classes"
        info = f"FPS {fps:.1f} | conf {conf:.2f} | {mode}"
        cv2.putText(image, info, (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        cv2.imshow("Detection test (q to quit)", image)

        key = cv2.waitKey(1) & 0xFF
        if key in (ord("q"), 27):
            break
        elif key == ord("s"):
            filename = os.path.join("captures", f"capture_{int(time.time())}.jpg")
            cv2.imwrite(filename, image)
            print(f"Saved: {filename}")
        elif key == ord("a"):
            target_only = not target_only
        elif key in (ord("+"), ord("=")):
            conf = min(0.95, conf + 0.05)
        elif key in (ord("-"), ord("_")):
            conf = max(0.05, conf - 0.05)

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
