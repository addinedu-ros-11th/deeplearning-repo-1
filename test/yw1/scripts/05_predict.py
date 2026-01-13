# scripts/05_predict.py
from ultralytics import YOLO
from pathlib import Path
import torch

# --- Configuration ---
# IMPORTANT: You must update this path to point to the specific training run you want to use for prediction.
PROJECT_NAME = "yolo_obb_training"
RUN_NAME = "250113_obb_ch" # This should match the 'RUN_NAME' from your training script
# 25123100_add_labelling
# 25123101_yolov8n-obb
WEIGHTS_NAME = "best.pt"

# --- Paths ---
ROOT_DIR = Path(__file__).resolve().parents[2]
RUNS_DIR = ROOT_DIR  / "yw1" / "runs" / "train"
WEIGHTS_PATH = RUNS_DIR / RUN_NAME / "weights" / WEIGHTS_NAME
#WEIGHTS_PATH = ROOT_DIR / "yw1" / "runs" /"best_251229.pt"
WEIGHTS_PATH = Path(__file__).resolve().parents[3]/ "models" / "product_recognizer" / "250113_obb_ch.pt"
# best_251231
# Source for image prediction
SOURCE_DIR = ROOT_DIR / "yw1" / "data" / "inference" / "input"
# Directory to save prediction results.
OUTPUT_DIR = ROOT_DIR  / "yw1" / "data" / "inference" / "output"

# --- Prediction Settings ---
CONFIDENCE_THRESHOLD = 0.3 # Only detect objects with confidence > 25%

def predict_on_images():
    """
    Loads a trained model and runs predictions on images in the source directory.
    Saves the results (images with boxes and text files with coordinates).
    """
    print("--- Running Inference on Images ---")

    # --- 1. Check for model and source ---
    if not WEIGHTS_PATH.exists():
        print(f"Error: Model weights not found at '{WEIGHTS_PATH}'")
        print("Please ensure your training run paths are correct.")
        return

    if not SOURCE_DIR.exists() or not any(SOURCE_DIR.iterdir()):
        print(f"Error: Source directory '{SOURCE_DIR}' is empty or does not exist.")
        print("Please add images to the 'input' folder and try again.")
        # Check for the placeholder and give a hint
        if (SOURCE_DIR / "placeholder.txt").exists():
             print("I see 'placeholder.txt'. Replace it with your actual image files (.jpg, .png, etc.).")
        return

    # --- 2. Create output directory ---
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # --- 3. Load the model ---
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"Using device: {device}")
    
    try:
        model = YOLO(WEIGHTS_PATH)
    except Exception as e:
        print(f"Error loading model from '{WEIGHTS_PATH}'.")
        print(f"Underlying error: {e}")
        return

    # --- 4. Run Prediction ---
    print(f"Loading model: {WEIGHTS_PATH}")
    print(f"Predicting on images in: {SOURCE_DIR}")
    print(f"Saving results to: {OUTPUT_DIR}")
    print("-" * 30)

    try:
        model.predict(
            source=str(SOURCE_DIR),
            conf=CONFIDENCE_THRESHOLD,
            save=True,
            save_txt=True,
            save_conf=True,
            project=str(OUTPUT_DIR.parent),
            name=OUTPUT_DIR.name,
            exist_ok=True,
            device=device,
        )

        output_subfolder = OUTPUT_DIR / "predict"
        if not output_subfolder.exists():
            output_subfolder = OUTPUT_DIR
            
        print("\n--- Prediction Complete ---")
        print(f"Results saved in: {output_subfolder}")
        print("- Images with detections are saved as .jpg files.")
        print("- Detection features are in the 'labels' sub-directory as .txt files.")

    except Exception as e:
        print(f"\nAn error occurred during prediction: {e}")

def predict_on_webcam():
    """
    Loads a trained model and runs real-time object detection on a webcam feed.
    Press 'q' in the display window to quit.
    """
    print("--- Starting Webcam Inference ---")
    print("Press 'q' in the display window to quit.")

    # --- 1. Check for model ---
    if not WEIGHTS_PATH.exists():
        print(f"Error: Model weights not found at '{WEIGHTS_PATH}'")
        print("Please ensure your training run paths are correct.")
        return

    # --- 2. Load the model ---
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"Using device: {device}")

    try:
        model = YOLO(WEIGHTS_PATH)
    except Exception as e:
        print(f"Error loading model from '{WEIGHTS_PATH}'.")
        print(f"Underlying error: {e}")
        return

    # --- 3. Run Real-time Prediction ---
    print(f"Loading model: {WEIGHTS_PATH}")
    print("Starting webcam feed...")
    print("-" * 30)

    try:
        # stream=True is efficient for video feeds.
        # show=True displays the output window.
        results = model.track(
            source='0',  # '0' is the default webcam
            conf=CONFIDENCE_THRESHOLD,
            stream=True,
            show=True,
            device=device
        )
        
        # Iterate through the generator to process the stream2

        for _ in results:
            # The loop runs for each frame. 'show=True' handles the display.
            # You can add custom logic here to process results per frame.
            pass
            #print(dir(results))

    except Exception as e:
        print(f"\nAn error occurred during webcam prediction: {e}")
    
    print("--- Webcam feed stopped. ---")

if __name__ == "__main__":
    print("Choose prediction source:")
    print("1: Images from a folder")
    print("2: Live Webcam Feed")
    
    choice = input("Enter your choice (1 or 2): ")

    if choice == '1':
        predict_on_images()
    elif choice == '2':
        predict_on_webcam()
    else:
        print("Invalid choice. Please run the script again and enter '1' or '2'.")
