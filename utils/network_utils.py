"""
Network utility functions
"""

import socket


def get_local_ip() -> str:
    """
    로컬 IP 주소 가져오기

    Returns:
        로컬 IP 주소
    """
    try:
        # 더미 UDP 연결을 통해 로컬 IP 확인
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return "127.0.0.1"


def check_port_available(host: str, port: int) -> bool:
    """
    포트 사용 가능 여부 확인

    Args:
        host: 호스트
        port: 포트 번호

    Returns:
        사용 가능 여부
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((host, port))
            return True
    except OSError:
        return False


def check_server_connection(host: str, port: int, timeout: float = 3.0) -> bool:
    """
    서버 연결 가능 여부 확인

    Args:
        host: 서버 호스트
        port: 서버 포트
        timeout: 타임아웃 (초)

    Returns:
        연결 가능 여부
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            s.connect((host, port))
            return True
    except (socket.timeout, socket.error):
        return False
