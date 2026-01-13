# scripts/06_test_video.py
import cv2
from ultralytics import YOLO
from pathlib import Path
import torch
import os
import shutil

# --- Configuration ---
# IMPORTANT: Update these paths and settings according to your video and model.

# Path to the trained model weights.
# Example: ROOT_DIR / "yw1" / "runs" / "train" / "yolo_obb_training_exp1" / "weights" / "best.pt"
# You might need to adjust RUN_NAME to match your actual training run.
ROOT_DIR = Path(__file__).resolve().parents[3]
RUNS_DIR = ROOT_DIR /"test"/ "yw1" / "runs" / "train"
RUN_NAME = "250113_obb_ch"
# Example: WEIGHTS_PATH = RUNS_DIR / "your_run_name" / "weights" / "best.pt"
WEIGHTS_PATH = ROOT_DIR / "models" / "product_recognizer" / (RUN_NAME+".pt") 
# WEIGHTS_PATH = RUNS_DIR / "260112_yolov11n-obb-add_beverage_freeze20" / "weights" /"best.pt"
# Path to the dataset configuration YAML file for evaluation.
DATASET_CONFIG_PATH = ROOT_DIR / "test" / "yw1" / "data" / "TEST_VIDEO" / "data.yaml"

# Prediction Settings (These will be passed to model.val())
CONFIDENCE_THRESHOLD = 0.25 # Minimum confidence for evaluation
IOU_THRESHOLD = 0.45       # IoU threshold for NMS for evaluation

# Class names will be loaded from DATASET_CONFIG_PATH by YOLO automatically.

# --- Main Performance Test Function ---

def test_model_performance():
    """
    Evaluates a trained YOLO OBB model's performance on the test dataset.
    """
    print("--- Starting YOLO OBB Model Performance Evaluation ---")

    # --- 0. Pre-checks ---
    if not WEIGHTS_PATH.exists():
        print(f"Error: Model weights not found at '{WEIGHTS_PATH}'")
        print("Please ensure WEIGHTS_PATH points to your trained model (e.g., 'best.pt').")
        return
    
    if not DATASET_CONFIG_PATH.exists():
        print(f"Error: Dataset configuration file not found at '{DATASET_CONFIG_PATH}'")
        print("Please ensure 02_split_dataset.py has been run to generate data.yaml.")
        return

    # --- 1. Check for GPU ---
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"Using device: {device}")
    if device == 'cpu':
        print("Warning: No GPU detected. Evaluation on CPU might be slow.")

    # --- 2. Load the trained model ---
    try:
        model = YOLO(str(WEIGHTS_PATH))
    except Exception as e:
        print(f"Error loading model from '{WEIGHTS_PATH}'.")
        print(f"Underlying error: {e}")
        return

    print(f"Loading model: {WEIGHTS_PATH}")
    print(f"Evaluating on test split defined in: {DATASET_CONFIG_PATH}")
    print("-" * 30)

    # --- 3. Run Validation on Test Split ---
    try:
        metrics = model.val(
            data=str(DATASET_CONFIG_PATH),
            split='test',  # Evaluate on the 'test' split defined in data.yaml
            project=(ROOT_DIR / "test" / "yw1" / "runs" / "test"), # Save evaluation results
            name=RUN_NAME, # Name for this specific evaluation run
            exist_ok=False, # Allow overwriting previous test runs if needed
            device=device,
            # Add other validation parameters if needed, e.g., imgsz, conf, iou
            conf=CONFIDENCE_THRESHOLD,
            iou=IOU_THRESHOLD,
        )
        print("--- Performance Evaluation Complete ---")
        print(f"Results saved to: {metrics.save_dir}")
        print("Oriented Bounding Box Metrics:")
        box_metrics = metrics.box
        print(f"  - mAP50-95 (OBB): {box_metrics.map:.4f}")
        print(f"  - mAP50 (OBB):    {box_metrics.map50:.4f}")
        print(f"  - mAP75 (OBB):    {box_metrics.map75:.4f}")

        # Save box_metrics to a text file
        output_dir = Path(metrics.save_dir)
        output_file = output_dir / "box_metrics.txt"
        with open(output_file, "w") as f:
            f.write("Oriented Bounding Box Metrics:\n")
            f.write(f"  - mAP50-95 (OBB): {box_metrics.map:.4f}\n")
            f.write(f"  - mAP50 (OBB):    {box_metrics.map50:.4f}\n")
            f.write(f"  - mAP75 (OBB):    {box_metrics.map75:.4f}\n")
        print(f"Box metrics also saved to: {output_file}")
        # You can access other metrics like precision, recall, f1-score per class if available
        # print(metrics.results_dict) # For a dictionary of all results

    except Exception as e:
        print(f"An error occurred during model evaluation: {e}")
        print("Please check the following:")
        print(f"1. The dataset configuration in '{DATASET_CONFIG_PATH}' is correct.")
        print("2. The image and label files for the 'test' split are correctly formatted and located.")
        print("3. You have sufficient system resources (RAM, GPU memory).")

# --- Script Execution ---
if __name__ == "__main__":
    test_model_performance()
