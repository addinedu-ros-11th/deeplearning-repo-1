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
    ) -> None:
        query = """
            INSERT INTO obstacle_logs (
                session_id,
                object_type,
                distance,
                speed,
                direction,
                is_warning,
                detected_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
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
