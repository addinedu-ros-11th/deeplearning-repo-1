"""
Product management business logic
"""

from typing import Optional, List
from database.product_repository import ProductRepository
from database.cart_repository import CartRepository
from database.log_repository import LogRepository


class ProductManager:
    """상품 관리 비즈니스 로직"""

    def __init__(self):
        self.product_repo = ProductRepository()
        self.cart_repo = CartRepository()
        self.log_repo = LogRepository()

    def add_product_to_cart(
        self, session_id: str, product_name: str, is_damaged: bool = False
    ) -> bool:
        """
        카트에 상품을 추가합니다

        Args:
            session_id: 세션 ID
            product_name: 상품 이름
            is_damaged: 손상 여부

        Returns:
            성공 여부
        """
        # 카트 조회
        cart = self.cart_repo.get_cart_by_session_id(session_id)
        if not cart:
            print(f"Cart not found: {session_id}")
            return False

        # 상품 조회
        product = self.product_repo.get_product_by_name(product_name)
        if not product:
            print(f"Product not found: {product_name}")
            return False

        # 손상된 상품은 추가하지 않음
        if is_damaged:
            print(f"Damaged product detected, not adding to cart: {product_name}")
            # 로그만 기록
            self.log_repo.create_event_log(
                cart_session_id=session_id,
                event_type="product_damaged",
                event_data={"product_name": product_name, "product_id": product.id},
            )
            return False

        # 카트에 상품 추가
        self.cart_repo.add_item_to_cart(
            cart_id=cart.id,
            product_id=product.id,
            unit_price=product.price,
            quantity=1,
            is_damaged=is_damaged,
        )

        # 로그 기록
        self.log_repo.create_event_log(
            cart_session_id=session_id,
            event_type="product_added",
            event_data={
                "product_name": product_name,
                "product_id": product.id,
                "price": product.price,
            },
        )

        print(f"Product added to cart: {product_name}")
        return True

    def remove_product_from_cart(self, session_id: str, product_name: str) -> bool:
        """
        카트에서 상품을 제거합니다

        Args:
            session_id: 세션 ID
            product_name: 상품 이름

        Returns:
            성공 여부
        """
        # 카트 조회
        cart = self.cart_repo.get_cart_by_session_id(session_id)
        if not cart:
            return False

        # 상품 조회
        product = self.product_repo.get_product_by_name(product_name)
        if not product:
            return False

        # 카트에서 상품 제거
        result = self.cart_repo.remove_item_from_cart(cart.id, product.id)

        if result:
            # 로그 기록
            self.log_repo.create_event_log(
                cart_session_id=session_id,
                event_type="product_removed",
                event_data={"product_name": product_name, "product_id": product.id},
            )
            print(f"Product removed from cart: {product_name}")

        return result

    def log_product_detection(self, session_id: str, detections: List[dict]):
        """
        상품 인식 로그를 기록합니다

        Args:
            session_id: 세션 ID
            detections: 인식된 상품 목록
        """
        for detection in detections:
            self.log_repo.create_event_log(
                cart_session_id=session_id,
                event_type="product_detected",
                event_data={
                    "product_name": detection.get("name"),
                    "confidence": detection.get("confidence"),
                    "category": detection.get("category"),
                    "quality": detection.get("quality", {}),
                },
            )

    def get_product_info(self, product_name: str) -> Optional[dict]:
        """
        상품 정보를 조회합니다

        Args:
            product_name: 상품 이름

        Returns:
            상품 정보
        """
        product = self.product_repo.get_product_by_name(product_name)
        if not product:
            return None

        return {
            "id": product.id,
            "name": product.name,
            "category": product.category,
            "price": product.price,
            "image_path": product.image_path,
            "total_count": product.total_count,
        }

    def get_all_products(self) -> List[dict]:
        """
        모든 상품 목록을 조회합니다

        Returns:
            상품 목록
        """
        products = self.product_repo.get_all_products()

        return [
            {
                "id": p.id,
                "name": p.name,
                "category": p.category,
                "price": p.price,
                "image_path": p.image_path,
                "total_count": p.total_count,
            }
            for p in products
        ]
