"""
Configuration loader for Smart Cart system
"""

import os
import yaml
from pathlib import Path
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()


class Config:
    """시스템 설정을 관리하는 클래스"""

    _instance = None
    _config = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if self._config is None:
            self.load_config()

    def load_config(self, config_path: str = None):
        """설정 파일을 로드합니다"""
        if config_path is None:
            base_path = Path(__file__).parent
            config_path = base_path / "config.yaml"

        with open(config_path, "r", encoding="utf-8") as f:
            self._config = yaml.safe_load(f)

    def get(self, key: str, default=None):
        """설정 값을 가져옵니다"""
        keys = key.split(".")
        value = self._config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default

        return value

    @property
    def server_tcp_host(self):
        return self.get("server.tcp.host", "0.0.0.0")

    @property
    def server_tcp_port(self):
        return self.get("server.tcp.port", 5000)

    @property
    def server_udp_host(self):
        return self.get("server.udp.host", "0.0.0.0")

    @property
    def server_udp_port(self):
        return self.get("server.udp.port", 5001)

    @property
    def product_camera_id(self):
        return self.get("camera.product_recognition.device_id", 0)

    @property
    def obstacle_camera_id(self):
        return self.get("camera.obstacle_recognition.device_id", 0)

    @property
    def products(self):
        return self.get("products", {})
