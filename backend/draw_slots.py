import cv2
import os
import pickle
import numpy as np
import ctypes
import shutil
from datetime import datetime

# ==================================================
# HARD-LOCKED IMAGE PATH (NO AMBIGUITY)
# ==================================================
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
IMAGE_PATH = os.path.join(BASE_DIR, "images", "img1.jpeg")
OUTPUT_FILE = os.path.join(BASE_DIR, "backend", "parking_slots.pkl")

points = []
slots = []
frame = None
display_scale = 1.0


def get_screen_size():
    try:
        user32 = ctypes.windll.user32
        return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
    except Exception:
        return 1280, 720


def to_original_coords(x, y):
    return (int(x / display_scale), int(y / display_scale))


def to_display_coords(point):
    x, y = point
    return (int(x * display_scale), int(y * display_scale))


def mouse_callback(event, x, y, flags, param):
    global points
    if event == cv2.EVENT_LBUTTONDOWN:
        original_point = to_original_coords(x, y)
        points.append(original_point)
        print(f"Point added: {original_point}")

        if len(points) == 4:
            slots.append(points.copy())
            points.clear()
            print(f"Slot {len(slots)} saved")


frame = cv2.imread(IMAGE_PATH)
if frame is None:
    print("Cannot open image:", IMAGE_PATH)
    raise SystemExit(1)

print("USING IMAGE:", IMAGE_PATH)
print("IMAGE SHAPE:", frame.shape)

screen_w, screen_h = get_screen_size()
max_display_width = int(screen_w * 0.9)
max_display_height = int(screen_h * 0.85)
display_scale = min(
    max_display_width / frame.shape[1],
    max_display_height / frame.shape[0],
    1.0,
)

window_name = "Draw Parking Slots"
cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_NORMAL)
cv2.resizeWindow(
    window_name,
    int(frame.shape[1] * display_scale),
    int(frame.shape[0] * display_scale),
)
cv2.setMouseCallback(window_name, mouse_callback)

print("Click 4 points per slot")
print("Press 'r' to reset current slot")
print("Press 's' to save and exit")

while True:
    display = frame.copy()
    if display_scale != 1.0:
        display = cv2.resize(
            display,
            (0, 0),
            fx=display_scale,
            fy=display_scale,
            interpolation=cv2.INTER_AREA,
        )

    for p in points:
        cv2.circle(display, to_display_coords(p), 5, (0, 0, 255), -1)

    for slot in slots:
        poly = np.array([to_display_coords(p) for p in slot], np.int32)
        cv2.polylines(display, [poly], True, (0, 255, 0), 2)

    cv2.imshow(window_name, display)
    key = cv2.waitKey(1) & 0xFF

    if key == ord("r"):
        points.clear()
        print("Current slot reset")
    elif key == ord("s"):
        if os.path.exists(OUTPUT_FILE):
            stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            backup_file = os.path.join(
                os.path.dirname(OUTPUT_FILE),
                f"parking_slots_backup_{stamp}.pkl",
            )
            shutil.copy2(OUTPUT_FILE, backup_file)
            print(f"Backed up previous slots to {backup_file}")

        with open(OUTPUT_FILE, "wb") as f:
            pickle.dump(slots, f)
        print(f"Saved {len(slots)} slots to {OUTPUT_FILE}")
        break

cv2.destroyAllWindows()
