import cv2
import json
import os
import pickle
import time

import numpy as np
import torch
from ultralytics import YOLO
# =========================================================
# CONFIG
# =========================================================
IMAGE_PATH = "images/img1.jpeg"
SLOTS_FILE = "backend/parking_slots.pkl"
MODEL_PATH = "best.pt"                 # or "yolov8n.pt"
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ANNOTATED_IMAGE_PATH = os.path.join(BASE_DIR, "frontend", "latest_parking_view.jpg")

CONF_THRESHOLD = 0.25
MAX_DET = 300

STATE_FILE = "backend/state.json"

# =========================================================
# STATE WRITER (NEW – SAFE)
# =========================================================
def write_state(slot_occupied):
    data = {
        "timestamp": time.time(),
        "slots": [
            {
                "id": i + 1,
                "status": "OCCUPIED" if occ else "FREE"
            }
            for i, occ in enumerate(slot_occupied)
        ]
    }

    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(data, f, indent=2)


def save_annotated_image(frame):
    os.makedirs(os.path.dirname(ANNOTATED_IMAGE_PATH), exist_ok=True)
    cv2.imwrite(ANNOTATED_IMAGE_PATH, frame)

# =========================================================
# LOAD PARKING SLOTS
# =========================================================
with open(SLOTS_FILE, "rb") as f:
    parking_slots = pickle.load(f)

num_slots = len(parking_slots)
print(f"Loaded {num_slots} parking slots")

# =========================================================
# LOAD MODEL
# =========================================================
device = "mps" if torch.backends.mps.is_available() else "cpu"
print("Using device:", device)

model = YOLO(MODEL_PATH)
model.to(device)

# =========================================================
# IMAGE LOADING
# =========================================================
frame = cv2.imread(IMAGE_PATH)
if frame is None:
    raise RuntimeError(f"Cannot open image: {IMAGE_PATH}")

# =========================================================
# HELPER
# =========================================================
def point_in_polygon(point, polygon):
    return cv2.pointPolygonTest(polygon, point, False) >= 0

def box_overlaps_polygon(box, polygon, image_shape, min_overlap_ratio=0.03):
    x1, y1, x2, y2 = box
    h, w = image_shape[:2]
    x1 = max(0, min(w - 1, x1))
    y1 = max(0, min(h - 1, y1))
    x2 = max(0, min(w - 1, x2))
    y2 = max(0, min(h - 1, y2))

    if x2 <= x1 or y2 <= y1:
        return False

    slot_mask = np.zeros((h, w), dtype=np.uint8)
    cv2.fillPoly(slot_mask, [polygon], 1)

    box_mask = np.zeros((h, w), dtype=np.uint8)
    cv2.rectangle(box_mask, (x1, y1), (x2, y2), 1, -1)

    overlap = cv2.bitwise_and(slot_mask, box_mask)
    overlap_area = int(np.count_nonzero(overlap))
    slot_area = int(np.count_nonzero(slot_mask))

    if slot_area == 0:
        return False

    return (overlap_area / slot_area) >= min_overlap_ratio

# =========================================================
# RUN INFERENCE ON STILL IMAGE
# =========================================================
slot_occupied = [False] * num_slots

results = model(
    frame,
    conf=CONF_THRESHOLD,
    max_det=MAX_DET,
    verbose=False
)

for r in results:
    if r.boxes is None:
        continue

    for box in r.boxes:
        x1, y1, x2, y2 = map(int, box.xyxy[0])

        # Keep the visual marker, but use overlap for occupancy.
        cx = int((x1 + x2) / 2)
        cy = int(y2 - 5)

        cv2.circle(frame, (cx, cy), 4, (255, 0, 0), -1)

        for i, slot in enumerate(parking_slots):
            poly = np.array(slot, np.int32)
            if box_overlaps_polygon((x1, y1, x2, y2), poly, frame.shape):
                slot_occupied[i] = True

free = 0
occupied = 0

for i, slot in enumerate(parking_slots):
    poly = np.array(slot, np.int32)

    if slot_occupied[i]:
        color = (0, 0, 255)
        occupied += 1
    else:
        color = (0, 255, 0)
        free += 1

    cv2.polylines(frame, [poly], True, color, 2)

write_state(slot_occupied)

overlay = frame.copy()
cv2.rectangle(overlay, (10, 10), (420, 120), (0, 0, 0), -1)
frame = cv2.addWeighted(overlay, 0.7, frame, 0.3, 0)

cv2.putText(frame, f"FREE: {free}", (30, 55),
            cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)

cv2.putText(frame, f"OCCUPIED: {occupied}", (30, 100),
            cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)

save_annotated_image(frame)
cv2.imshow("Smart Parking - AI Backend", frame)
print(f"Processed still image: {IMAGE_PATH}")
print("Press any key in the preview window to close.")
cv2.waitKey(0)
cv2.destroyAllWindows()
