# database/obstacle_log_dao.py
from typing import List
from datetime import datetime


class ObstacleLogDAO:
    """
    Obstacle & Safety Event Log DAO
    """

    def __init__(self, db_handler):
        self.db = db_handler

    def log_obstacle(
        self,
        session_id: int,
        object_type: str,
        distance: float,
        speed: float,
        direction: str,
        is_warning: bool,
        track_id: int = -1,
        pttc_s: float = None,
        risk_score: float = None,
        in_center: bool = False,
        approaching: bool = False,
    ) -> None:
        """
        장애물 감지 이벤트를 로그에 기록
        - track_id: YOLO tracking ID (추적 기반 감지)
        - pttc_s: Predicted Time To Collision (초)
        - risk_score: 위험도 점수
        - in_center: 중앙 영역 위치 여부
        - approaching: 접근 중 여부
        """
        query = """
            INSERT INTO obstacle_logs (
                session_id,
                object_type,
                distance,
                speed,
                direction,
                is_warning,
                detected_at,
                track_id,
                pttc_s,
                risk_score,
                in_center,
                approaching
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        self.db.execute(
            query,
            (
                session_id,
                object_type,
                distance,
                speed,
                direction,
                is_warning,
                datetime.now(),
                track_id,
                pttc_s,
                risk_score,
                in_center,
                approaching,
            ),
        )

    def list_warnings_by_session(
        self,
        session_id: int,
    ) -> List[dict]:
        sql = """
        SELECT
            object_type,
            distance,
            speed,
            direction,
            detected_at
        FROM obstacle_logs
        WHERE session_id = %s
          AND is_warning = TRUE
        ORDER BY detected_at DESC
        """
        return self.db.fetch_all(sql, (session_id,))
