#!/usr/bin/env python3
"""
Obstacle Detection System - Quick Verification Test
실제 프레임으로 동작 확인 (카메라 불필요)
"""
import sys
import cv2
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from detectors.obstacle_dl import ObstacleDetector
from detectors.risk_engine import RISK_SAFE, RISK_CAUTION, RISK_WARN


def create_test_frames():
    """테스트용 프레임 생성 (접근하는 사람 시뮬레이션)"""
    frames = []

    # 5개 프레임: 멀리 → 가까이 (객체가 커짐)
    for i in range(5):
        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        # 사람 크기를 점점 키우고 중앙으로 이동
        scale = 1 + (i * 0.3)  # 1.0 → 2.2
        y_offset = 200 - (i * 30)  # 위에서 아래로 이동

        # 중앙에 하얀 사각형 (사람 대체)
        center_x = 320
        width = int(100 * scale)
        height = int(150 * scale)

        x1 = center_x - width // 2
        y1 = y_offset
        x2 = center_x + width // 2
        y2 = y_offset + height

        cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 255, 255), -1)
        cv2.putText(
            frame, f"Frame {i+1}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2
        )

        frames.append(frame)

    return frames


def test_obstacle_sequence():
    """연속 프레임으로 위험도 변화 테스트"""
    print("=" * 70)
    print("장애물 감지 시퀀스 테스트 (접근하는 객체 시뮬레이션)")
    print("=" * 70)

    # Detector 초기화
    print("\n[1] ObstacleDetector 초기화...")
    detector = ObstacleDetector()
    print("✅ 초기화 완료")

    # 테스트 프레임 생성
    print("\n[2] 테스트 프레임 생성 (5 frames)...")
    frames = create_test_frames()
    print("✅ 프레임 생성 완료")

    # 연속 감지
    print("\n[3] 연속 감지 실행...")
    print("-" * 70)
    print(
        f"{'Frame':<8} {'Risk':<10} {'Level':<8} {'Objects':<10} {'Track IDs':<15} {'pTTC':<10}"
    )
    print("-" * 70)

    results_history = []

    for i, frame in enumerate(frames):
        result = detector.detect(frame)

        level = result.get("level", 0)
        risk_name = ["SAFE", "CAUTION", "WARN"][level]
        obj_count = len(result.get("objects", []))

        # Track IDs 수집
        track_ids = [obj.get("track_id", -1) for obj in result.get("objects", [])]
        track_str = ",".join(map(str, track_ids[:3]))  # 처음 3개만

        # pTTC
        highest_risk = result.get("highest_risk_object")
        pttc = "∞"
        if highest_risk:
            pttc_val = highest_risk.get("pttc_s", 1e9)
            if pttc_val < 1e6:
                pttc = f"{pttc_val:.1f}s"

        print(
            f"{i+1:<8} {risk_name:<10} {level:<8} {obj_count:<10} {track_str:<15} {pttc:<10}"
        )

        results_history.append(
            {
                "frame": i + 1,
                "level": level,
                "risk_name": risk_name,
                "objects": obj_count,
                "result": result,
            }
        )

    print("-" * 70)

    # 결과 분석
    print("\n[4] 결과 분석...")

    # 위험도 변화 확인
    levels = [r["level"] for r in results_history]
    max_level = max(levels)
    level_changes = sum(1 for i in range(1, len(levels)) if levels[i] != levels[i - 1])

    print(
        f"   - 최대 위험 레벨: {max_level} ({['SAFE', 'CAUTION', 'WARN'][max_level]})"
    )
    print(f"   - 위험도 변화 횟수: {level_changes}")
    print(
        f"   - 프레임별 레벨: {' → '.join([r['risk_name'] for r in results_history])}"
    )

    # Track ID 일관성 확인
    all_track_ids = set()
    for r in results_history:
        for obj in r["result"].get("objects", []):
            all_track_ids.add(obj.get("track_id", -1))

    print(
        f"   - 고유 Track ID 개수: {len(all_track_ids) - (1 if -1 in all_track_ids else 0)}"
    )
    print(f"   - Track IDs: {sorted([tid for tid in all_track_ids if tid != -1])}")

    # 마지막 프레임 상세 정보
    last_result = results_history[-1]["result"]
    print(f"\n[5] 마지막 프레임 상세 정보:")
    print(
        f"   - Risk Level: {last_result.get('level')} ({['SAFE', 'CAUTION', 'WARN'][last_result.get('level', 0)]})"
    )
    print(f"   - Object Type: {last_result.get('object_type', 'N/A')}")
    print(f"   - Distance: {last_result.get('distance', 'N/A')} mm")

    if last_result.get("highest_risk_object"):
        obj = last_result["highest_risk_object"]
        print(f"   - Highest Risk Object:")
        print(f"     • Track ID: {obj.get('track_id', -1)}")
        print(f"     • Risk Score: {obj.get('score', 0):.2f}")
        print(f"     • In Center: {obj.get('in_center', False)}")
        print(f"     • Approaching: {obj.get('approaching', False)}")

    print("\n" + "=" * 70)
    print("✅ 시퀀스 테스트 완료!")
    print("=" * 70)

    # 검증
    print("\n[검증]")
    if obj_count > 0:
        print("✅ 객체 감지 성공")
    else:
        print("⚠️  객체 미감지 (모델이 테스트 프레임을 인식하지 못함)")

    if len(all_track_ids) > 1:  # -1 제외
        print("✅ Track ID 할당 성공")
    else:
        print("⚠️  Track ID 미할당 (추적 실패)")

    print("\n💡 참고: 실제 YOLO 모델은 학습된 객체만 감지하므로")
    print("   테스트 프레임(흰색 사각형)을 인식하지 못할 수 있습니다.")
    print("   실제 카메라/비디오 테스트를 권장합니다.")

    return results_history


def test_danger_level_mapping():
    """DangerLevel 매핑 테스트"""
    print("\n\n" + "=" * 70)
    print("DangerLevel 매핑 테스트")
    print("=" * 70)

    from common.protocols import DangerLevel

    mappings = [
        (RISK_SAFE, DangerLevel.NORMAL, "SAFE/NORMAL"),
        (RISK_CAUTION, DangerLevel.CAUTION, "CAUTION"),
        (RISK_WARN, DangerLevel.CRITICAL, "WARN/CRITICAL"),
    ]

    print(f"\n{'Risk Engine':<15} {'Protocol':<15} {'설명':<20} {'일치':<10}")
    print("-" * 70)

    all_match = True
    for risk_val, danger_val, desc in mappings:
        match = risk_val == danger_val
        status = "✅" if match else "❌"
        print(f"{risk_val:<15} {danger_val:<15} {desc:<20} {status:<10}")
        all_match = all_match and match

    print("-" * 70)
    if all_match:
        print("✅ 모든 매핑 일치")
    else:
        print("❌ 매핑 불일치 발견")

    return all_match


if __name__ == "__main__":
    try:
        # Test 1: 시퀀스 테스트
        results = test_obstacle_sequence()

        # Test 2: 매핑 테스트
        mapping_ok = test_danger_level_mapping()

        print("\n\n" + "=" * 70)
        print("최종 결과")
        print("=" * 70)
        print("✅ 시퀀스 테스트 완료")
        print(
            f"{'✅' if mapping_ok else '❌'} DangerLevel 매핑 {'일치' if mapping_ok else '불일치'}"
        )
        print("\n다음 단계: 실제 카메라/비디오로 테스트")
        print("  python test/changhee/obstacle_v2/run_webcam.py --source 0 --show")

    except Exception as e:
        print(f"\n❌ 테스트 실패: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
