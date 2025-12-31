#!/usr/bin/env python3
"""
UI 업데이트 테스트 스크립트
Main Hub Engine을 통해 상품을 장바구니에 추가하고 UI로 전송
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from common.config import config
from database.db_handler import DBHandler
from database.product_dao import ProductDAO
from database.transaction_dao import TransactionDAO
from network.tcp_client import TCPClient
from common.protocols import Protocol, UICommand


def main():
    # 1. DB 연결
    print("[Test] Connecting to database...")
    db = DBHandler(config.db.aws_rds)

    product_dao = ProductDAO(db)
    tx_dao = TransactionDAO(db)

    # 2. 활성 세션 확인
    print("[Test] Checking for active session...")
    session = tx_dao.get_active_session(cart_id=1)

    if not session:
        print("[Test] No active session found, creating new session...")
        session_id = tx_dao.start_session(cart_id=1)
        print(f"[Test] Created session_id={session_id}")
    else:
        session_id = session["session_id"]
        print(f"[Test] Found active session_id={session_id}")

    # 3. 테스트 상품 추가 (product_id=1: Mountain Dew)
    product_id = 1
    print(f"\n[Test] Adding product_id={product_id} to cart...")

    product = product_dao.get_product_by_id(product_id)
    if not product:
        print(f"[Test] ERROR: Product {product_id} not found in DB!")
        return

    print(f"[Test] Product info: {product}")

    # 4. 장바구니에 추가
    tx_dao.add_cart_item(session_id=session_id, product_id=product_id, quantity=1)
    print(f"[Test] Item added to cart")

    # 5. 장바구니 조회
    cart_items = tx_dao.list_cart_items(session_id)
    total = sum(item["subtotal"] for item in cart_items)

    print(f"\n[Test] Current cart:")
    for item in cart_items:
        print(
            f"  - {item['product_name']}: {item['quantity']}개 x ₩{item['price']} = ₩{item['subtotal']}"
        )
    print(f"  Total: ₩{total}")

    # 6. UI에 UPDATE_CART 명령 전송
    print(f"\n[Test] Sending UPDATE_CART to UI...")
    ui_client = TCPClient("127.0.0.1", config.network.pc3_ui.ui_port)

    msg = Protocol.ui_command(
        UICommand.UPDATE_CART, {"items": cart_items, "total": total}
    )

    print(f"[Test] Message payload: {msg}")
    ui_client.send_request(msg)
    print(f"[Test] UPDATE_CART sent successfully!")

    print(f"\n[Test] ✓ Test completed. Check UI window for cart update.")


if __name__ == "__main__":
    main()
