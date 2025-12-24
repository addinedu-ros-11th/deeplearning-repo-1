"""
Purchase repository for database operations
"""

from typing import List, Optional
from .db_manager import Purchase, PurchaseItem, DBManager


class PurchaseRepository:
    """구매 정보 관리 Repository"""

    def __init__(self):
        self.db_manager = DBManager()

    def create_purchase(
        self,
        cart_session_id: str,
        total_amount: int,
        payment_method: str,
        purchase_image_path: str = None,
    ) -> Purchase:
        """새로운 구매 정보를 생성합니다"""
        session = self.db_manager.get_session()
        try:
            purchase = Purchase(
                cart_session_id=cart_session_id,
                total_amount=total_amount,
                payment_method=payment_method,
                purchase_image_path=purchase_image_path,
            )
            session.add(purchase)
            session.commit()
            session.refresh(purchase)
            return purchase
        finally:
            self.db_manager.close_session(session)

    def add_purchase_item(
        self, purchase_id: int, product_id: int, quantity: int, unit_price: int
    ) -> PurchaseItem:
        """구매 항목을 추가합니다"""
        session = self.db_manager.get_session()
        try:
            item = PurchaseItem(
                purchase_id=purchase_id,
                product_id=product_id,
                quantity=quantity,
                unit_price=unit_price,
            )
            session.add(item)
            session.commit()
            session.refresh(item)
            return item
        finally:
            self.db_manager.close_session(session)

    def get_purchase_by_session_id(self, cart_session_id: str) -> Optional[Purchase]:
        """세션 ID로 구매 정보를 조회합니다"""
        session = self.db_manager.get_session()
        try:
            return (
                session.query(Purchase)
                .filter(Purchase.cart_session_id == cart_session_id)
                .first()
            )
        finally:
            self.db_manager.close_session(session)

    def get_purchase_items(self, purchase_id: int) -> List[PurchaseItem]:
        """구매 항목 목록을 조회합니다"""
        session = self.db_manager.get_session()
        try:
            return (
                session.query(PurchaseItem)
                .filter(PurchaseItem.purchase_id == purchase_id)
                .all()
            )
        finally:
            self.db_manager.close_session(session)

    def get_all_purchases(self, limit: int = 100) -> List[Purchase]:
        """모든 구매 기록을 조회합니다"""
        session = self.db_manager.get_session()
        try:
            return (
                session.query(Purchase)
                .order_by(Purchase.created_at.desc())
                .limit(limit)
                .all()
            )
        finally:
            self.db_manager.close_session(session)
