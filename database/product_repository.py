"""
Product repository for database operations
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from .db_manager import Product, DBManager


class ProductRepository:
    """상품 정보 관리 Repository"""

    def __init__(self):
        self.db_manager = DBManager()

    def create_product(
        self,
        name: str,
        category: str,
        price: int,
        image_path: str = None,
        total_count: int = 0,
    ) -> Product:
        """새로운 상품을 생성합니다"""
        session = self.db_manager.get_session()
        try:
            product = Product(
                name=name,
                category=category,
                price=price,
                image_path=image_path,
                total_count=total_count,
            )
            session.add(product)
            session.commit()
            session.refresh(product)
            return product
        finally:
            self.db_manager.close_session(session)

    def get_product_by_id(self, product_id: int) -> Optional[Product]:
        """ID로 상품을 조회합니다"""
        session = self.db_manager.get_session()
        try:
            return session.query(Product).filter(Product.id == product_id).first()
        finally:
            self.db_manager.close_session(session)

    def get_product_by_name(self, name: str) -> Optional[Product]:
        """이름으로 상품을 조회합니다"""
        session = self.db_manager.get_session()
        try:
            return session.query(Product).filter(Product.name == name).first()
        finally:
            self.db_manager.close_session(session)

    def get_products_by_category(self, category: str) -> List[Product]:
        """카테고리별 상품 목록을 조회합니다"""
        session = self.db_manager.get_session()
        try:
            return session.query(Product).filter(Product.category == category).all()
        finally:
            self.db_manager.close_session(session)

    def get_all_products(self) -> List[Product]:
        """모든 상품 목록을 조회합니다"""
        session = self.db_manager.get_session()
        try:
            return session.query(Product).all()
        finally:
            self.db_manager.close_session(session)

    def update_product_count(self, product_id: int, count: int) -> bool:
        """상품 개수를 업데이트합니다"""
        session = self.db_manager.get_session()
        try:
            product = session.query(Product).filter(Product.id == product_id).first()
            if product:
                product.total_count = count
                session.commit()
                return True
            return False
        finally:
            self.db_manager.close_session(session)

    def delete_product(self, product_id: int) -> bool:
        """상품을 삭제합니다"""
        session = self.db_manager.get_session()
        try:
            product = session.query(Product).filter(Product.id == product_id).first()
            if product:
                session.delete(product)
                session.commit()
                return True
            return False
        finally:
            self.db_manager.close_session(session)
