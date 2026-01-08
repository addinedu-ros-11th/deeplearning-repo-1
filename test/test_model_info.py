#!/usr/bin/env python3
"""
Test YOLO model to see what it detects
"""
import sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ultralytics import YOLO
from common.config import config


def check_model(model_path):
    print(f"\n{'='*60}")
    print(f"Testing model: {model_path}")
    print(f"{'='*60}")

    try:
        model = YOLO(model_path)
        print("✓ Model loaded successfully")

        # Model info
        print("\nModel Info:")
        print(f"  - Type: {model.task}")
        print(f"  - Classes: {model.names}")
        print(
            f"  - Number of classes: {len(model.names) if model.names else 'Unknown'}"
        )

        # Create a test image
        test_img = np.zeros((640, 640, 3), dtype=np.uint8)

        # Test prediction with different confidence thresholds
        for conf in [0.1, 0.3, 0.5, 0.7]:
            print(f"\n--- Testing with conf={conf} ---")
            results = model.predict(test_img, conf=conf, verbose=False)

            if results is None:
                print("  ❌ Results is None")
            elif len(results) == 0:
                print("  ⚠ Results is empty")
            elif results[0].boxes is None:
                print("  ⚠ No boxes attribute")
            elif len(results[0].boxes) == 0:
                print("  ✓ No detections (expected for blank image)")
            else:
                print(f"  ✓ {len(results[0].boxes)} detections")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    # Test best.pt
    check_model("models/product_recognizer/best.pt")

    # Test other models for comparison
    print("\n\n")
    check_model("models/product_recognizer/product_yolov8s.pt")

    print(f"\n{'='*60}")
    print("Current config:")
    print(f"  - Model: {config.model.product_recognizer.weights}")
    print(f"  - Confidence: {config.model.product_recognizer.confidence}")
    print(f"{'='*60}")
