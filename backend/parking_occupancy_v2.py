import cv2
import pickle
import numpy as np
import torch
import json
import time
import os
from ultralytics import YOLO
import json
import os

def write_state(slot_occupied):
    os.makedirs("backend", exist_ok=True)
    state = {
        "slots": [
            {"id": i + 1, "status": "occupied" if occ else "free"}
            for i, occ in enumerate(slot_occupied)
        ]
    }
    with open("backend/state.json", "w") as f:
        json.dump(state, f)
# =========================================================
# CONFIG
# =========================================================
VIDEO_PATH = "videos/parking3.mp4"
SLOTS_FILE = "backend/parking_slots.pkl"
MODEL_PATH = "best.pt"                 # or "yolov8n.pt"

CONF_THRESHOLD = 0.25
MAX_DET = 300
FRAME_SKIP = 2                         # higher = slower playback

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
# VIDEO CAPTURE
# =========================================================
cap = cv2.VideoCapture(VIDEO_PATH)
if not cap.isOpened():
    raise RuntimeError(f"❌ Cannot open video: {VIDEO_PATH}")

frame_count = 0

# =========================================================
# HELPER
# =========================================================
def point_in_polygon(point, polygon):
    return cv2.pointPolygonTest(polygon, point, False) >= 0

# =========================================================
# MAIN LOOP
# =========================================================
while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame_count += 1
    if frame_count % FRAME_SKIP != 0:
        continue

    slot_occupied = [False] * num_slots

    # ---------------- YOLO INFERENCE ----------------
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

            # bottom-center logic (UNCHANGED)
            cx = int((x1 + x2) / 2)
            cy = int(y2 - 5)

            cv2.circle(frame, (cx, cy), 4, (255, 0, 0), -1)

            for i, slot in enumerate(parking_slots):
                poly = np.array(slot, np.int32)
                if point_in_polygon((cx, cy), poly):
                    slot_occupied[i] = True

    # ---------------- DRAW SLOTS ----------------
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

    # ✅ EXPORT STATE (SAFE ADDITION)
    write_state(slot_occupied)

    # ---------------- UI PANEL ----------------
    overlay = frame.copy()
    cv2.rectangle(overlay, (10, 10), (420, 120), (0, 0, 0), -1)
    frame = cv2.addWeighted(overlay, 0.7, frame, 0.3, 0)

    cv2.putText(frame, f"FREE: {free}", (30, 55),
                cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)

    cv2.putText(frame, f"OCCUPIED: {occupied}", (30, 100),
                cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)
    write_state(slot_occupied)
    # ---------------- DISPLAY ----------------
    cv2.imshow("Smart Parking – AI Backend", frame)

    if cv2.waitKey(30) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
