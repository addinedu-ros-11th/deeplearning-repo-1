"""
Database manager and ORM models
"""

from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Text,
    ForeignKey,
    Boolean,
)
from sqlalchemy.orm import relationship
from config.db_config import Base, DBConfig


class Product(Base):
    """상품 정보 테이블"""

    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False)  # icecream, snack, ramen
    price = Column(Integer, nullable=False)
    image_path = Column(String(255))
    total_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class Cart(Base):
    """카트 정보 테이블"""

    __tablename__ = "carts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cart_session_id = Column(String(100), unique=True, nullable=False)
    status = Column(String(20), default="active")  # active, completed, cancelled
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Relationships
    items = relationship(
        "CartItem", back_populates="cart", cascade="all, delete-orphan"
    )


class CartItem(Base):
    """카트 아이템 테이블"""

    __tablename__ = "cart_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cart_id = Column(Integer, ForeignKey("carts.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, default=1)
    unit_price = Column(Integer, nullable=False)
    is_damaged = Column(Boolean, default=False)
    added_at = Column(DateTime, default=datetime.now)

    # Relationships
    cart = relationship("Cart", back_populates="items")
    product = relationship("Product")


class EventLog(Base):
    """이벤트 로그 테이블"""

    __tablename__ = "event_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cart_session_id = Column(String(100))
    event_type = Column(
        String(50), nullable=False
    )  # cart_start, cart_end, product_detected, obstacle_detected
    event_data = Column(Text)  # JSON 형태의 이벤트 데이터
    created_at = Column(DateTime, default=datetime.now)


class ObstacleLog(Base):
    """장애물 감지 로그 테이블"""

    __tablename__ = "obstacle_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cart_session_id = Column(String(100))
    obstacle_type = Column(String(50))  # person, cart
    distance = Column(Float)
    direction = Column(String(50))
    speed = Column(Float)
    warning_level = Column(String(20))  # normal, warning, critical
    created_at = Column(DateTime, default=datetime.now)


class Purchase(Base):
    """구매 완료 정보 테이블"""

    __tablename__ = "purchases"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cart_session_id = Column(String(100), unique=True, nullable=False)
    total_amount = Column(Integer, nullable=False)
    payment_method = Column(String(50))
    purchase_image_path = Column(String(255))  # 구매 완료 시점 이미지
    created_at = Column(DateTime, default=datetime.now)

    # Relationships
    items = relationship(
        "PurchaseItem", back_populates="purchase", cascade="all, delete-orphan"
    )


class PurchaseItem(Base):
    """구매 아이템 테이블"""

    __tablename__ = "purchase_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    purchase_id = Column(Integer, ForeignKey("purchases.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Integer, nullable=False)

    # Relationships
    purchase = relationship("Purchase", back_populates="items")
    product = relationship("Product")


class DBManager:
    """데이터베이스 매니저 클래스"""

    def __init__(self):
        self.db_config = DBConfig()

    def initialize_database(self):
        """데이터베이스 초기화 및 테이블 생성"""
        self.db_config.create_tables()

    def get_session(self):
        """데이터베이스 세션 반환"""
        return self.db_config.get_session()

    def close_session(self, session):
        """세션 종료"""
        if session:
            session.close()
