"""
Database configuration for Smart Cart system
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# SQLAlchemy Base
Base = declarative_base()


class DBConfig:
    """데이터베이스 연결 설정을 관리하는 클래스"""

    _instance = None
    _engine = None
    _session_factory = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DBConfig, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if self._engine is None:
            self.initialize()

    def initialize(self):
        """데이터베이스 연결을 초기화합니다"""
        # 환경 변수에서 우선 읽기, 없으면 config.yaml에서 읽기
        host = os.getenv("DB_HOST")
        port = int(os.getenv("DB_PORT", 3306))
        user = os.getenv("DB_USER")
        password = os.getenv("DB_PASSWORD")
        database = os.getenv("DB_NAME")

        # 환경 변수가 없으면 config.yaml 사용
        if not all([host, user, password, database]):
            from .config import Config

            config = Config()
            host = host or config.get("database.host")
            port = port or config.get("database.port", 3306)
            user = user or config.get("database.user")
            password = password or config.get("database.password")
            database = database or config.get("database.database")

        # MySQL connection string
        connection_string = (
            f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"
            "?charset=utf8mb4"
        )

        self._engine = create_engine(
            connection_string, pool_pre_ping=True, pool_recycle=3600, echo=False
        )

        self._session_factory = sessionmaker(bind=self._engine)

    def get_engine(self):
        """SQLAlchemy 엔진을 반환합니다"""
        return self._engine

    def get_session(self):
        """새로운 데이터베이스 세션을 생성합니다"""
        return self._session_factory()

    def create_tables(self):
        """모든 테이블을 생성합니다"""
        Base.metadata.create_all(self._engine)

    def drop_tables(self):
        """모든 테이블을 삭제합니다"""
        Base.metadata.drop_all(self._engine)
