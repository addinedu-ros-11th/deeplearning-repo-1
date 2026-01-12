#!/usr/bin/env python3
"""
Test script for integrated obstacle detection with tracking and risk assessment
Tests the new obstacle_v2 algorithm integration
"""
import sys
import cv2
import numpy as np
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from detectors.obstacle_dl import ObstacleDetector
from common.config import config


def test_obstacle_detector():
    """Test the new ObstacleDetector with tracking and risk engine"""
    print("=" * 60)
    print("Testing Integrated Obstacle Detection System")
    print("=" * 60)

    # Initialize detector
    print("\n[1] Initializing ObstacleDetector with tracking...")
    try:
        detector = ObstacleDetector()
        print("✅ ObstacleDetector initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize detector: {e}")
        import traceback

        traceback.print_exc()
        return

    # Create test frame
    print("\n[2] Creating test frame (640x480, black with white rectangle)...")
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    # Draw a simulated object (person/cart)
    cv2.rectangle(frame, (200, 150), (440, 400), (255, 255, 255), -1)
    cv2.putText(
        frame, "Test Object", (250, 270), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2
    )
    print("✅ Test frame created")

    # Run detection
    print("\n[3] Running detection with tracking and risk assessment...")
    try:
        result = detector.detect(frame)
        print("✅ Detection completed")

        print("\n" + "=" * 60)
        print("Detection Results:")
        print("=" * 60)
        print(
            f"Risk Level: {result.get('level')} ({['SAFE', 'CAUTION', 'WARN'][result.get('level', 0)]})"
        )
        print(f"Danger Level (legacy): {result.get('danger_level'):.2f}")
        print(f"Object Type: {result.get('object_type', 'N/A')}")
        print(f"Distance: {result.get('distance', 'N/A')} mm")
        print(f"Detected Objects: {len(result.get('objects', []))}")

        if result.get("highest_risk_object"):
            print("\nHighest Risk Object:")
            obj = result["highest_risk_object"]
            print(f"  - Track ID: {obj.get('track_id', 'N/A')}")
            print(f"  - Class: {obj.get('class_name', 'N/A')}")
            print(
                f"  - Risk: {obj.get('risk_name', 'N/A')} (score: {obj.get('score', 0):.2f})"
            )
            print(
                f"  - pTTC: {obj.get('pttc_s', 'N/A'):.2f}s"
                if obj.get("pttc_s", 1e9) < 1e6
                else "  - pTTC: ∞"
            )
            print(f"  - In Center: {obj.get('in_center', False)}")
            print(f"  - Approaching: {obj.get('approaching', False)}")

        print("\nAll Detected Objects:")
        for i, obj in enumerate(result.get("objects", []), 1):
            print(
                f"  [{i}] Track ID: {obj.get('track_id', -1)} | "
                f"Class: {obj.get('class_name', 'unknown')} | "
                f"Risk: {obj.get('risk_name', 'SAFE')} | "
                f"Conf: {obj.get('confidence', 0):.2f}"
            )

    except Exception as e:
        print(f"❌ Detection failed: {e}")
        import traceback

        traceback.print_exc()
        return

    # Test multiple frames (simulating tracking)
    print("\n[4] Testing tracking over multiple frames...")
    for i in range(5):
        # Move object closer (simulate approaching)
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        y_offset = i * 20
        cv2.rectangle(
            frame, (200, 150 + y_offset), (440, 400 + y_offset), (255, 255, 255), -1
        )

        result = detector.detect(frame)
        print(
            f"  Frame {i+1}: Level={result.get('level')} "
            f"({['SAFE', 'CAUTION', 'WARN'][result.get('level', 0)]}), "
            f"Objects={len(result.get('objects', []))}"
        )

    print("\n" + "=" * 60)
    print("✅ All tests completed successfully!")
    print("=" * 60)


def test_config_loading():
    """Test if risk engine config is loaded correctly"""
    print("\n[5] Testing configuration loading...")
    if config:
        print("✅ Config loaded")
        if hasattr(config.model.obstacle_detector, "risk"):
            print("✅ Risk engine config found:")
            risk_cfg = config.model.obstacle_detector.risk
            print(f"  - center_band_ratio: {risk_cfg.get('center_band_ratio', 'N/A')}")
            print(f"  - pttc_warn_s: {risk_cfg.get('pttc_warn_s', 'N/A')}")
            print(f"  - streak_warn: {risk_cfg.get('streak_warn', 'N/A')}")
        else:
            print("⚠️  Risk engine config not found (using defaults)")
    else:
        print("⚠️  Config not loaded")


if __name__ == "__main__":
    test_config_loading()
    test_obstacle_detector()
