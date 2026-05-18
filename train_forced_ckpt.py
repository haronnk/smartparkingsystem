from ultralytics import YOLO
from ultralytics.models.yolo.detect.train import DetectionTrainer
import torch
import os

SAVE_EVERY_BATCHES = 200  # <-- save every 200 batches
MAX_BATCHES = 600         # <-- stop before MPS usually crashes

class ForcedSaveTrainer(DetectionTrainer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.batch_count = 0

    def train_batch(self, batch):
        loss = super().train_batch(batch)
        self.batch_count += 1

        if self.batch_count % SAVE_EVERY_BATCHES == 0:
            save_dir = os.path.join(self.save_dir, "weights")
            os.makedirs(save_dir, exist_ok=True)
            save_path = os.path.join(save_dir, f"forced_batch_{self.batch_count}.pt")
            self.model.save(save_path)
            print(f"\n[FORCED SAVE] {save_path}\n")

        if self.batch_count >= MAX_BATCHES:
            print("\n[SAFE EXIT] Max batch count reached\n")
            raise KeyboardInterrupt

        return loss


model = YOLO("yolov8n.pt")

model.train(
    data="aerial_data.yaml",
    imgsz=448,
    batch=2,
    workers=1,
    device="mps",
    epochs=999,                 # we stop manually
    trainer=ForcedSaveTrainer,
    save=False                  # disable normal saving
)
