"""
Smart Cart System - Main Entry Point
스마트 카트 시스템 메인 실행 파일
"""

import argparse
import sys
from server.tcp_server import TCPServer
from server.udp_server import UDPServer
from server.message_handler import MessageHandler
from config.config import Config
from database.db_manager import DBManager
from utils.logger import Logger


def start_server():
    """서버 시작"""
    logger = Logger()
    config = Config()

    logger.info("=" * 60)
    logger.info("Smart Cart System Server Starting...")
    logger.info("=" * 60)

    # 데이터베이스 초기화
    try:
        logger.info("Initializing database...")
        db_manager = DBManager()
        db_manager.initialize_database()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        return

    # 메시지 핸들러
    message_handler = MessageHandler()

    # TCP 서버 시작
    try:
        logger.info("Starting TCP server...")
        tcp_server = TCPServer(message_handler.handle_tcp_message)
        tcp_server.start()
    except Exception as e:
        logger.error(f"Failed to start TCP server: {e}")
        return

    # UDP 서버 시작
    try:
        logger.info("Starting UDP server...")
        udp_server = UDPServer(message_handler.handle_udp_message)
        udp_server.start()
    except Exception as e:
        logger.error(f"Failed to start UDP server: {e}")
        tcp_server.stop()
        return

    logger.info("=" * 60)
    logger.info("Smart Cart System Server is running")
    logger.info(f"TCP Server: {config.server_tcp_host}:{config.server_tcp_port}")
    logger.info(f"UDP Server: {config.server_udp_host}:{config.server_udp_port}")
    logger.info("Press Ctrl+C to stop the server")
    logger.info("=" * 60)

    try:
        # 서버 실행 유지
        import time

        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("\nShutting down server...")
        tcp_server.stop()
        udp_server.stop()
        logger.info("Server stopped")


def start_product_client(server_host: str):
    """상품 인식 클라이언트 시작"""
    from client.product_recognition_client import ProductRecognitionClient

    config = Config()
    client = ProductRecognitionClient(
        server_host, config.server_tcp_port, config.server_udp_port
    )

    try:
        client.connect()
        client.start_cart_session()
        import time

        time.sleep(1)  # 세션 ID 수신 대기
        client.start_recognition()
    except KeyboardInterrupt:
        print("\nStopping product recognition client...")
    finally:
        client.disconnect()


def start_obstacle_client(server_host: str, session_id: str = None):
    """장애물 인식 클라이언트 시작"""
    from client.obstacle_recognition_client import ObstacleRecognitionClient

    config = Config()
    client = ObstacleRecognitionClient(
        server_host, config.server_tcp_port, config.server_udp_port
    )

    try:
        client.connect()
        if session_id:
            client.set_session_id(session_id)
        else:
            print("Warning: No session ID provided. Please set it manually.")
        client.start_recognition()
    except KeyboardInterrupt:
        print("\nStopping obstacle recognition client...")
    finally:
        client.disconnect()


def start_user_ui(server_host: str):
    """사용자 UI 시작"""
    from PyQt6.QtWidgets import QApplication
    from gui.user_ui import UserUI

    config = Config()
    app = QApplication(sys.argv)
    window = UserUI(server_host, config.server_tcp_port)
    window.show()
    sys.exit(app.exec())


def start_admin_ui(server_host: str):
    """관리자 UI 시작"""
    from PyQt6.QtWidgets import QApplication
    from gui.admin_ui import AdminUI

    config = Config()
    app = QApplication(sys.argv)
    window = AdminUI(server_host, config.server_tcp_port)
    window.show()
    sys.exit(app.exec())


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description="Smart Cart System")
    parser.add_argument(
        "mode",
        choices=["server", "product-client", "obstacle-client", "user-ui", "admin-ui"],
        help="실행 모드 선택",
    )
    parser.add_argument(
        "--host",
        default="localhost",
        help="서버 호스트 주소 (클라이언트/UI 모드에서 사용)",
    )
    parser.add_argument("--session-id", help="세션 ID (장애물 클라이언트에서 사용)")

    args = parser.parse_args()

    if args.mode == "server":
        start_server()
    elif args.mode == "product-client":
        start_product_client(args.host)
    elif args.mode == "obstacle-client":
        start_obstacle_client(args.host, args.session_id)
    elif args.mode == "user-ui":
        start_user_ui(args.host)
    elif args.mode == "admin-ui":
        start_admin_ui(args.host)


if __name__ == "__main__":
    main()
