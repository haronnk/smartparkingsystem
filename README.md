# Smart Parking System

Smart Parking System is a computer-vision parking monitor with a simple web dashboard for drivers and admins.

The project combines:

- A YOLO-based occupancy detector that reads parking-lot video and marks slots as `FREE` or `OCCUPIED`
- A Flask backend that serves live slot data and reservation APIs
- A static frontend with a driver portal and an admin dashboard

## Features

- Live parking-slot occupancy from video inference
- Driver reservation flow
- Admin dashboard with slot counts and active reservations
- Local JSON state storage for occupancy and bookings

## Project Structure

```text
smart-parking-4/
├── backend/
│   ├── app.py
│   ├── parking_occupancy_v2.py
│   ├── parking_slots.pkl
│   ├── reservations.json
│   └── state.json
├── frontend/
│   ├── index.html
│   ├── user.html
│   ├── admin.html
│   ├── app.js
│   └── style.css
├── videos/
├── best.pt
├── train_aerial.py
└── train_forced_ckpt.py
```

## Tech Stack

- Python
- Flask
- Flask-CORS
- OpenCV
- Ultralytics YOLO
- PyTorch
- HTML, CSS, JavaScript

## How It Works

1. `backend/parking_occupancy_v2.py` loads the trained YOLO model and a parking video.
2. The detector checks whether each configured polygon slot contains a car.
3. Occupancy is written to `backend/state.json`.
4. `backend/app.py` combines live occupancy with reservation data from `backend/reservations.json`.
5. The frontend polls the API and updates the driver/admin views.

## Running Locally

### 1. Create and activate a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install flask flask-cors opencv-python ultralytics torch numpy
```

### 3. Start the web app

```bash
python backend/app.py
```

Open:

- `http://127.0.0.1:9000/`

### 4. Start the occupancy detector

```bash
python backend/parking_occupancy_v2.py
```

Note: the detector currently uses `cv2.imshow(...)`, so it needs a desktop session with GUI access.

## API Endpoints

- `GET /api/slots` - live slot data with reservation state
- `POST /api/reserve` - reserve a slot
- `POST /api/cancel` - cancel a reservation
- `GET /api/admin/stats` - dashboard counts

## Model And Data Notes

- `best.pt` is the trained model used for inference
- Large training assets such as `cardb/` and `cardb.zip` are intentionally excluded from Git because they are too large for a normal repository push

## Future Improvements

- Replace local JSON storage with a database
- Make the AI backend run headless without `cv2.imshow`
- Add authentication for admin features
- Add a `requirements.txt` file for repeatable setup
