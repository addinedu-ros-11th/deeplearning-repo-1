"""
UDP server for smart cart system (for real-time streaming)
"""

import socket
import threading
import json
from typing import Callable
from config.config import Config


class UDPServer:
    """UDP 서버 클래스 (실시간 데이터 스트리밍용)"""

    def __init__(self, message_handler: Callable = None):
        self.config = Config()
        self.host = self.config.server_udp_host
        self.port = self.config.server_udp_port
        self.server_socket = None
        self.running = False
        self.message_handler = message_handler

    def start(self):
        """서버를 시작합니다"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server_socket.bind((self.host, self.port))

        self.running = True
        print(f"UDP Server started on {self.host}:{self.port}")

        # 메시지 수신 스레드
        receive_thread = threading.Thread(target=self._receive_messages)
        receive_thread.daemon = True
        receive_thread.start()

    def _receive_messages(self):
        """메시지를 수신합니다"""
        while self.running:
            try:
                data, address = self.server_socket.recvfrom(65535)
                self._process_message(data, address)
            except Exception as e:
                if self.running:
                    print(f"Error receiving UDP message: {e}")

    def _process_message(self, data: bytes, address: tuple):
        """수신한 메시지를 처리합니다"""
        try:
            message = json.loads(data.decode("utf-8"))

            if self.message_handler:
                response = self.message_handler(address, message)
                if response:
                    self.send_message(address, response)
            else:
                print(f"Received from {address}: {message}")

        except json.JSONDecodeError as e:
            print(f"Invalid JSON from {address}: {e}")
        except Exception as e:
            print(f"Error processing UDP message from {address}: {e}")

    def send_message(self, address: tuple, message: dict):
        """특정 주소로 메시지를 전송합니다"""
        try:
            data = json.dumps(message).encode("utf-8")
            self.server_socket.sendto(data, address)
        except Exception as e:
            print(f"Error sending UDP message: {e}")

    def broadcast_message(self, message: dict, broadcast_address: str = "<broadcast>"):
        """브로드캐스트 메시지를 전송합니다"""
        try:
            # 브로드캐스트 활성화
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

            data = json.dumps(message).encode("utf-8")
            self.server_socket.sendto(data, (broadcast_address, self.port))
        except Exception as e:
            print(f"Error broadcasting UDP message: {e}")

    def stop(self):
        """서버를 종료합니다"""
        self.running = False

        if self.server_socket:
            self.server_socket.close()

        print("UDP Server stopped")
