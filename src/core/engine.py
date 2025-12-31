# src/core/engine.py
import time
from typing import Optional

from common.protocols import DangerLevel, Protocol, UICommand
from database.obstacle_log_dao import ObstacleLogDAO
from database.product_dao import ProductDAO
from database.transaction_dao import TransactionDAO
from network.tcp_client import TCPClient


class SmartCartEngine:
    """
    Business decision engine.
    - Encapsulates business logic for handling events.
    - Processes data from AI events, interacts with the database, and sends commands to the UI.
    """

    DUPLICATE_PRODUCT_INTERVAL_SEC = 2.0

    def __init__(
        self,
        product_dao: ProductDAO,
        transaction_dao: TransactionDAO,
        obstacle_dao: ObstacleLogDAO,
        ui_client: TCPClient,
    ):
        self.product_dao = product_dao
        self.tx_dao = transaction_dao
        self.obstacle_dao = obstacle_dao
        self.ui_client = ui_client

        # State for obstacle danger level
        self.last_obstacle_level: DangerLevel = DangerLevel.NORMAL

        # State for product de-duplication
        self._last_product_id: Optional[int] = None
        self._last_product_ts: float = 0.0

    def process_obstacle_event(self, data: dict, session_id: int):
        """Processes an obstacle danger event from the AI."""
        level = DangerLevel(data["level"])

        # 1. Log event to database
        self.obstacle_dao.log_obstacle(
            session_id=session_id,
            object_type=data.get("object_type", "UNKNOWN"),
            distance=data.get("distance", 1000),
            speed=data.get("speed", 0),
            direction=data.get("direction", "stop"),
            is_warning=level >= DangerLevel.CAUTION,
        )

        # 2. Avoid sending duplicate events
        if level == self.last_obstacle_level:
            return
        self.last_obstacle_level = level

        # 3. Send warning to UI if danger level is high enough
        if level >= DangerLevel.CAUTION:
            msg = Protocol.ui_command(
                UICommand.SHOW_ALARM,
                {
                    "level": level.value,
                    "object_type": data.get("object_type", "obstacle"),
                    "distance": data.get("distance", 0),
                    "speed": data.get("speed", 0),
                    "direction": data.get("direction", "front"),
                },
            )
            self.ui_client.send_request(msg)

    def process_product_event(self, data: dict, session_id: int):
        """Processes a product detection event from the AI."""
        product_id = data["product_id"]
        print(
            f"[Engine] Product event received: product_id={product_id}, confidence={data.get('confidence', 'N/A')}"
        )

        # 1. Debounce product detection
        if not self._is_new_product_detection(product_id):
            print(
                f"[Engine] Duplicate detection ignored (within {self.DUPLICATE_PRODUCT_INTERVAL_SEC}s)"
            )
            return

        # 2. Get product details from DB
        product = self.product_dao.get_product_by_id(product_id)
        if not product:
            print(f"[Engine] WARN: Product with ID {product_id} not found in database.")
            return

        print(
            f"[Engine] Product found in DB: {product.get('name', 'N/A')}, price={product.get('price', 0)}"
        )

        # 3. Add item to cart in DB
        self.tx_dao.add_cart_item(
            session_id=session_id,
            product_id=product_id,
            quantity=1,
        )
        print(f"[Engine] Item added to cart (session_id={session_id})")

        # 4. Get updated cart and send to UI
        cart_items = self.tx_dao.list_cart_items(session_id)
        total = sum(item["subtotal"] for item in cart_items)

        print(f"[Engine] Cart updated: {len(cart_items)} items, total={total}")
        print(f"[Engine] Cart items: {cart_items}")

        msg = Protocol.ui_command(
            UICommand.UPDATE_CART, {"items": cart_items, "total": total}
        )
        print(f"[Engine] Sending UPDATE_CART to UI...")
        self.ui_client.send_request(msg)
        print(f"[Engine] UPDATE_CART sent successfully")

    def _is_new_product_detection(self, product_id: int) -> bool:
        """Internal helper to check for duplicate product detections."""
        now = time.time()

        is_duplicate = (
            self._last_product_id == product_id
            and (now - self._last_product_ts) < self.DUPLICATE_PRODUCT_INTERVAL_SEC
        )

        if is_duplicate:
            return False

        self._last_product_id = product_id
        self._last_product_ts = now
        return True

    def update_item_quantity(self, session_id: int, product_id: int, quantity: int):
        """Update quantity of a specific product in cart"""
        print(
            f"[Engine] Updating quantity: product_id={product_id}, quantity={quantity}"
        )

        # Update DB
        self.tx_dao.update_item_quantity(session_id, product_id, quantity)

        # Get updated cart and send to UI
        cart_items = self.tx_dao.list_cart_items(session_id)
        total = sum(item["subtotal"] for item in cart_items)

        msg = Protocol.ui_command(
            UICommand.UPDATE_CART, {"items": cart_items, "total": total}
        )
        self.ui_client.send_request(msg)
        print(f"[Engine] Quantity updated, cart refreshed")

    def remove_cart_item(self, session_id: int, product_id: int):
        """Remove a specific product from cart"""
        print(f"[Engine] Removing item: product_id={product_id}")

        # Remove from DB
        self.tx_dao.remove_cart_item(session_id, product_id)

        # Get updated cart and send to UI
        cart_items = self.tx_dao.list_cart_items(session_id)
        total = sum(item["subtotal"] for item in cart_items)

        msg = Protocol.ui_command(
            UICommand.UPDATE_CART, {"items": cart_items, "total": total}
        )
        self.ui_client.send_request(msg)
        print(f"[Engine] Item removed, cart refreshed")

    def reset(self) -> None:
        """Resets the engine's session state."""
        self.last_obstacle_level = DangerLevel.NORMAL
        self._last_product_id = None
        self._last_product_ts = 0.0
