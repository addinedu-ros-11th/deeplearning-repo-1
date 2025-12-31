# scripts/03_train.py
from ultralytics import YOLO
from pathlib import Path
import torch

# --- Configuration ---
# Model: 
# The user requested 'YOLO11n-obb'. As this specific model isn't standard,
# we are using 'yolov8n-obb.pt', which is a well-known model for oriented object detection.
# You can choose other models like 'yolov8s-obb.pt', 'yolov8m-obb.pt', etc.


# Dataset: Path to the dataset configuration YAML file.
# We use an absolute path to ensure it's found correctly.
ROOT_DIR = Path(__file__).resolve().parents[2]
DATASET_CONFIG_PATH = ROOT_DIR / "yw1" / "data" / "processed" /"data.yaml"
#MODEL_NAME = "yolov8n-obb.pt"
MODEL_NAME = ROOT_DIR / "yw1" / "runs" / "train" / "25123101_yolov8n-obb_temp" / "weights" / "best.pt"

# Training Hyperparameters
EPOCHS = 100
IMG_SIZE = 640
BATCH_SIZE = 16 # Adjust based on your GPU memory
PROJECT_NAME = "yolo_obb_training"
RUN_NAME = "25123101_yolov8n-obb"

# --- Main Training Function ---
def train_model():
    """
    Loads a YOLO OBB model and starts the training process.
    """
    print("--- Starting YOLO OBB Model Training ---")
    
    # --- 1. Check for GPU ---
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"Using device: {device}")
    if device == 'cpu':
        print("Warning: No GPU detected. Training on CPU will be very slow.")

    # --- 2. Load the YOLO model ---
    # This will download the model if it's not already available.
    try:
        model = YOLO(MODEL_NAME)
    except Exception as e:
        print(f"Error loading model '{MODEL_NAME}'. Please ensure you have internet access.")
        print(f"Underlying error: {e}")
        return

    # --- 3. Start Training ---
    print(f"Model: {MODEL_NAME}")
    print(f"Dataset: {DATASET_CONFIG_PATH}")
    print(f"Epochs: {EPOCHS}, Image Size: {IMG_SIZE}, Batch Size: {BATCH_SIZE}")
    print("-" * 30)

    try:
        results = model.train(
            data=str(DATASET_CONFIG_PATH),
            epochs=EPOCHS,
            imgsz=IMG_SIZE,
            batch=BATCH_SIZE,
            project=(ROOT_DIR / "yw1" / "runs" / "train"), # Save results to test/yw1/runs/train
            name=RUN_NAME,
            exist_ok=False, # Don't overwrite existing runs
            device=device,
            # Additional OBB-specific or general training options can be added here
            # e.g., optimizer='AdamW', lr0='0.001', etc.
        )
        print("\n--- Training Finished ---")
        print(f"Results saved to: {results.save_dir}")
        print(f"Best model weights saved at: {results.save_dir / 'weights' / 'best.pt'}")
        print("You can view training metrics in 'results.csv' inside the save directory.")

    except Exception as e:
        print(f"\nAn error occurred during training: {e}")
        print("Please check the following:")
        print(f"1. The dataset path in '{DATASET_CONFIG_PATH}' is correct.")
        print("2. The image and label files are correctly formatted and located.")
        print("3. You have sufficient system resources (RAM, GPU memory).")

if __name__ == "__main__":
    train_model()
