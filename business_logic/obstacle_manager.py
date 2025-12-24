"""
Obstacle management business logic
"""

from typing import List, Dict
from database.log_repository import LogRepository


class ObstacleManager:
    """장애물 관리 비즈니스 로직"""

    def __init__(self):
        self.log_repo = LogRepository()

    def process_obstacles(self, session_id: str, obstacles: List[Dict]) -> List[Dict]:
        """
        장애물 정보를 처리하고 경고를 생성합니다

        Args:
            session_id: 세션 ID
            obstacles: 인식된 장애물 목록

        Returns:
            경고 목록
        """
        warnings = []

        for obstacle in obstacles:
            # 장애물 로그 기록
            self.log_repo.create_obstacle_log(
                cart_session_id=session_id,
                obstacle_type=obstacle.get("type"),
                distance=obstacle.get("distance"),
                direction=obstacle.get("direction"),
                speed=obstacle.get("speed"),
                warning_level=obstacle.get("warning_level"),
            )

            # 경고가 필요한 경우
            if obstacle.get("warning_level") in ["warning", "critical"]:
                warning = {
                    "level": obstacle.get("warning_level"),
                    "type": obstacle.get("type"),
                    "distance": obstacle.get("distance"),
                    "direction": obstacle.get("direction"),
                    "speed": obstacle.get("speed"),
                    "message": self._generate_warning_message(obstacle),
                }
                warnings.append(warning)

        return warnings

    def _generate_warning_message(self, obstacle: Dict) -> str:
        """
        경고 메시지를 생성합니다

        Args:
            obstacle: 장애물 정보

        Returns:
            경고 메시지
        """
        level = obstacle.get("warning_level")
        obj_type = obstacle.get("type")
        distance = obstacle.get("distance")
        direction = obstacle.get("direction")

        type_kr = {"person": "사람", "cart": "카트"}

        direction_kr = {"left": "왼쪽", "center": "정면", "right": "오른쪽"}

        obj_name = type_kr.get(obj_type, obj_type)
        dir_name = direction_kr.get(direction, direction)

        if level == "critical":
            return f"⚠️ 위험! {dir_name}에 {obj_name}이(가) {distance:.1f}m 거리에 있습니다!"
        elif level == "warning":
            return f"⚡ 주의! {dir_name}에 {obj_name}이(가) 접근 중입니다. ({distance:.1f}m)"
        else:
            return f"{dir_name}에 {obj_name} 감지됨 ({distance:.1f}m)"

    def get_obstacle_history(self, session_id: str) -> List[Dict]:
        """
        장애물 감지 이력을 조회합니다

        Args:
            session_id: 세션 ID

        Returns:
            장애물 감지 이력
        """
        logs = self.log_repo.get_obstacle_logs_by_session(session_id)

        return [
            {
                "type": log.obstacle_type,
                "distance": log.distance,
                "direction": log.direction,
                "speed": log.speed,
                "warning_level": log.warning_level,
                "timestamp": log.created_at.isoformat(),
            }
            for log in logs
        ]

    def get_critical_warnings(self, session_id: str = None) -> List[Dict]:
        """
        위험 수준의 경고를 조회합니다

        Args:
            session_id: 세션 ID (선택사항)

        Returns:
            위험 경고 목록
        """
        logs = self.log_repo.get_critical_obstacle_logs(session_id)

        return [
            {
                "session_id": log.cart_session_id,
                "type": log.obstacle_type,
                "distance": log.distance,
                "direction": log.direction,
                "speed": log.speed,
                "timestamp": log.created_at.isoformat(),
            }
            for log in logs
        ]
