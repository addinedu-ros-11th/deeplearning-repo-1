"""
TCP server for smart cart system
"""

import socket
import threading
import json
from typing import Dict, Callable
from config.config import Config


class TCPServer:
    """TCP 서버 클래스"""

    def __init__(self, message_handler: Callable = None):
        self.config = Config()
        self.host = self.config.server_tcp_host
        self.port = self.config.server_tcp_port
        self.server_socket = None
        self.running = False
        self.clients = {}
        self.message_handler = message_handler

    def start(self):
        """서버를 시작합니다"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)

        self.running = True
        print(f"TCP Server started on {self.host}:{self.port}")

        # 클라이언트 연결 수락 스레드
        accept_thread = threading.Thread(target=self._accept_clients)
        accept_thread.daemon = True
        accept_thread.start()

    def _accept_clients(self):
        """클라이언트 연결을 수락합니다"""
        while self.running:
            try:
                client_socket, address = self.server_socket.accept()
                print(f"Client connected from {address}")

                client_id = f"{address[0]}:{address[1]}"
                self.clients[client_id] = client_socket

                # 각 클라이언트를 별도 스레드에서 처리
                client_thread = threading.Thread(
                    target=self._handle_client, args=(client_socket, client_id)
                )
                client_thread.daemon = True
                client_thread.start()
            except Exception as e:
                if self.running:
                    print(f"Error accepting client: {e}")

    def _handle_client(self, client_socket: socket.socket, client_id: str):
        """클라이언트 메시지를 처리합니다"""
        buffer = ""

        while self.running:
            try:
                data = client_socket.recv(4096).decode("utf-8")
                if not data:
                    break

                buffer += data

                # 메시지 파싱 (줄바꿈으로 구분)
                while "\n" in buffer:
                    message, buffer = buffer.split("\n", 1)
                    if message:
                        self._process_message(client_socket, client_id, message)

            except Exception as e:
                print(f"Error handling client {client_id}: {e}")
                break

        # 클라이언트 연결 종료
        self._disconnect_client(client_id)

    def _process_message(
        self, client_socket: socket.socket, client_id: str, message: str
    ):
        """수신한 메시지를 처리합니다"""
        try:
            data = json.loads(message)

            if self.message_handler:
                response = self.message_handler(client_id, data)
                if response:
                    self.send_message(client_socket, response)
            else:
                print(f"Received from {client_id}: {data}")

        except json.JSONDecodeError as e:
            print(f"Invalid JSON from {client_id}: {e}")
        except Exception as e:
            print(f"Error processing message from {client_id}: {e}")

    def send_message(self, client_socket: socket.socket, message: Dict):
        """클라이언트에게 메시지를 전송합니다"""
        try:
            data = json.dumps(message) + "\n"
            client_socket.send(data.encode("utf-8"))
        except Exception as e:
            print(f"Error sending message: {e}")

    def broadcast_message(self, message: Dict, exclude_client: str = None):
        """모든 클라이언트에게 메시지를 브로드캐스트합니다"""
        for client_id, client_socket in list(self.clients.items()):
            if client_id != exclude_client:
                self.send_message(client_socket, message)

    def _disconnect_client(self, client_id: str):
        """클라이언트 연결을 종료합니다"""
        if client_id in self.clients:
            try:
                self.clients[client_id].close()
            except:
                pass
            del self.clients[client_id]
            print(f"Client disconnected: {client_id}")

    def stop(self):
        """서버를 종료합니다"""
        self.running = False

        # 모든 클라이언트 연결 종료
        for client_id in list(self.clients.keys()):
            self._disconnect_client(client_id)

        # 서버 소켓 종료
        if self.server_socket:
            self.server_socket.close()

        print("TCP Server stopped")
