"""
Product recognition client (Camera 1)
상품 인식을 담당하는 클라이언트 (1번 노트북)
"""

import cv2
import socket
import json
import threading
import time
from detection.product_detector import ProductDetector
from detection.quality_inspector import QualityInspector
from config.config import Config


class ProductRecognitionClient:
    """상품 인식 클라이언트"""

    def __init__(self, server_host: str, server_tcp_port: int, server_udp_port: int):
        self.config = Config()
        self.server_host = server_host
        self.server_tcp_port = server_tcp_port
        self.server_udp_port = server_udp_port

        # 검출기 초기화
        self.product_detector = ProductDetector()
        self.quality_inspector = QualityInspector()

        # 네트워크 연결
        self.tcp_socket = None
        self.udp_socket = None

        # 카메라
        self.camera = None
        self.camera_id = self.config.product_camera_id

        # 상태
        self.running = False
        self.session_id = None
        self.check_interval = self.config.get("quality.check_interval", 2.0)

    def connect(self):
        """서버에 연결합니다"""
        # TCP 연결
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_socket.connect((self.server_host, self.server_tcp_port))
        print(f"Connected to TCP server at {self.server_host}:{self.server_tcp_port}")

        # UDP 소켓
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        print("UDP socket ready")

        # TCP 수신 스레드
        receive_thread = threading.Thread(target=self._receive_tcp_messages)
        receive_thread.daemon = True
        receive_thread.start()

    def start_cart_session(self):
        """카트 세션을 시작합니다"""
        message = {"type": "cart_start"}
        self._send_tcp_message(message)

    def start_recognition(self):
        """상품 인식을 시작합니다"""
        # 카메라 초기화
        self.camera = cv2.VideoCapture(self.camera_id)

        if not self.camera.isOpened():
            print("Error: Cannot open camera")
            return

        self.running = True
        print("Product recognition started")

        last_quality_check = time.time()

        while self.running:
            ret, frame = self.camera.read()
            if not ret:
                print("Error: Cannot read frame")
                break

            # 상품 감지
            detections = self.product_detector.detect_products(frame)

            # 품질 검사 (일정 간격마다)
            current_time = time.time()
            if current_time - last_quality_check >= self.check_interval:
                for detection in detections:
                    quality_result = self.quality_inspector.inspect_quality(
                        frame, detection["bbox"]
                    )
                    detection["quality"] = quality_result

                    # 손상된 상품 발견 시 알림
                    if quality_result["is_damaged"]:
                        print(
                            f"Warning: Damaged product detected - {detection['name']}"
                        )

                last_quality_check = current_time

            # 검출 결과를 UDP로 전송
            if detections:
                self._send_detection_data(detections)

            # 화면 표시
            annotated_frame = self.product_detector.draw_detections(frame, detections)
            cv2.imshow("Product Recognition", annotated_frame)

            # 'q' 키로 종료
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

        self.stop_recognition()

    def stop_recognition(self):
        """상품 인식을 중지합니다"""
        self.running = False

        if self.camera:
            self.camera.release()

        cv2.destroyAllWindows()
        print("Product recognition stopped")

    def _send_tcp_message(self, message: dict):
        """TCP 메시지를 전송합니다"""
        try:
            data = json.dumps(message) + "\n"
            self.tcp_socket.send(data.encode("utf-8"))
        except Exception as e:
            print(f"Error sending TCP message: {e}")

    def _send_detection_data(self, detections: list):
        """검출 데이터를 UDP로 전송합니다"""
        try:
            message = {
                "type": "product_detection",
                "session_id": self.session_id,
                "detections": detections,
                "timestamp": time.time(),
            }
            data = json.dumps(message).encode("utf-8")
            self.udp_socket.sendto(data, (self.server_host, self.server_udp_port))
        except Exception as e:
            print(f"Error sending detection data: {e}")

    def _receive_tcp_messages(self):
        """TCP 메시지를 수신합니다"""
        buffer = ""

        while True:
            try:
                data = self.tcp_socket.recv(4096).decode("utf-8")
                if not data:
                    break

                buffer += data

                while "\n" in buffer:
                    message, buffer = buffer.split("\n", 1)
                    if message:
                        self._process_tcp_message(message)

            except Exception as e:
                print(f"Error receiving TCP message: {e}")
                break

    def _process_tcp_message(self, message: str):
        """TCP 메시지를 처리합니다"""
        try:
            data = json.loads(message)

            # 세션 ID 수신
            if "session_id" in data:
                self.session_id = data["session_id"]
                print(f"Session ID received: {self.session_id}")

            print(f"Server response: {data}")

        except json.JSONDecodeError as e:
            print(f"Invalid JSON: {e}")

    def disconnect(self):
        """서버 연결을 종료합니다"""
        self.running = False

        if self.tcp_socket:
            self.tcp_socket.close()

        if self.udp_socket:
            self.udp_socket.close()

        print("Disconnected from server")


if __name__ == "__main__":
    # 사용 예시
    client = ProductRecognitionClient("localhost", 5000, 5001)

    try:
        client.connect()
        client.start_cart_session()
        time.sleep(1)  # 세션 ID 수신 대기
        client.start_recognition()
    except KeyboardInterrupt:
        print("\nStopping client...")
    finally:
        client.disconnect()
