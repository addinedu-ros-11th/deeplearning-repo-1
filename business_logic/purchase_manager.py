"""
Purchase management business logic
"""

from typing import Optional, Dict
from database.purchase_repository import PurchaseRepository


class PurchaseManager:
    """구매 관리 비즈니스 로직"""

    def __init__(self):
        self.purchase_repo = PurchaseRepository()

    def get_purchase_history(self, session_id: str) -> Optional[Dict]:
        """
        구매 이력을 조회합니다

        Args:
            session_id: 세션 ID

        Returns:
            구매 정보
        """
        purchase = self.purchase_repo.get_purchase_by_session_id(session_id)
        if not purchase:
            return None

        items = self.purchase_repo.get_purchase_items(purchase.id)

        return {
            "purchase_id": purchase.id,
            "session_id": purchase.cart_session_id,
            "total_amount": purchase.total_amount,
            "payment_method": purchase.payment_method,
            "purchase_image": purchase.purchase_image_path,
            "items": [
                {
                    "product_name": item.product.name,
                    "quantity": item.quantity,
                    "unit_price": item.unit_price,
                    "total_price": item.unit_price * item.quantity,
                }
                for item in items
            ],
            "timestamp": purchase.created_at.isoformat(),
        }

    def get_all_purchases(self, limit: int = 100):
        """
        모든 구매 기록을 조회합니다

        Args:
            limit: 조회 개수 제한

        Returns:
            구매 기록 목록
        """
        purchases = self.purchase_repo.get_all_purchases(limit)

        return [
            {
                "purchase_id": p.id,
                "session_id": p.cart_session_id,
                "total_amount": p.total_amount,
                "payment_method": p.payment_method,
                "timestamp": p.created_at.isoformat(),
            }
            for p in purchases
        ]
