"""
Cart management business logic
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional
from database.cart_repository import CartRepository
from database.purchase_repository import PurchaseRepository
from database.log_repository import LogRepository


class CartManager:
    """카트 관리 비즈니스 로직"""

    def __init__(self):
        self.cart_repo = CartRepository()
        self.purchase_repo = PurchaseRepository()
        self.log_repo = LogRepository()

    def start_cart_session(self) -> str:
        """
        새로운 카트 세션을 시작합니다

        Returns:
            세션 ID
        """
        # 고유한 세션 ID 생성
        session_id = (
            f"CART_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"
        )

        # 카트 생성
        cart = self.cart_repo.create_cart(session_id)

        # 이벤트 로그 기록
        self.log_repo.create_event_log(
            cart_session_id=session_id,
            event_type="cart_start",
            event_data={"timestamp": datetime.now().isoformat()},
        )

        print(f"Cart session started: {session_id}")
        return session_id

    def end_cart_session(self, session_id: str) -> bool:
        """
        카트 세션을 종료합니다

        Args:
            session_id: 세션 ID

        Returns:
            성공 여부
        """
        cart = self.cart_repo.get_cart_by_session_id(session_id)
        if not cart:
            return False

        # 카트 상태 업데이트
        self.cart_repo.update_cart_status(cart.id, "cancelled")

        # 이벤트 로그 기록
        self.log_repo.create_event_log(
            cart_session_id=session_id,
            event_type="cart_end",
            event_data={"timestamp": datetime.now().isoformat()},
        )

        print(f"Cart session ended: {session_id}")
        return True

    def get_cart_info(self, session_id: str) -> Optional[Dict]:
        """
        카트 정보를 조회합니다

        Args:
            session_id: 세션 ID

        Returns:
            카트 정보
        """
        cart = self.cart_repo.get_cart_by_session_id(session_id)
        if not cart:
            return None

        # 카트 아이템 조회
        items = self.cart_repo.get_cart_items(cart.id)

        # 카트 총액 계산
        total = self.cart_repo.get_cart_total(cart.id)

        # 정보 구성
        cart_info = {
            "session_id": session_id,
            "status": cart.status,
            "items": [
                {
                    "product_name": item.product.name,
                    "category": item.product.category,
                    "quantity": item.quantity,
                    "unit_price": item.unit_price,
                    "total_price": item.unit_price * item.quantity,
                    "is_damaged": item.is_damaged,
                }
                for item in items
            ],
            "total_amount": total,
            "item_count": len(items),
        }

        return cart_info

    def get_cart_total(self, session_id: str) -> int:
        """
        카트 총액을 계산합니다

        Args:
            session_id: 세션 ID

        Returns:
            총액
        """
        cart = self.cart_repo.get_cart_by_session_id(session_id)
        if not cart:
            return 0

        return self.cart_repo.get_cart_total(cart.id)

    def complete_purchase(
        self, session_id: str, payment_method: str, purchase_image_path: str = None
    ) -> Optional[Dict]:
        """
        구매를 완료합니다

        Args:
            session_id: 세션 ID
            payment_method: 결제 방법
            purchase_image_path: 구매 완료 이미지 경로

        Returns:
            구매 정보
        """
        cart = self.cart_repo.get_cart_by_session_id(session_id)
        if not cart:
            return None

        # 카트 아이템 조회
        cart_items = self.cart_repo.get_cart_items(cart.id)
        if not cart_items:
            return None

        # 총액 계산
        total_amount = self.cart_repo.get_cart_total(cart.id)

        # 구매 정보 생성
        purchase = self.purchase_repo.create_purchase(
            cart_session_id=session_id,
            total_amount=total_amount,
            payment_method=payment_method,
            purchase_image_path=purchase_image_path,
        )

        # 구매 아이템 추가
        for item in cart_items:
            self.purchase_repo.add_purchase_item(
                purchase_id=purchase.id,
                product_id=item.product_id,
                quantity=item.quantity,
                unit_price=item.unit_price,
            )

        # 카트 상태 업데이트
        self.cart_repo.update_cart_status(cart.id, "completed")

        # 이벤트 로그 기록
        self.log_repo.create_event_log(
            cart_session_id=session_id,
            event_type="purchase_complete",
            event_data={
                "total_amount": total_amount,
                "payment_method": payment_method,
                "timestamp": datetime.now().isoformat(),
            },
        )

        print(f"Purchase completed for session: {session_id}")

        return {
            "purchase_id": purchase.id,
            "session_id": session_id,
            "total_amount": total_amount,
            "payment_method": payment_method,
            "timestamp": purchase.created_at.isoformat(),
        }
