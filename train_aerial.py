from ultralytics import YOLO

print("Starting aerial YOLO training on Apple MPS (safe mode)")

model = YOLO("yolov8n.pt")

model.train(
    data="aerial_data.yaml",
    epochs=15,
    imgsz=448,
    batch=4,
    workers=2,
    device="mps"
)
