import os

import cv2
import numpy as np

PERSON = 0
VEHICLES = (2, 3, 5, 7)


def pad_box(x1, y1, x2, y2, frac, w, h):
    bw, bh = x2 - x1, y2 - y1
    px, py = bw * frac, bh * frac
    return (
        int(max(0, x1 - px)),
        int(max(0, y1 - py)),
        int(min(w, x2 + px)),
        int(min(h, y2 + py)),
    )


def pixelate(img, box, blocks=6):
    x1, y1, x2, y2 = box
    if x2 - x1 < 2 or y2 - y1 < 2:
        return False
    roi = img[y1:y2, x1:x2]
    small = cv2.resize(roi, (blocks, blocks), interpolation=cv2.INTER_AREA)
    img[y1:y2, x1:x2] = cv2.resize(small, (x2 - x1, y2 - y1), interpolation=cv2.INTER_NEAREST)
    return True


class PrivacyBlur:
    def __init__(self):
        self.enabled = os.getenv("PRIVACY_BLUR", "1") == "1"
        self.mode = os.getenv("PRIVACY_MODE", "standard")
        self.face = None
        self.profile = None
        self.plate = None
        self.plate_model = None
        self.coco = None

        # Check if OpenCV cascade classifiers are supported in this environment
        if hasattr(cv2, "CascadeClassifier") and hasattr(cv2, "data") and hasattr(cv2.data, "haarcascades"):
            base = cv2.data.haarcascades
            try:
                self.face = cv2.CascadeClassifier(base + "haarcascade_frontalface_default.xml")
                self.profile = cv2.CascadeClassifier(base + "haarcascade_profileface.xml")
                self.plate = cv2.CascadeClassifier(base + "haarcascade_russian_plate_number.xml")
            except Exception:
                self.face = self.profile = self.plate = None

        plate_path = os.getenv("PLATE_MODEL_PATH")
        if self.enabled and plate_path and os.path.exists(plate_path):
            from ultralytics import YOLO
            self.plate_model = YOLO(plate_path)

        # In aggressive mode OR if Haar cascades are unavailable, use YOLO COCO model
        if self.enabled and (self.mode == "aggressive" or self.face is None):
            from ultralytics import YOLO
            coco_path = os.getenv("COCO_MODEL_PATH", "yolov8n.pt")
            self.coco = YOLO(coco_path)

    def find_boxes(self, img):
        h, w = img.shape[:2]
        boxes = []

        if self.face is not None and self.profile is not None:
            c_scale = 1.0
            if max(h, w) > 800:
                c_scale = 800.0 / max(h, w)
                c_img = cv2.resize(img, (int(w * c_scale), int(h * c_scale)), interpolation=cv2.INTER_LINEAR)
            else:
                c_img = img

            gray = cv2.cvtColor(c_img, cv2.COLOR_BGR2GRAY)
            for cascade in (self.face, self.profile):
                for x, y, bw, bh in cascade.detectMultiScale(gray, 1.2, 4, minSize=(25, 25)):
                    ox1, oy1 = int(x / c_scale), int(y / c_scale)
                    ox2, oy2 = int((x + bw) / c_scale), int((y + bh) / c_scale)
                    boxes.append(pad_box(ox1, oy1, ox2, oy2, 0.3, w, h))

        if self.plate_model is not None:
            r = self.plate_model.predict(img, conf=0.25, imgsz=640, verbose=False)[0]
            for x1, y1, x2, y2 in r.boxes.xyxy.cpu().numpy():
                boxes.append(pad_box(x1, y1, x2, y2, 0.15, w, h))
        elif self.plate is not None:
            if 'gray' not in locals():
                c_scale = 1.0
                if max(h, w) > 800:
                    c_scale = 800.0 / max(h, w)
                    c_img = cv2.resize(img, (int(w * c_scale), int(h * c_scale)), interpolation=cv2.INTER_LINEAR)
                else:
                    c_img = img
                gray = cv2.cvtColor(c_img, cv2.COLOR_BGR2GRAY)
            for x, y, bw, bh in self.plate.detectMultiScale(gray, 1.2, 4, minSize=(30, 10)):
                ox1, oy1 = int(x / c_scale), int(y / c_scale)
                ox2, oy2 = int((x + bw) / c_scale), int((y + bh) / c_scale)
                boxes.append(pad_box(ox1, oy1, ox2, oy2, 0.15, w, h))

        if self.coco is not None:
            r = self.coco.predict(
                img, conf=0.3, imgsz=640, classes=[PERSON, *VEHICLES], verbose=False
            )[0]
            xyxy = r.boxes.xyxy.cpu().numpy()
            cls = r.boxes.cls.cpu().numpy().astype(int)
            for (x1, y1, x2, y2), c in zip(xyxy, cls):
                if c == PERSON:
                    boxes.append(pad_box(x1, y1, x2, y1 + 0.3 * (y2 - y1), 0.1, w, h))
                else:
                    boxes.append(pad_box(x1, y1 + 0.6 * (y2 - y1), x2, y2, 0.05, w, h))

        return boxes

    def apply(self, img):
        if not self.enabled:
            return img, 0
        out = img.copy()
        count = 0
        for box in self.find_boxes(img):
            if pixelate(out, box):
                count += 1
        return out, count
