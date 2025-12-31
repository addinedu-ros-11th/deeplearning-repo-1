#!/usr/bin/env python3
"""
최적화된 하이브리드 카메라 앱 (디버그 박스 포함)
- cv2.imshow()를 메인 스레드에서 처리
- 웹캠에서 상품 인식 바운딩 박스 표시
"""
import cv2
import time
import threading
import sys
from pathlib import Path
from queue import Queue

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from network.udp_handler import UDPFrameSender
from common.config import config
from utils.image_proc import ImageProcessor
from detectors.product_dl import ProductRecognizer


class OptimizedHybridCameraApp:
    """최적화된 하이브리드 카메라 앱"""

    def __init__(self, front_cam_id=2, cart_cam_id=0):
        if config is None:
            raise RuntimeError("Configuration could not be loaded. Exiting.")

        # Get config values
        main_hub_ip = config.network.pc2_main.ip
        front_cam_port = config.network.pc2_main.udp_front_cam_port
        cart_cam_port = config.network.pc2_main.udp_cart_cam_port

        # Camera resolution and FPS
        self.img_width, self.img_height = config.app.camera.resolution
        self.fps = config.app.camera.fps

        # UDP Senders
        self.front_sender = UDPFrameSender(main_hub_ip, front_cam_port, jpeg_quality=70)
        self.cart_sender = UDPFrameSender(main_hub_ip, cart_cam_port, jpeg_quality=70)

        # Front Webcam
        self.front_cam_id = front_cam_id
        self.front_cap = cv2.VideoCapture(front_cam_id)
        if not self.front_cap.isOpened():
            raise RuntimeError(f"Cannot open front webcam (device {front_cam_id})")

        # 웹캠 해상도 설정
        self.front_cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.front_cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        self.video_interval = 1.0 / self.fps

        # Cart Webcam
        self.cart_cam_id = cart_cam_id
        self.cart_cap = cv2.VideoCapture(cart_cam_id)
        if not self.cart_cap.isOpened():
            raise RuntimeError(f"Cannot open cart webcam (device {cart_cam_id})")

        # 웹캠 해상도 설정
        self.cart_cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cart_cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        # Product recognizer for debug visualization
        print("상품 인식 모델 로딩 중...")
        self.product_recognizer = ProductRecognizer()
        print("모델 로딩 완료!")

        # Frame queues for display
        self.front_frame_queue = Queue(maxsize=2)
        self.cart_frame_queue = Queue(maxsize=2)

        self.is_running = True

        print("=" * 60)
        print("최적화된 하이브리드 카메라 앱 (디버그 박스)")
        print(f"  전방: 웹캠 {front_cam_id} (장애물 감지)")
        print(f"  카트: 웹캠 {cart_cam_id} (상품 인식 바운딩 박스 표시)")
        print(f"  Main Hub: {main_hub_ip}")
        print("=" * 60)

    def _capture_video_thread(self):
        """전방 웹캠 캡처 스레드"""
        print(f"[전방] 웹캠 {self.front_cam_id} 캡처 시작")
        while self.is_running:
            ret, frame = self.front_cap.read()

            if not ret:
                time.sleep(0.1)
                continue

            # 리사이즈
            resized = ImageProcessor.resize_for_ai(
                frame, (self.img_width, self.img_height)
            )

            # UDP 전송
            self.front_sender.send_frame(resized)

            # 디스플레이 큐에 추가
            if not self.front_frame_queue.full():
                self.front_frame_queue.put(resized.copy())

            time.sleep(self.video_interval)

        print("[전방] 캡처 종료")

    def _capture_webcam_thread(self):
        """웹캠 캡처 스레드 (상품 인식 포함 - 모션 트리거)"""
        print("[카트] 웹캠 캡처 시작 (ROI + 모션 트리거 활성화)")
        interval = 1.0 / self.fps
        frame_count = 0
        last_result = None

        while self.is_running:
            ret, frame = self.cart_cap.read()
            if not ret:
                time.sleep(interval)
                continue

            frame_count += 1

            # 리사이즈
            resized = ImageProcessor.resize_for_ai(
                frame, (self.img_width, self.img_height)
            )

            # UDP 전송
            self.cart_sender.send_frame(resized)

            # 디스플레이용 프레임
            display_frame = resized.copy()

            # 상품 인식 (모션 트리거 방식)
            if frame_count % 2 == 0:  # 2프레임마다 인식 (더 빠른 반응)
                try:
                    current_time = time.time()
                    last_result = self.product_recognizer.recognize_with_trigger(
                        resized, current_time
                    )
                except Exception as e:
                    last_result = {"status": "error", "message": str(e)}

            # 시스템 상태 표시
            zones = self.product_recognizer.get_debug_zones(display_frame.shape)
            h, w = display_frame.shape[:2]

            # 상태 정보 표시 (상단)
            info_text = [
                f"Tracking: {zones['tracked_count']}",
                f"Cooldown: {zones['cooldown_count']}",
                f"Duration: {zones['required_duration']:.1f}s",
            ]
            y_offset = 30
            for text in info_text:
                cv2.putText(
                    display_frame,
                    text,
                    (10, y_offset),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 0),
                    2,
                )
                y_offset += 30

            # 인식 결과 시각화
            if last_result:
                status = last_result.get("status")
                main_event = last_result.get("main_event")
                all_detections = last_result.get("all_detections", [])

                # 모든 감지된 물체들의 바운딩 박스 표시
                for detection in all_detections:
                    bbox = detection.get("bbox")
                    if not bbox:
                        continue

                    x1, y1, x2, y2 = map(int, bbox)
                    product_id = detection.get("product_id")
                    confidence = detection.get("confidence", 0.0)
                    state = detection.get("state", "unknown")

                    # 상태별 색상 및 라벨 설정
                    if state == "added":
                        # 🎉 카트에 추가됨 (주황색)
                        color = (0, 165, 255)
                        thickness = 4
                        duration = detection.get("duration", 0.0)
                        label = f"ADDED! ID:{product_id} ({duration:.1f}s)"
                    elif state == "tracking":
                        # 추적 중 (노란색)
                        color = (0, 255, 255)
                        thickness = 3
                        duration = detection.get("duration", 0.0)
                        remaining = detection.get("remaining", 0.0)
                        label = (
                            f"Tracking ID:{product_id} {duration:.1f}s/{remaining:.1f}s"
                        )
                    elif state == "cooldown":
                        # 쿨다운 중 (회색)
                        color = (128, 128, 128)
                        thickness = 2
                        cooldown_time = detection.get("cooldown_remaining", 0)
                        label = f"Cooldown ID:{product_id} ({cooldown_time:.1f}s)"
                    else:
                        # 기타 (초록색)
                        color = (0, 255, 0)
                        thickness = 2
                        label = f"ID:{product_id} {confidence:.2f}"

                    # 바운딩 박스 그리기
                    cv2.rectangle(display_frame, (x1, y1), (x2, y2), color, thickness)

                    # 레이블 배경
                    label_size, _ = cv2.getTextSize(
                        label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2
                    )
                    cv2.rectangle(
                        display_frame,
                        (x1, y1 - label_size[1] - 10),
                        (x1 + label_size[0], y1),
                        color,
                        -1,
                    )

                    # 레이블 텍스트
                    text_color = (255, 255, 255) if state == "added" else (0, 0, 0)
                    cv2.putText(
                        display_frame,
                        label,
                        (x1, y1 - 5),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        text_color,
                        2,
                    )

                # 화면 상단 메시지
                if status == "added" and main_event:
                    # 추가됨 알림
                    cv2.putText(
                        display_frame,
                        f"PRODUCT ADDED TO CART!",
                        (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.8,
                        (0, 165, 255),
                        2,
                    )
                elif status == "tracking" and main_event:
                    # 추적 중 메시지
                    zone = main_event.get("zone", "")
                    cv2.putText(
                        display_frame,
                        f"Tracking... ({zone})",
                        (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (0, 255, 255),
                        2,
                    )
                elif status == "none":
                    # 인식 안됨
                    if len(all_detections) == 0:
                        cv2.putText(
                            display_frame,
                            "Waiting for product...",
                            (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.7,
                            (128, 128, 128),
                            2,
                        )

                elif status == "error":
                    cv2.putText(
                        display_frame,
                        f"Error: {last_result.get('message', '')[:40]}",
                        (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (0, 0, 255),
                        2,
                    )
                else:
                    # 인식 안됨
                    cv2.putText(
                        display_frame,
                        "Waiting for product...",
                        (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (128, 128, 128),
                        2,
                    )

            # 추적 정보 표시
            info_y = 60
            cv2.putText(
                display_frame,
                f"Tracked: {zones['tracked_count']} | Cooldown: {zones['cooldown_count']}",
                (10, info_y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                1,
            )

            # FPS 표시
            cv2.putText(
                display_frame,
                f"Frame: {frame_count}",
                (10, display_frame.shape[0] - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                1,
            )

            # 디스플레이 큐에 추가
            if not self.cart_frame_queue.full():
                self.cart_frame_queue.put(display_frame)

            time.sleep(interval)

        print("[카트] 캡처 종료")

    def run(self):
        """메인 실행"""
        # 캡처 스레드 시작
        front_thread = threading.Thread(target=self._capture_video_thread, daemon=True)
        cart_thread = threading.Thread(target=self._capture_webcam_thread, daemon=True)

        front_thread.start()
        cart_thread.start()

        print("\n화면 표시 시작 ('q' 키로 종료)...")

        # 메인 스레드에서 화면 표시
        try:
            while self.is_running:
                # 전방 카메라 프레임 표시
                if not self.front_frame_queue.empty():
                    front_frame = self.front_frame_queue.get()
                    cv2.imshow("Front Camera (Obstacle)", front_frame)

                # 카트 카메라 프레임 표시 (바운딩 박스 포함)
                if not self.cart_frame_queue.empty():
                    cart_frame = self.cart_frame_queue.get()
                    cv2.imshow("Cart Camera (Product - Debug)", cart_frame)

                # 키 입력 확인
                key = cv2.waitKey(1) & 0xFF
                if key == ord("q"):
                    print("\n종료 요청...")
                    self.is_running = False
                    break

        except KeyboardInterrupt:
            print("\n\n종료 요청...")
            self.is_running = False

        # 스레드 종료 대기
        front_thread.join(timeout=2)
        cart_thread.join(timeout=2)

        # 리소스 정리
        self.front_cap.release()
        self.cart_cap.release()
        cv2.destroyAllWindows()
        print("종료 완료")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="최적화된 하이브리드 카메라 앱 (듀얼 웹캠)"
    )
    parser.add_argument(
        "--front",
        type=int,
        default=0,
        help="전방 카메라 장치 번호 (기본값: 0)",
    )
    parser.add_argument(
        "--cart",
        type=int,
        default=1,
        help="카트 카메라 장치 번호 (기본값: 1)",
    )

    args = parser.parse_args()

    try:
        app = OptimizedHybridCameraApp(front_cam_id=args.front, cart_cam_id=args.cart)
        app.run()
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
