"""
Cart repository for database operations
"""

from typing import List, Optional
from datetime import datetime
from .db_manager import Cart, CartItem, DBManager


class CartRepository:
    """카트 정보 관리 Repository"""

    def __init__(self):
        self.db_manager = DBManager()

    def create_cart(self, cart_session_id: str) -> Cart:
        """새로운 카트를 생성합니다"""
        session = self.db_manager.get_session()
        try:
            cart = Cart(cart_session_id=cart_session_id, status="active")
            session.add(cart)
            session.commit()
            session.refresh(cart)
            return cart
        finally:
            self.db_manager.close_session(session)

    def get_cart_by_session_id(self, cart_session_id: str) -> Optional[Cart]:
        """세션 ID로 카트를 조회합니다"""
        session = self.db_manager.get_session()
        try:
            return (
                session.query(Cart)
                .filter(Cart.cart_session_id == cart_session_id)
                .first()
            )
        finally:
            self.db_manager.close_session(session)

    def add_item_to_cart(
        self,
        cart_id: int,
        product_id: int,
        unit_price: int,
        quantity: int = 1,
        is_damaged: bool = False,
    ) -> CartItem:
        """카트에 상품을 추가합니다"""
        session = self.db_manager.get_session()
        try:
            # 이미 카트에 있는 상품인지 확인
            existing_item = (
                session.query(CartItem)
                .filter(CartItem.cart_id == cart_id, CartItem.product_id == product_id)
                .first()
            )

            if existing_item:
                existing_item.quantity += quantity
                session.commit()
                session.refresh(existing_item)
                return existing_item
            else:
                cart_item = CartItem(
                    cart_id=cart_id,
                    product_id=product_id,
                    quantity=quantity,
                    unit_price=unit_price,
                    is_damaged=is_damaged,
                )
                session.add(cart_item)
                session.commit()
                session.refresh(cart_item)
                return cart_item
        finally:
            self.db_manager.close_session(session)

    def remove_item_from_cart(self, cart_id: int, product_id: int) -> bool:
        """카트에서 상품을 제거합니다"""
        session = self.db_manager.get_session()
        try:
            cart_item = (
                session.query(CartItem)
                .filter(CartItem.cart_id == cart_id, CartItem.product_id == product_id)
                .first()
            )

            if cart_item:
                session.delete(cart_item)
                session.commit()
                return True
            return False
        finally:
            self.db_manager.close_session(session)

    def update_item_quantity(
        self, cart_id: int, product_id: int, quantity: int
    ) -> bool:
        """카트 내 상품 수량을 업데이트합니다"""
        session = self.db_manager.get_session()
        try:
            cart_item = (
                session.query(CartItem)
                .filter(CartItem.cart_id == cart_id, CartItem.product_id == product_id)
                .first()
            )

            if cart_item:
                cart_item.quantity = quantity
                session.commit()
                return True
            return False
        finally:
            self.db_manager.close_session(session)

    def get_cart_items(self, cart_id: int) -> List[CartItem]:
        """카트의 모든 아이템을 조회합니다"""
        session = self.db_manager.get_session()
        try:
            return session.query(CartItem).filter(CartItem.cart_id == cart_id).all()
        finally:
            self.db_manager.close_session(session)

    def get_cart_total(self, cart_id: int) -> int:
        """카트의 총 금액을 계산합니다"""
        session = self.db_manager.get_session()
        try:
            items = session.query(CartItem).filter(CartItem.cart_id == cart_id).all()
            total = sum(item.unit_price * item.quantity for item in items)
            return total
        finally:
            self.db_manager.close_session(session)

    def update_cart_status(self, cart_id: int, status: str) -> bool:
        """카트 상태를 업데이트합니다"""
        session = self.db_manager.get_session()
        try:
            cart = session.query(Cart).filter(Cart.id == cart_id).first()
            if cart:
                cart.status = status
                cart.updated_at = datetime.now()
                session.commit()
                return True
            return False
        finally:
            self.db_manager.close_session(session)
