"""
Alarm management business logic
"""

from typing import Dict
from datetime import datetime


class AlarmManager:
    """알람 관리 비즈니스 로직"""

    def __init__(self):
        self.active_alarms = {}  # session_id: alarm_info

    def trigger_alarm(self, session_id: str, warning: Dict):
        """
        알람을 발생시킵니다

        Args:
            session_id: 세션 ID
            warning: 경고 정보
        """
        alarm_info = {
            "level": warning.get("level"),
            "type": warning.get("type"),
            "message": warning.get("message"),
            "distance": warning.get("distance"),
            "direction": warning.get("direction"),
            "timestamp": datetime.now().isoformat(),
        }

        self.active_alarms[session_id] = alarm_info

        # 알람 출력
        self._display_alarm(alarm_info)

    def _display_alarm(self, alarm_info: Dict):
        """
        알람을 표시합니다

        Args:
            alarm_info: 알람 정보
        """
        level = alarm_info.get("level")
        message = alarm_info.get("message")

        # 콘솔 출력
        if level == "critical":
            print(f"\n{'='*60}")
            print(f"🚨 긴급 알람 🚨")
            print(f"{message}")
            print(f"{'='*60}\n")
        else:
            print(f"\n⚡ 경고: {message}\n")

    def clear_alarm(self, session_id: str):
        """
        알람을 해제합니다

        Args:
            session_id: 세션 ID
        """
        if session_id in self.active_alarms:
            del self.active_alarms[session_id]
            print(f"Alarm cleared for session: {session_id}")

    def get_active_alarm(self, session_id: str) -> Dict:
        """
        활성화된 알람을 조회합니다

        Args:
            session_id: 세션 ID

        Returns:
            알람 정보
        """
        return self.active_alarms.get(session_id)

    def get_all_active_alarms(self) -> Dict:
        """
        모든 활성화된 알람을 조회합니다

        Returns:
            모든 알람 정보
        """
        return self.active_alarms.copy()
