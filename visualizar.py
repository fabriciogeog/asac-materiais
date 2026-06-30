from ultralytics import YOLO

# Load a pre-trained model (n=nano, s=small, m=medium)
model = YOLO("detect/train-2/weights/best.pt") 

# Run inference on webcam (source=0) with real-time display
model.predict(source="0", show=True)
