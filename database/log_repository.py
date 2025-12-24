"""
Log repository for event and obstacle logging
"""

import json
from typing import List, Optional
from datetime import datetime
from .db_manager import EventLog, ObstacleLog, DBManager


class LogRepository:
    """로그 관리 Repository"""

    def __init__(self):
        self.db_manager = DBManager()

    def create_event_log(
        self, cart_session_id: str, event_type: str, event_data: dict = None
    ) -> EventLog:
        """이벤트 로그를 생성합니다"""
        session = self.db_manager.get_session()
        try:
            log = EventLog(
                cart_session_id=cart_session_id,
                event_type=event_type,
                event_data=json.dumps(event_data) if event_data else None,
            )
            session.add(log)
            session.commit()
            session.refresh(log)
            return log
        finally:
            self.db_manager.close_session(session)

    def get_event_logs_by_session(self, cart_session_id: str) -> List[EventLog]:
        """세션 ID로 이벤트 로그를 조회합니다"""
        session = self.db_manager.get_session()
        try:
            return (
                session.query(EventLog)
                .filter(EventLog.cart_session_id == cart_session_id)
                .order_by(EventLog.created_at)
                .all()
            )
        finally:
            self.db_manager.close_session(session)

    def get_event_logs_by_type(
        self, event_type: str, start_date: datetime = None, end_date: datetime = None
    ) -> List[EventLog]:
        """이벤트 타입과 날짜 범위로 로그를 조회합니다"""
        session = self.db_manager.get_session()
        try:
            query = session.query(EventLog).filter(EventLog.event_type == event_type)

            if start_date:
                query = query.filter(EventLog.created_at >= start_date)
            if end_date:
                query = query.filter(EventLog.created_at <= end_date)

            return query.order_by(EventLog.created_at).all()
        finally:
            self.db_manager.close_session(session)

    def create_obstacle_log(
        self,
        cart_session_id: str,
        obstacle_type: str,
        distance: float,
        direction: str,
        speed: float,
        warning_level: str,
    ) -> ObstacleLog:
        """장애물 로그를 생성합니다"""
        session = self.db_manager.get_session()
        try:
            log = ObstacleLog(
                cart_session_id=cart_session_id,
                obstacle_type=obstacle_type,
                distance=distance,
                direction=direction,
                speed=speed,
                warning_level=warning_level,
            )
            session.add(log)
            session.commit()
            session.refresh(log)
            return log
        finally:
            self.db_manager.close_session(session)

    def get_obstacle_logs_by_session(self, cart_session_id: str) -> List[ObstacleLog]:
        """세션 ID로 장애물 로그를 조회합니다"""
        session = self.db_manager.get_session()
        try:
            return (
                session.query(ObstacleLog)
                .filter(ObstacleLog.cart_session_id == cart_session_id)
                .order_by(ObstacleLog.created_at)
                .all()
            )
        finally:
            self.db_manager.close_session(session)

    def get_critical_obstacle_logs(
        self, cart_session_id: str = None
    ) -> List[ObstacleLog]:
        """위험 수준의 장애물 로그를 조회합니다"""
        session = self.db_manager.get_session()
        try:
            query = session.query(ObstacleLog).filter(
                ObstacleLog.warning_level == "critical"
            )

            if cart_session_id:
                query = query.filter(ObstacleLog.cart_session_id == cart_session_id)

            return query.order_by(ObstacleLog.created_at.desc()).all()
        finally:
            self.db_manager.close_session(session)
