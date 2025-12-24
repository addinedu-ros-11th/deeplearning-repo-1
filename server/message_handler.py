"""
Message handler for server
"""

from typing import Dict
from business_logic.cart_manager import CartManager
from business_logic.product_manager import ProductManager
from business_logic.obstacle_manager import ObstacleManager
from business_logic.alarm_manager import AlarmManager


class MessageHandler:
    """서버 메시지 처리 핸들러"""

    def __init__(self):
        self.cart_manager = CartManager()
        self.product_manager = ProductManager()
        self.obstacle_manager = ObstacleManager()
        self.alarm_manager = AlarmManager()

    def handle_tcp_message(self, client_id: str, message: Dict) -> Dict:
        """
        TCP 메시지를 처리합니다

        Args:
            client_id: 클라이언트 ID
            message: 수신한 메시지

        Returns:
            응답 메시지
        """
        msg_type = message.get("type")

        if msg_type == "cart_start":
            return self._handle_cart_start(message)

        elif msg_type == "cart_end":
            return self._handle_cart_end(message)

        elif msg_type == "product_add":
            return self._handle_product_add(message)

        elif msg_type == "product_remove":
            return self._handle_product_remove(message)

        elif msg_type == "get_cart_info":
            return self._handle_get_cart_info(message)

        elif msg_type == "purchase_complete":
            return self._handle_purchase_complete(message)

        else:
            return {"status": "error", "message": "Unknown message type"}

    def handle_udp_message(self, address: tuple, message: Dict) -> Dict:
        """
        UDP 메시지를 처리합니다 (실시간 데이터)

        Args:
            address: 클라이언트 주소
            message: 수신한 메시지

        Returns:
            응답 메시지 (필요시)
        """
        msg_type = message.get("type")

        if msg_type == "product_detection":
            return self._handle_product_detection(message)

        elif msg_type == "obstacle_detection":
            return self._handle_obstacle_detection(message)

        return None

    def _handle_cart_start(self, message: Dict) -> Dict:
        """카트 사용 시작"""
        session_id = self.cart_manager.start_cart_session()
        return {
            "status": "success",
            "session_id": session_id,
            "message": "Cart session started",
        }

    def _handle_cart_end(self, message: Dict) -> Dict:
        """카트 사용 종료"""
        session_id = message.get("session_id")
        self.cart_manager.end_cart_session(session_id)
        return {"status": "success", "message": "Cart session ended"}

    def _handle_product_add(self, message: Dict) -> Dict:
        """상품 추가"""
        session_id = message.get("session_id")
        product_name = message.get("product_name")
        is_damaged = message.get("is_damaged", False)

        result = self.product_manager.add_product_to_cart(
            session_id, product_name, is_damaged
        )

        if result:
            return {
                "status": "success",
                "message": "Product added to cart",
                "cart_total": self.cart_manager.get_cart_total(session_id),
            }
        else:
            return {"status": "error", "message": "Failed to add product"}

    def _handle_product_remove(self, message: Dict) -> Dict:
        """상품 제거"""
        session_id = message.get("session_id")
        product_name = message.get("product_name")

        result = self.product_manager.remove_product_from_cart(session_id, product_name)

        if result:
            return {
                "status": "success",
                "message": "Product removed from cart",
                "cart_total": self.cart_manager.get_cart_total(session_id),
            }
        else:
            return {"status": "error", "message": "Failed to remove product"}

    def _handle_get_cart_info(self, message: Dict) -> Dict:
        """카트 정보 조회"""
        session_id = message.get("session_id")
        cart_info = self.cart_manager.get_cart_info(session_id)

        if cart_info:
            return {"status": "success", "cart_info": cart_info}
        else:
            return {"status": "error", "message": "Cart not found"}

    def _handle_purchase_complete(self, message: Dict) -> Dict:
        """구매 완료"""
        session_id = message.get("session_id")
        payment_method = message.get("payment_method")

        result = self.cart_manager.complete_purchase(session_id, payment_method)

        if result:
            return {
                "status": "success",
                "message": "Purchase completed",
                "purchase_info": result,
            }
        else:
            return {"status": "error", "message": "Failed to complete purchase"}

    def _handle_product_detection(self, message: Dict) -> Dict:
        """상품 인식 처리"""
        session_id = message.get("session_id")
        detections = message.get("detections", [])

        # 로그 기록
        self.product_manager.log_product_detection(session_id, detections)

        return None

    def _handle_obstacle_detection(self, message: Dict) -> Dict:
        """장애물 인식 처리"""
        session_id = message.get("session_id")
        obstacles = message.get("obstacles", [])

        # 장애물 처리 및 경고 생성
        warnings = self.obstacle_manager.process_obstacles(session_id, obstacles)

        # 위험한 장애물이 있으면 알람 발생
        if warnings:
            for warning in warnings:
                if warning["level"] == "critical":
                    self.alarm_manager.trigger_alarm(session_id, warning)

        return None
