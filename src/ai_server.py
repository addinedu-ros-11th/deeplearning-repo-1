# ai_server.py
# ai_server.py
import threading
import time
import cv2
import numpy as np

from network.udp_handler import UDPFrameReceiver
from network.tcp_client import TCPClient
from common.config import config
from common.protocols import (
    Protocol,
    AIEvent,
    DangerLevel,
)
from detectors.obstacle_dl_v2 import ObstacleDetectorV2  # Use V2
from detectors.product_dl import ProductRecognizer


class AIServer:
    """
    AI Server (PC1)

    - Receives frames via UDP from Main PC2.
    - Performs inference on frames.
    - Pushes events (e.g., product detected, obstacle detected) to Main PC2.
    """

    def __init__(self):
        print("Initializing AI Server...")
        if config is None:
            raise RuntimeError("Configuration could not be loaded. Exiting.")

        # -------------------------
        # Models
        # -------------------------
        self.obstacle_model = ObstacleDetectorV2() # Use ObstacleDetectorV2
        self.product_model = ProductRecognizer()

        # -------------------------
        # Latest frame buffers & Locks
        # -------------------------
        self._latest_obstacle_bytes = None
        self._obstacle_lock = threading.Lock()

        self._latest_product_bytes = None
        self._product_lock = threading.Lock()

        # -------------------------
        # UDP receivers for frame data
        # -------------------------
        self.obstacle_receiver = UDPFrameReceiver(
            "0.0.0.0", config.network.pc1_ai.udp_port_front
        )
        self.product_receiver = UDPFrameReceiver(
            "0.0.0.0", config.network.pc1_ai.udp_port_cart
        )
        print(
            f"UDP receivers listening on ports {config.network.pc1_ai.udp_port_front} and {config.network.pc1_ai.udp_port_cart}"
        )

        # -------------------------
        # TCP client to push events to Main Hub
        # -------------------------
        main_hub_ip = config.network.pc2_main.ip
        main_hub_port = config.network.pc2_main.event_port
        self.event_client = TCPClient(main_hub_ip, main_hub_port)
        print(f"Event client configured to connect to {main_hub_ip}:{main_hub_port}")

    # =========================
    # UDP receive loops
    # =========================
    def _obstacle_udp_loop(self):
        print("Obstacle UDP loop started.")
        for jpeg_bytes in self.obstacle_receiver.receive_packets():
            with self._obstacle_lock:
                self._latest_obstacle_bytes = jpeg_bytes

    def _product_udp_loop(self):
        print("Product UDP loop started.")
        packet_count = 0
        for jpeg_bytes in self.product_receiver.receive_packets():
            packet_count += 1
            if packet_count % 30 == 0:  # Every 30 frames
                print(
                    f"[AI Server] Received {packet_count} product frames, latest size: {len(jpeg_bytes)} bytes"
                )
            with self._product_lock:
                self._latest_product_bytes = jpeg_bytes

    # =========================
    # Inference loops
    # =========================
    def _obstacle_inference_loop(self):
        print("Obstacle inference loop started.")
        last_sent_level = None  # Track last sent level to avoid redundant events

        while True:
            with self._obstacle_lock:
                jpeg = self._latest_obstacle_bytes
                self._latest_obstacle_bytes = None # Consume the latest frame

            if jpeg is None:
                time.sleep(0.01) # Shorter sleep to react faster if frames are frequent
                continue

            frame = self._decode(jpeg)
            if frame is None:
                continue

            result = self.obstacle_model.detect(frame)
            level = DangerLevel(result.get("level", 0))

            # Send event only when level changes (including SAFE transitions)
            # This prevents spamming the Main Hub with identical states
            if level != last_sent_level:
                self._push_event(AIEvent.OBSTACLE_DANGER, result)
                last_sent_level = level

            time.sleep(0.05)  # Control inference frequency

    def _product_inference_loop(self):
        print("Product inference loop started.")
        while True:
            with self._product_lock:
                jpeg = self._latest_product_bytes

            if jpeg is None:
                time.sleep(0.1)
                continue

            frame = self._decode(jpeg)
            if frame is None:
                continue

            # 모션 트리거 방식 사용 (카트에 넣는 순간만 감지)
            result = self.product_model.recognize_with_trigger(frame, time.time())

            status = result.get("status")
            main_event = result.get("main_event")
            all_detections = result.get("all_detections", [])

            # 디버그: 전체 상태 출력
            print(f"[AI Server] Status: {status}, Detections: {len(all_detections)}")

            # "added" 상태일 때만 이벤트 푸시 (추적 중에는 이벤트 안 보냄)
            if status == "added" and main_event:
                product_id = main_event.get("product_id")
                confidence = main_event.get("confidence", 0.0)

                print(
                    f"[AI Server] 🎉 Product ADDED: product_id={product_id}, confidence={confidence:.2f}, movement={main_event.get('movement', 0):.1f}px"
                )

                # 카트에 추가된 순간만 이벤트 푸시
                self._push_event(
                    AIEvent.PRODUCT_DETECTED,
                    {"product_id": product_id, "confidence": confidence},
                )
            elif status == "tracking" and main_event:
                # 추적 중 (디버그 로그)
                product_id = main_event.get("product_id")
                zone = main_event.get("zone", "")
                print(f"[AI Server] 📦 Tracking product_id={product_id}, zone={zone}")
            elif status == "none":
                # 아무것도 감지 안됨
                if len(all_detections) > 0:
                    print(
                        "[AI Server] ⏸️  Detections exist but no main event (cooldown or other)"
                    )
                # else: 아무것도 없음 (로그 안 함)

            time.sleep(0.1)  # Control inference frequency

    # =========================
    # Utilities
    # =========================
    @staticmethod
    def _decode(jpeg_bytes: bytes):
        try:
            arr = np.frombuffer(jpeg_bytes, np.uint8)
            return cv2.imdecode(arr, cv2.IMREAD_COLOR)
        except Exception as e:
            print(f"Error decoding frame: {e}")
            return None

    # =========================
    # PUSH (AI → Main PC2)
    # =========================
    def _push_event(self, event: AIEvent, data: dict):
        try:
            msg = Protocol.ai_event(event, data)
            self.event_client.send_request(msg)
        except Exception as e:
            print(f"Failed to push AI event: {e}")

    # =========================
    # Lifecycle
    # =========================
    def run(self):
        print("Starting AI Server threads...")
        threads = [
            threading.Thread(target=self._obstacle_udp_loop, daemon=True),
            threading.Thread(target=self._product_udp_loop, daemon=True),
            threading.Thread(target=self._obstacle_inference_loop, daemon=True),
            threading.Thread(target=self._product_inference_loop, daemon=True),
        ]

        for t in threads:
            t.start()

        print("AI Server is running.")
        # Keep main thread alive
        for t in threads:
            t.join()


if __name__ == "__main__":
    AIServer().run()
