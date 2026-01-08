#!/usr/bin/env python3
"""
카메라 장치 확인 스크립트
각 카메라 번호에 어떤 장치가 연결되어 있는지 확인
"""
import cv2


def check_camera(camera_id):
    """특정 카메라 ID를 열어서 정보 확인"""
    cap = cv2.VideoCapture(camera_id)

    if not cap.isOpened():
        print(f"카메라 {camera_id}: 연결 안됨")
        return False

    # 카메라 정보 가져오기
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    backend = cap.getBackendName()

    print(f"\n카메라 {camera_id}:")
    print(f"  - 해상도: {width}x{height}")
    print(f"  - FPS: {fps}")
    print(f"  - Backend: {backend}")

    # 프레임 캡처 테스트
    ret, frame = cap.read()
    if ret:
        print("  - 상태: 정상 작동")
        cv2.imshow(f"Camera {camera_id} - Press any key to continue", frame)
        cv2.waitKey(2000)  # 2초 표시
        cv2.destroyAllWindows()
    else:
        print("  - 상태: 프레임 캡처 실패")

    cap.release()
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("카메라 장치 확인")
    print("=" * 60)

    # 0~3번까지 확인
    for camera_id in range(4):
        check_camera(camera_id)

    print("\n" + "=" * 60)
    print("확인 완료!")
    print("내장 카메라는 보통 더 낮은 해상도를 가지고 있습니다.")
    print("=" * 60)
