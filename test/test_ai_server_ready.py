#!/usr/bin/env python3
"""
Quick test: Load ObstacleDetector and verify it's ready
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

print("=" * 60)
print("AI Server Obstacle Detector Readiness Check")
print("=" * 60)

# Test 1: Import modules
print("\n[1/4] Importing modules...")
try:
    from detectors.obstacle_dl import ObstacleDetector
    from common.config import config
    from common.protocols import DangerLevel, AIEvent

    print("✅ All modules imported successfully")
except Exception as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)

# Test 2: Check config
print("\n[2/4] Checking configuration...")
if config:
    print(f"✅ Config loaded")
    print(f"   - Obstacle model: {config.model.obstacle_detector.weights}")
    print(f"   - Confidence: {config.model.obstacle_detector.confidence}")
    if (
        hasattr(config.model.obstacle_detector, "risk")
        and config.model.obstacle_detector.risk
    ):
        print(f"   - Risk engine: ✅ Configured")
    else:
        print(f"   - Risk engine: ⚠️  Using defaults")
else:
    print("❌ Config not loaded")
    sys.exit(1)

# Test 3: Initialize detector
print("\n[3/4] Initializing ObstacleDetector...")
try:
    detector = ObstacleDetector()
    print("✅ ObstacleDetector initialized")
    print(f"   - Frame counter: {detector.frame_index}")
    print(f"   - FPS: {detector.last_fps}")
except Exception as e:
    print(f"❌ Initialization failed: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)

# Test 4: DangerLevel mapping
print("\n[4/4] Checking DangerLevel mapping...")
print(f"   - NORMAL (SAFE):    {DangerLevel.NORMAL} = {DangerLevel.NORMAL.value}")
print(f"   - CAUTION:          {DangerLevel.CAUTION} = {DangerLevel.CAUTION.value}")
print(f"   - CRITICAL (WARN):  {DangerLevel.CRITICAL} = {DangerLevel.CRITICAL.value}")
print("✅ DangerLevel enum ready")

print("\n" + "=" * 60)
print("🎉 All checks passed! AI Server is ready to use.")
print("=" * 60)
print("\n💡 Next step: python src/ai_server.py")
