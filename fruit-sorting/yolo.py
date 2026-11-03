"""
Detection test with YOLO and an ESP32-CAM stream (or a webcam), without accumulating lag.

The stream is read in a separate thread that keeps only the latest frame.
This way, even if YOLO is slower than the camera, the processed image is always the current one.

Usage:
    python esp32_detection_test.py --source http://ESP32_IP:81/stream
    python esp32_detection_test.py --source 0                  # computer webcam
    python esp32_detection_test.py --source http://IP:81/stream --model yolo11m.pt --imgsz 480

Keys:
    q or ESC : quit
    s        : save the current frame (with detections) to captures/
    a        : toggle between "target classes only" and "all 80 classes"
    + / -    : increase / decrease the confidence threshold
"""

import argparse
import os
import threading
import time

# Must be set before cv2 is imported: tells FFmpeg not to buffer the MJPEG stream
os.environ.setdefault("OPENCV_FFMPEG_CAPTURE_OPTIONS", "fflags;nobuffer|flags;low_delay")

try:
    import importlib

    cv2 = importlib.import_module("cv2")
except ImportError as exc:
    raise SystemExit(
        "OpenCV is required. Install it in the active Python environment with: "
        "python -m pip install opencv-python"
    ) from exc

from ultralytics import YOLO

# COCO IDs: 32 = sports ball, 46 = banana, 47 = apple, 49 = orange
TARGET_CLASSES = [32, 46, 47, 49]


class FrameReader:
    """Continuously reads the camera in another thread and keeps only the latest frame."""

    def __init__(self, source):
        self.source = source
        self.cap = None
        self.frame = None
        self.frame_id = 0
        self.lock = threading.Lock()
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)

    def _open(self):
        cap = cv2.VideoCapture(self.source)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # not every backend honors this, but it helps
        return cap

    def _loop(self):
        self.cap = self._open()
        while self.running:
            if not self.cap.isOpened():
                time.sleep(1.0)
                self.cap = self._open()
                continue
            ok, frame = self.cap.read()
            if not ok:
                self.cap.release()
                time.sleep(0.5)
                self.cap = self._open()
                continue
            with self.lock:
                self.frame = frame
                self.frame_id += 1

    def start(self):
        self.thread.start()
        return self

    def read(self):
        with self.lock:
            if self.frame is None:
                return None, 0
            return self.frame.copy(), self.frame_id

    def stop(self):
        self.running = False
        self.thread.join(timeout=2.0)
        if self.cap is not None:
            self.cap.release()


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--source", default="0",
                   help="webcam index (0, 1, ...) or ESP32 stream URL")
    p.add_argument("--model", default="yolo11s.pt")
    p.add_argument("--conf", type=float, default=0.5)
    p.add_argument("--imgsz", type=int, default=640,
                   help="model input size; smaller = faster (e.g. 480, 416)")
    return p.parse_args()


def main():
    args = parse_args()
    source = int(args.source) if args.source.isdigit() else args.source

    model = YOLO(args.model)
    reader = FrameReader(source).start()

    os.makedirs("captures", exist_ok=True)
    conf = args.conf
    target_only = True
    last_id = 0
    annotated = None
    infer_time = 0.0
    cam_fps = 0.0
    fps_t0 = time.time()
    fps_id0 = 0

    print("Waiting for the first frame...")
    while True:
        frame, frame_id = reader.read()
        if frame is None:
            time.sleep(0.05)
            if cv2.waitKey(1) & 0xFF in (ord("q"), 27):
                break
            continue

        # Camera frame rate as received (network + decode), updated once per second
        now = time.time()
        if now - fps_t0 >= 1.0:
            cam_fps = (frame_id - fps_id0) / (now - fps_t0)
            fps_t0, fps_id0 = now, frame_id

        # Only run the model when a new frame has arrived
        if frame_id != last_id:
            last_id = frame_id
            t0 = time.time()
            result = model(frame, classes=TARGET_CLASSES if target_only else None,
                           conf=conf, imgsz=args.imgsz, verbose=False)[0]
            infer_time = time.time() - t0
            annotated = result.plot()

            detections = []
            for box in result.boxes:
                name = model.names[int(box.cls)]
                cx, cy = box.xywh[0][:2].tolist()
                detections.append(f"{name} {float(box.conf):.2f} ({cx:.0f},{cy:.0f})")
            if detections:
                print(" | ".join(detections))

            mode = "target classes" if target_only else "all classes"
            info = (f"cam {cam_fps:.0f} fps | inference {infer_time * 1000:.0f} ms | "
                    f"conf {conf:.2f} | {mode} | imgsz {args.imgsz}")
            cv2.putText(annotated, info, (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        if annotated is not None:
            cv2.imshow("ESP32 + YOLO (press q to quit)", annotated)

        key = cv2.waitKey(1) & 0xFF
        if key in (ord("q"), 27):
            break
        elif key == ord("s") and annotated is not None:
            filename = os.path.join("captures", f"capture_{int(time.time())}.jpg")
            cv2.imwrite(filename, annotated)
            print(f"Saved: {filename}")
        elif key == ord("a"):
            target_only = not target_only
        elif key in (ord("+"), ord("=")):
            conf = min(0.95, conf + 0.05)
        elif key in (ord("-"), ord("_")):
            conf = max(0.05, conf - 0.05)

    reader.stop()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()