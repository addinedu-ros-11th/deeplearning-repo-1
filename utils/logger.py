"""
Logging utility module
"""

import logging
import os
from datetime import datetime
from config.config import Config


class Logger:
    """로깅 유틸리티 클래스"""

    _instance = None
    _logger = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if self._logger is None:
            self.setup_logger()

    def setup_logger(self):
        """로거 설정"""
        config = Config()

        log_level = config.get("logging.level", "INFO")
        log_dir = config.get("logging.log_dir", "logs")
        log_file = config.get("logging.log_file", "smart_cart.log")
        max_size = config.get("logging.max_size", 10485760)
        backup_count = config.get("logging.backup_count", 5)

        # 로그 디렉토리 생성
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        log_path = os.path.join(log_dir, log_file)

        # 로거 생성
        self._logger = logging.getLogger("SmartCart")
        self._logger.setLevel(getattr(logging, log_level))

        # 포매터
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # 파일 핸들러
        from logging.handlers import RotatingFileHandler

        file_handler = RotatingFileHandler(
            log_path, maxBytes=max_size, backupCount=backup_count
        )
        file_handler.setFormatter(formatter)
        self._logger.addHandler(file_handler)

        # 콘솔 핸들러
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self._logger.addHandler(console_handler)

    def debug(self, message: str):
        """디버그 로그"""
        self._logger.debug(message)

    def info(self, message: str):
        """정보 로그"""
        self._logger.info(message)

    def warning(self, message: str):
        """경고 로그"""
        self._logger.warning(message)

    def error(self, message: str):
        """에러 로그"""
        self._logger.error(message)

    def critical(self, message: str):
        """치명적 에러 로그"""
        self._logger.critical(message)
