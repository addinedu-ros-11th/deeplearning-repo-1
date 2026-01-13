# scripts/03_train.py
from ultralytics import YOLO
from pathlib import Path
import torch
import yaml
import shutil

# --- Configuration ---
# Model: 
# The user requested 'YOLO11n-obb'. As this specific model isn't standard,
# we are using 'yolov8n-obb.pt', which is a well-known model for oriented object detection.
# You can choose other models like 'yolov8s-obb.pt', 'yolov8m-obb.pt', etc.


# Dataset: Path to the dataset configuration YAML file.
# We use an absolute path to ensure it's found correctly.
ROOT_DIR = Path(__file__).resolve().parents[2]
# #DATASET_CONFIG_PATH = ROOT_DIR / "yw1" / "data" / "processed" /"data.yaml"
# DATASET_CONFIG_PATH = ROOT_DIR / "yw1" / "data" / "yolo_oversampling" /"data.yaml"

# #MODEL_NAME = "yolov8n-obb.pt"
# MODEL_NAME = ROOT_DIR / "yw1" / "runs" / "train" / "25123100_add_labelling" / "weights" / "best.pt"

# # Training Hyperparameters
# EPOCHS = 50
# IMG_SIZE = 640
# BATCH_SIZE = 16 # Adjust based on your GPU memory
# PROJECT_NAME = "yolo_obb_training"
# RUN_NAME = "260112_yolov11n-obb-add_beverage"

# Modify Configuration : "test/yw1/configs/train.yaml"
CONFIG_PATH = ROOT_DIR / "yw1" / "configs" / "train.yaml"

def load_config(path: Path) -> dict:
    """
    Single source of truth for training configuration.
    """
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    with open(path, "r") as f:
        return yaml.safe_load(f)


def save_run_config(cfg: dict, run_dir: Path) -> None:
    """
    Persist the exact config used for this run for full reproducibility.
    """
    run_dir.mkdir(parents=True, exist_ok=True)
    dst = run_dir / "config.yaml"
    with open(dst, "w") as f:
        yaml.safe_dump(cfg, f, sort_keys=False)

# --- Main Training Function ---
def train_model():
    """
    Loads a YOLO OBB model and starts the training process.
    """
    print("--- Starting YOLO OBB Model Training ---")
    cfg = load_config(CONFIG_PATH)
    
    # --- 1. Check for GPU ---
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"Using device: {device}")
    if device == 'cpu':
        print("Warning: No GPU detected. Training on CPU will be very slow.")

    
    model_path = ROOT_DIR / cfg["model"]["name"]
    dataset_yaml = ROOT_DIR / cfg["data"]["dataset_yaml"]
    project_dir = ROOT_DIR / cfg["output"]["project"]
    run_name = cfg["output"]["name"]
    run_dir = project_dir / run_name

    # Save config BEFORE training starts
    save_run_config(cfg, run_dir)

    # --- 2. Load the YOLO model ---
    # This will download the model if it's not already available.
    try:
        model = YOLO(model_path)
    except Exception as e:
        print(f"Error loading model '{model_path}'. Please ensure you have internet access.")
        print(f"Underlying error: {e}")
        return

    # --- 3. Start Training ---
    print(f"Model: {model_path}")
    print(f"Dataset: {dataset_yaml}")
    print(f"Epochs: {cfg['train']['epochs']}, Image Size: {cfg['train']['imgsz']}, Batch Size: {cfg['train']['batch']}")
    print("-" * 30)

    train_args = {
        "data" : str(dataset_yaml),
        "device" : device,
        "project" : cfg["output"]["project"]
    }

    train_args.update(cfg["train"])
    out_cfg = cfg["output"].copy()
    train_args.update(out_cfg)
    final_args = {}
    for k, v in train_args.items():
        if v is None:
            continue
        
        # lr0, lrf, freeze 등 숫자형이어야 하는 인자들을 체크
        if k in ['lr0', 'lrf', 'momentum', 'weight_decay', 'warmup_epochs']:
            try:
                final_args[k] = float(v)
            except (ValueError, TypeError):
                continue # 혹은 에러 처리
        else:
            final_args[k] = v

    try:
        results = model.train(**final_args)

        print("\n--- Training Finished ---")
        print(f"Results saved to: {results.save_dir}")
        print(f"Best model weights saved at: {results.save_dir / 'weights' / 'best.pt'}")
        print("You can view training metrics in 'results.csv' inside the save directory.")

    except Exception as e:
        print(f"\nAn error occurred during training: {e}")
        print("Please check the following:")
        print(f"1. The dataset path in '{dataset_yaml}' is correct.")
        print("2. The image and label files are correctly formatted and located.")
        print("3. You have sufficient system resources (RAM, GPU memory).")

if __name__ == "__main__":
    train_model()
