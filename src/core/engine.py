# src/core/engine.py
import time
from typing import Optional, Any, Dict

from common.protocols import DangerLevel, Protocol, UICommand
from database.obstacle_log_dao import ObstacleLogDAO
from database.product_dao import ProductDAO
from database.transaction_dao import TransactionDAO
from network.tcp_client import TCPClient

from detectors.obstacle_dl_v2 import ObstacleDetectorV2, RISK_SAFE, RISK_CAUTION, RISK_WARN, RISK_NAME


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
        self.obstacle_detector_v2 = ObstacleDetectorV2() # Initialize the new detector

        # State for obstacle danger level
        self.last_obstacle_level: DangerLevel = DangerLevel.NORMAL

        # State for product de-duplication
        self._last_product_id: Optional[int] = None
        self._last_product_ts: float = 0.0

    def process_obstacle_event(self, data: Dict[str, Any], session_id: int, frame_index: int = 0, fps: float = 30.0):
        """Processes an obstacle danger event from the AI using the new ObstacleDetectorV2."""
        
        # 'data' here is expected to be the raw frame (numpy array)
        detection_results = self.obstacle_detector_v2.detect_and_assess(data, frame_index=frame_index, fps=fps)
        
        current_danger_level = DangerLevel.NORMAL
        
        # Determine the highest danger level from detected objects
        # And prepare data for logging and UI command
        if detection_results["objects"]:
            highest_risk_level = RISK_SAFE
            main_obstacle_info = {}
            
            for obj in detection_results["objects"]:
                risk_level = obj["risk_level_name"]
                
                if risk_level == RISK_NAME[RISK_WARN]:
                    highest_risk_level = max(highest_risk_level, RISK_WARN)
                elif risk_level == RISK_NAME[RISK_CAUTION]:
                    highest_risk_level = max(highest_risk_level, RISK_CAUTION)
                
                # For logging and UI, pick the most critical object or the first one if all are same level
                if highest_risk_level == RISK_WARN and obj["risk_level_name"] == RISK_NAME[RISK_WARN]:
                    main_obstacle_info = obj
                    break # Found a WARN, prioritize it
                elif highest_risk_level == RISK_CAUTION and obj["risk_level_name"] == RISK_NAME[RISK_CAUTION]:
                    main_obstacle_info = obj
                    # Don't break yet, in case a WARN appears later
                elif not main_obstacle_info: # If no CAUTION or WARN yet, take the first safe one
                    main_obstacle_info = obj

            if highest_risk_level == RISK_WARN:
                current_danger_level = DangerLevel.CRITICAL
            elif highest_risk_level == RISK_CAUTION:
                current_danger_level = DangerLevel.CAUTION
            else:
                current_danger_level = DangerLevel.NORMAL
        
            # 1. Log event to database
            self.obstacle_dao.log_obstacle(
                session_id=session_id,
                object_type=main_obstacle_info.get("class", "UNKNOWN"),
                distance=float(main_obstacle_info.get("dist_proxy", 1000.0)), # Using dist_proxy as approximate distance
                speed=float(main_obstacle_info.get("closing_rate", 0.0)),     # Using closing_rate as approximate speed
                direction="front", # New model doesn't explicitly provide direction, assuming front
                is_warning=current_danger_level >= DangerLevel.CAUTION,
                # Add new fields to log if schema allows, or concatenate into existing ones
                # For now, mapping to existing fields
            )
            
        else: # No objects detected, so normal
            current_danger_level = DangerLevel.NORMAL
            main_obstacle_info = {
                "class": "NONE",
                "track_id": -1,
                "risk_level_name": RISK_NAME[RISK_SAFE],
                "risk_score": 0.0,
                "pttc_s": 1e9,
                "dist_proxy": 1000.0,
                "closing_rate": 0.0,
                "box": [0,0,0,0]
            }
            # Log event to database for normal as well, if needed. For now, only caution/critical are logged.
            self.obstacle_dao.log_obstacle(
                session_id=session_id,
                object_type=main_obstacle_info.get("class", "UNKNOWN"),
                distance=float(main_obstacle_info.get("dist_proxy", 1000.0)),
                speed=float(main_obstacle_info.get("closing_rate", 0.0)),
                direction="front",
                is_warning=current_danger_level >= DangerLevel.CAUTION,
            )

        # 2. Avoid sending duplicate events (only if danger level changes)
        if current_danger_level == self.last_obstacle_level:
            return
        self.last_obstacle_level = current_danger_level
        
        # 3. Send warning to UI if danger level is high enough
        if current_danger_level >= DangerLevel.CAUTION:
            ui_alarm_data = {
                "level": current_danger_level.value,
                "object_type": main_obstacle_info.get("class", "obstacle"),
                "distance": float(main_obstacle_info.get("dist_proxy", 0)),
                "speed": float(main_obstacle_info.get("closing_rate", 0)),
                "direction": "front", # Assuming front, as new model doesn't provide explicit direction
                "risk_level_name": main_obstacle_info.get("risk_level_name", "SAFE"),
                "risk_score": float(main_obstacle_info.get("risk_score", 0.0)),
                "pttc_s": float(main_obstacle_info.get("pttc_s", 1e9)),
                "dist_proxy": float(main_obstacle_info.get("dist_proxy", 1000.0)),
                "closing_rate": float(main_obstacle_info.get("closing_rate", 0.0)),
                "track_id": int(main_obstacle_info.get("track_id", -1)),
                "box": main_obstacle_info.get("box", [0,0,0,0])
            }
            msg = Protocol.ui_command(UICommand.SHOW_ALARM, ui_alarm_data)
            self.ui_client.send_request(msg)
            
        elif current_danger_level == DangerLevel.NORMAL and self.last_obstacle_level != DangerLevel.NORMAL:
            # If the danger level goes back to NORMAL, send a clear alarm command
            ui_alarm_data = {
                "level": DangerLevel.NORMAL.value,
                "object_type": "NONE",
                "distance": 0.0,
                "speed": 0.0,
                "direction": "none",
                "risk_level_name": "SAFE",
                "risk_score": 0.0,
                "pttc_s": 1e9,
                "dist_proxy": 1000.0,
                "closing_rate": 0.0,
                "track_id": -1,
                "box": [0,0,0,0]
            }
            msg = Protocol.ui_command(UICommand.SHOW_ALARM, ui_alarm_data)
            self.ui_client.send_request(msg)
            self.last_obstacle_level = DangerLevel.NORMAL


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
        print("[Engine] Sending UPDATE_CART to UI...")
        self.ui_client.send_request(msg)
        print("[Engine] UPDATE_CART sent successfully")

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
        print("[Engine] Quantity updated, cart refreshed")

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
        print("[Engine] Item removed, cart refreshed")

    def reset(self) -> None:
        """Resets the engine's session state."""
        self.last_obstacle_level = DangerLevel.NORMAL
        self._last_product_id = None
        self._last_product_ts = 0.0
