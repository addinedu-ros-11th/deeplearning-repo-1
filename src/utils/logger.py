import logging
import os

class SystemLogger:
    def __init__(self, name="SmartCart", log_file="logs/system.log"):
        """
        시스템 이벤트를 기록하기 위한 로거 설정
        """
        # logs 디렉토리가 없으면 생성
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)

        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)

        # 이미 핸들러가 설정되어 있다면 중복 추가 방지
        if not self.logger.handlers:
            # 1. 파일 핸들러 (로그 파일에 저장)
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_format = logging.Formatter('%(asctime)s - [%(levelname)s] - %(name)s - %(message)s')
            file_handler.setFormatter(file_format)

            # 2. 콘솔 핸들러 (터미널 출력)
            console_handler = logging.StreamHandler()
            console_format = logging.Formatter('%(levelname)s: %(message)s')
            console_handler.setFormatter(console_format)

            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)

    def log_event(self, event_type, message):
        """
        특정 이벤트 타입별로 포맷팅하여 기록
        event_type: SCAN, OBSTACLE, SESSION, ERROR 등
        """
        log_msg = f"[{event_type}] {message}"
        self.logger.info(log_msg)

    def log_error(self, message):
        self.logger.error(message)

# 전역에서 사용하기 위한 인스턴스 생성 (선택 사항)
# logger = SystemLogger()