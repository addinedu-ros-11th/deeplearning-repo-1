#!/usr/bin/env python3
"""
Complete System Integration Test
Tests all components with the new obstacle detection system
"""
import subprocess
import sys
import time
from pathlib import Path


def run_command(cmd, description):
    """Run a command and print results"""
    print(f"\n{'='*60}")
    print(f"🔧 {description}")
    print(f"{'='*60}")
    print(f"$ {cmd}\n")

    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)

    if result.returncode == 0:
        print(f"✅ {description} - SUCCESS")
    else:
        print(f"❌ {description} - FAILED (exit code: {result.returncode})")

    return result.returncode == 0


def main():
    print("=" * 60)
    print("🚀 Complete System Integration Test")
    print("   obstacle_v2 알고리즘 통합 검증")
    print("=" * 60)

    tests = [
        ("python3 test/test_ai_server_ready.py", "AI Server 준비 상태 확인"),
        ("python3 test/test_obstacle_integration.py", "Obstacle Detection 통합 테스트"),
    ]

    results = []
    for cmd, desc in tests:
        success = run_command(cmd, desc)
        results.append((desc, success))
        time.sleep(1)

    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for desc, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {desc}")

    print(f"\n결과: {passed}/{total} 테스트 통과")

    if passed == total:
        print("\n" + "=" * 60)
        print("🎉 모든 테스트 통과! 시스템 준비 완료!")
        print("=" * 60)
        print("\n다음 단계:")
        print("  1. 전체 시스템 실행:")
        print("     python test/run_hybrid_test.py")
        print("\n  2. 또는 개별 컴포넌트 실행:")
        print("     # Terminal 1: AI Server")
        print("     python src/ai_server.py")
        print("\n     # Terminal 2: Main Hub")
        print("     python src/main_hub.py")
        print("\n     # Terminal 3: Camera App")
        print("     python src/cart_camera_app.py")
        print("\n     # Terminal 4: UI App")
        print("     python src/cart_ui_app.py")
        return 0
    else:
        print("\n⚠️  일부 테스트 실패. 로그를 확인하세요.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
