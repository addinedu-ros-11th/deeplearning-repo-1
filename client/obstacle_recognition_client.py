"""
Obstacle recognition client (Camera 2)
장애물 인식을 담당하는 클라이언트 (2번 노트북)
"""

import cv2
import socket
import json
import threading
import time
from detection.obstacle_detector import ObstacleDetector
from config.config import Config


class ObstacleRecognitionClient:
    """장애물 인식 클라이언트"""

    def __init__(self, server_host: str, server_tcp_port: int, server_udp_port: int):
        self.config = Config()
        self.server_host = server_host
        self.server_tcp_port = server_tcp_port
        self.server_udp_port = server_udp_port

        # 검출기 초기화
        self.obstacle_detector = ObstacleDetector()

        # 네트워크 연결
        self.tcp_socket = None
        self.udp_socket = None

        # 카메라
        self.camera = None
        self.camera_id = self.config.obstacle_camera_id

        # 상태
        self.running = False
        self.session_id = None

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

    def set_session_id(self, session_id: str):
        """세션 ID를 설정합니다"""
        self.session_id = session_id
        print(f"Session ID set: {self.session_id}")

    def start_recognition(self):
        """장애물 인식을 시작합니다"""
        # 카메라 초기화
        self.camera = cv2.VideoCapture(self.camera_id)

        if not self.camera.isOpened():
            print("Error: Cannot open camera")
            return

        self.running = True
        print("Obstacle recognition started")

        while self.running:
            ret, frame = self.camera.read()
            if not ret:
                print("Error: Cannot read frame")
                break

            # 장애물 감지
            obstacles = self.obstacle_detector.detect_obstacles(frame)

            # 검출 결과를 UDP로 전송
            if obstacles:
                self._send_detection_data(obstacles)

                # 위험 경고 출력
                for obstacle in obstacles:
                    if obstacle["warning_level"] == "critical":
                        print(
                            f"⚠️ CRITICAL WARNING: {obstacle['type']} at {obstacle['distance']}m"
                        )
                    elif obstacle["warning_level"] == "warning":
                        print(
                            f"⚡ WARNING: {obstacle['type']} at {obstacle['distance']}m"
                        )

            # 화면 표시
            annotated_frame = self.obstacle_detector.draw_detections(frame, obstacles)
            cv2.imshow("Obstacle Recognition", annotated_frame)

            # 'q' 키로 종료
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

        self.stop_recognition()

    def stop_recognition(self):
        """장애물 인식을 중지합니다"""
        self.running = False

        if self.camera:
            self.camera.release()

        cv2.destroyAllWindows()
        print("Obstacle recognition stopped")

    def _send_detection_data(self, obstacles: list):
        """검출 데이터를 UDP로 전송합니다"""
        try:
            message = {
                "type": "obstacle_detection",
                "session_id": self.session_id,
                "obstacles": obstacles,
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
    client = ObstacleRecognitionClient("localhost", 5000, 5001)

    try:
        client.connect()
        # 세션 ID는 상품 인식 클라이언트로부터 받거나 별도로 설정
        client.set_session_id("test_session")
        client.start_recognition()
    except KeyboardInterrupt:
        print("\nStopping client...")
    finally:
        client.disconnect()
