import cv2
import pickle
import os
import numpy as np

# ==================================================
# HARD-LOCKED VIDEO PATH (NO AMBIGUITY)
# ==================================================
VIDEO_PATH = "/Users/summie/Desktop/smart-parking 4/videos/parking.mp4"
OUTPUT_FILE = "/Users/summie/Desktop/smart-parking 4/backend/parking_slots.pkl"

points = []
slots = []

def mouse_callback(event, x, y, flags, param):
    global points
    if event == cv2.EVENT_LBUTTONDOWN:
        points.append((x, y))
        print(f"Point added: {(x, y)}")

        if len(points) == 4:
            slots.append(points.copy())
            points.clear()
            print(f"✅ Slot {len(slots)} saved")

cap = cv2.VideoCapture(VIDEO_PATH)
if not cap.isOpened():
    print("❌ Cannot open video:", VIDEO_PATH)
    exit()

ret, frame = cap.read()
if not ret:
    print("❌ Cannot read first frame")
    exit()

print("USING VIDEO:", VIDEO_PATH)
print("FRAME SHAPE:", frame.shape)

cv2.namedWindow("Draw Parking Slots", cv2.WINDOW_NORMAL)
cv2.setMouseCallback("Draw Parking Slots", mouse_callback)

print("🖱 Click 4 points per slot")
print("🔁 Press 'r' to reset current slot")
print("💾 Press 's' to save and exit")

while True:
    display = frame.copy()

    for p in points:
        cv2.circle(display, p, 5, (0, 0, 255), -1)

    for slot in slots:
        poly = np.array(slot, np.int32)
        cv2.polylines(display, [poly], True, (0, 255, 0), 2)

    cv2.imshow("Draw Parking Slots", display)
    key = cv2.waitKey(1) & 0xFF

    if key == ord("r"):
        points.clear()
        print("↩️ Current slot reset")

    elif key == ord("s"):
        with open(OUTPUT_FILE, "wb") as f:
            pickle.dump(slots, f)
        print(f"💾 Saved {len(slots)} slots to {OUTPUT_FILE}")
        break

cap.release()
cv2.destroyAllWindows()
