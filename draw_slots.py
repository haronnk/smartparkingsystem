import cv2
import pickle
import numpy as np

# =========================================================
# CONFIG
# =========================================================
VIDEO_PATH = "videos/parking3.mp4"
SLOTS_FILE = "backend/parking_slots.pkl"

print("🖱 Click 4 points per slot")
print("🔁 Press 'r' to reset current slot")
print("💾 Press 's' to save and exit")

# =========================================================
# LOAD VIDEO
# =========================================================
cap = cv2.VideoCapture(VIDEO_PATH)
if not cap.isOpened():
    raise RuntimeError("❌ Cannot open video")

ret, frame = cap.read()
if not ret:
    raise RuntimeError("❌ Cannot read first frame")

slots = []          # ← START EMPTY (IMPORTANT)
current_slot = []

# =========================================================
# MOUSE CALLBACK
# =========================================================
def mouse_callback(event, x, y, flags, param):
    global current_slot, slots

    if event == cv2.EVENT_LBUTTONDOWN:
        current_slot.append((x, y))

        if len(current_slot) == 4:
            slots.append(current_slot.copy())
            print(f"Slot {len(slots)} saved")
            current_slot.clear()

cv2.namedWindow("Draw Slots", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Draw Slots", 1100, 700)
cv2.setMouseCallback("Draw Slots", mouse_callback)

# =========================================================
# DRAW LOOP
# =========================================================
while True:
    display = frame.copy()

    # Draw completed slots
    for slot in slots:
        poly = np.array(slot, np.int32)
        cv2.polylines(display, [poly], True, (0, 255, 0), 2)

    # Draw current points
    for pt in current_slot:
        cv2.circle(display, pt, 5, (0, 0, 255), -1)

    cv2.imshow("Draw Slots", display)
    key = cv2.waitKey(1) & 0xFF

    if key == ord("r"):
        current_slot.clear()
        print("🔁 Current slot reset")

    elif key == ord("s"):
        with open(SLOTS_FILE, "wb") as f:
            pickle.dump(slots, f)
        print(f"💾 Saved {len(slots)} slots to {SLOTS_FILE}")
        break

    elif key == ord("q"):
        print("❌ Quit without saving")
        break

cap.release()
cv2.destroyAllWindows()
