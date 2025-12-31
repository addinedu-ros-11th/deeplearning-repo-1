import cv2
import time
import threading

from network.udp_handler import UDPFrameSender
from common.config import config
from utils.image_proc import ImageProcessor


class CartEdgeApp:
    """
    PC3 Edge Application
    - Captures two cameras
    - Sends frames via UDP
    """

    def __init__(self):
        if config is None:
            raise RuntimeError("Configuration could not be loaded. Exiting.")

        # Get config values
        main_hub_ip = config.network.pc2_main.ip
        front_cam_port = config.network.pc2_main.udp_front_cam_port
        cart_cam_port = config.network.pc2_main.udp_cart_cam_port

        # Camera resolution and FPS
        self.img_width, self.img_height = config.app.camera.resolution
        self.fps = config.app.camera.fps

        # -------------------------
        # UDP Senders (port = meaning)
        # -------------------------
        self.front_sender = UDPFrameSender(
            main_hub_ip,
            front_cam_port,
            jpeg_quality=80,
        )
        self.cart_sender = UDPFrameSender(
            main_hub_ip,
            cart_cam_port,
            jpeg_quality=85,
        )

        # -------------------------
        # Camera devices
        # -------------------------
        self.front_cap = cv2.VideoCapture(2)
        self.cart_cap = cv2.VideoCapture(0)

        if not self.front_cap.isOpened():
            raise RuntimeError("Front camera not available")
        if not self.cart_cap.isOpened():
            raise RuntimeError("Cart camera not available")

        self.is_running = True

    # =========================
    # Streaming loops
    # =========================
    def _stream_camera(
        self,
        cap: cv2.VideoCapture,
        sender: UDPFrameSender,
        resize_shape: tuple,
        fps: float,
        name: str = "",
    ):
        interval = 1.0 / fps
        print(f"{name} camera streaming started")

        while self.is_running:
            ret, frame = cap.read()
            if not ret:
                time.sleep(interval)
                continue

            frame = ImageProcessor.resize_for_ai(frame, resize_shape)
            sender.send_frame(frame)

            time.sleep(interval)

    def stream_front_camera(self):
        """전방 카메라 (장애물 인식용)"""
        self._stream_camera(
            cap=self.front_cap,
            sender=self.front_sender,
            resize_shape=(self.img_width, self.img_height),
            fps=self.fps,
            name="Front",
        )

    def stream_cart_camera(self):
        """카트 내부 카메라 (상품 인식용)"""
        self._stream_camera(
            cap=self.cart_cap,
            sender=self.cart_sender,
            resize_shape=(self.img_width, self.img_height),
            fps=self.fps,
            name="Cart",
        )

    # =========================
    # Lifecycle
    # =========================
    def run(self):
        front_thread = threading.Thread(
            target=self.stream_front_camera,
            daemon=True,
        )
        cart_thread = threading.Thread(
            target=self.stream_cart_camera,
            daemon=True,
        )

        front_thread.start()
        cart_thread.start()

        try:
            while self.is_running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        print("Stopping camera streams...")
        self.is_running = False
        time.sleep(0.5)

        self.front_cap.release()
        self.cart_cap.release()


if __name__ == "__main__":
    app = CartEdgeApp()
    app.run()
