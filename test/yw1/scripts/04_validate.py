# scripts/04_validate.py
from ultralytics import YOLO
from pathlib import Path
import torch

# --- Configuration ---
# IMPORTANT: You must update this path to point to the specific training run you want to validate.
# Path to the trained model weights.
# The best model is typically saved as 'best.pt' inside the run directory.
# Example: "yolo_obb_training/exp1/weights/best.pt"
PROJECT_NAME = "yolo_obb_training"
RUN_NAME = "obb-label6" # This should match the 'RUN_NAME' from your training script
WEIGHTS_NAME = "best.pt"

# --- Paths ---
ROOT_DIR = Path(__file__).resolve().parents[2]
RUNS_DIR = ROOT_DIR  / "yw1" / "runs" / "train"
WEIGHTS_PATH = RUNS_DIR / RUN_NAME / "weights" / WEIGHTS_NAME
# ---------------------------------------------------------------
WEIGHTS_PATH =  ROOT_DIR  / "yw1" / "runs" / "best_251224.pt"
RUN_NAME = "best_251224"
# ---------------------------------------------------------------
# Dataset split to use for validation: 'val' or 'test'
DATA_SPLIT = "val"

# --- Main Validation Function ---
def validate_model():
    """
    Loads a trained YOLO OBB model and evaluates its performance on a data split.
    """
    print("--- Starting Model Validation ---")

    # --- 1. Check if model weights exist ---
    if not WEIGHTS_PATH.exists():
        print(f"Error: Model weights not found at '{WEIGHTS_PATH}'")
        print("Please ensure the following:")
        print("1. You have run the training script (03_train.py).")
        print(f"2. The PROJECT_NAME ('{PROJECT_NAME}') and RUN_NAME ('{RUN_NAME}') variables match your training output folder.")
        return

    # --- 2. Check for GPU ---
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"Using device: {device}")

    # --- 3. Load the trained model ---
    try:
        model = YOLO(WEIGHTS_PATH)
    except Exception as e:
        print(f"Error loading model from '{WEIGHTS_PATH}'.")
        print(f"Underlying error: {e}")
        return

    # --- 4. Run Validation ---
    print(f"Loading model: {WEIGHTS_PATH}")
    print(f"Evaluating on '{DATA_SPLIT}' split.")
    print("-" * 30)

    try:
        metrics = model.val(
            split=DATA_SPLIT,
            # You can override some settings from the dataset.yaml if needed
            data='./test/yw1/data/processed/data.yaml',
            project=(RUNS_DIR.parent / "val"), # Save validation results to test/yw1/runs/val
            name=RUN_NAME,
            exist_ok=True,
        )
        print("\n--- Validation Complete ---")
        print(f"Results saved to: {metrics.save_dir}")
        print("\nOriented Bounding Box Metrics:")
        box_metrics = metrics.box
        print(f"  - mAP50-95: {box_metrics.map:.4f}")
        print(f"  - mAP50:    {box_metrics.map50:.4f}")
        print(f"  - mAP75:    {box_metrics.map75:.4f}")

    except Exception as e:
        print(f"\nAn error occurred during validation: {e}")
        print("Please check that the dataset is correctly configured and accessible.")


if __name__ == "__main__":
    validate_model()
