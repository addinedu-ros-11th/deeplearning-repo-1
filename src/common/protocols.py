import time
import json
from enum import IntEnum
from typing import Any, Dict, Optional


# =========================
# Enums
# =========================
class MessageType(IntEnum):
    AI_REQ = 1
    AI_RES = 2
    AI_EVT = 3

    UI_REQ = 10
    UI_CMD = 11
    UI_EVT = 12

    DB_REQ = 20
    DB_RES = 21


class AITask(IntEnum):
    OBSTACLE = 1
    PRODUCT = 2


class UICommand(IntEnum):
    SHOW_ALARM = 1
    ADD_TO_CART = 2
    UPDATE_STATUS = 3
    CHECKOUT_DONE = 4
    UPDATE_CART = 5


class UIRequest(IntEnum):
    START_SESSION = 1
    CHECKOUT = 2
    UPDATE_QUANTITY = 3
    REMOVE_ITEM = 4


class DBAction(IntEnum):
    GET_PRODUCT = 1
    ADD_CART_ITEM = 2
    GET_CART = 3  #    CART_CLEARED = 3


class AIEvent(IntEnum):
    OBSTACLE_DANGER = 1
    PRODUCT_DETECTED = 2


class DangerLevel(IntEnum):
    NORMAL = 0
    CAUTION = 1
    CRITICAL = 2


# =========================
# Protocol
# =========================
class Protocol:
    """
    System-wide JSON control protocol (TCP only)
    Binary data (image/frame) is NOT allowed.
    """

    VERSION = 1

    # -------------------------
    # Core
    # -------------------------
    @staticmethod
    def _base_message(
        msg_type: MessageType,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        return {
            "header": {
                "type": int(msg_type),
                "timestamp": time.time(),
                "version": Protocol.VERSION,
            },
            "payload": payload,
        }

    # =========================
    # AI <-> Main PC2
    # =========================
    @staticmethod
    def ai_request(task: AITask) -> Dict[str, Any]:
        return Protocol._base_message(
            MessageType.AI_REQ,
            {"task": int(task)},
        )

    @staticmethod
    def ai_response(
        status: bool,
        analysis: Dict[str, Any],
        error: Optional[str] = None,
    ) -> Dict[str, Any]:
        payload = {
            "status": status,
            "analysis": analysis,
        }
        if error:
            payload["error"] = error

        return Protocol._base_message(MessageType.AI_RES, payload)

    @staticmethod
    def ai_event(event: AIEvent, data: Dict[str, Any]) -> Dict[str, Any]:
        return Protocol._base_message(
            MessageType.AI_EVT,
            {
                "event": int(event),
                "data": data,
            },
        )

    # =========================
    # UI
    # =========================
    @staticmethod
    def ui_command(
        command: UICommand,
        content: Any,
    ) -> Dict[str, Any]:
        return Protocol._base_message(
            MessageType.UI_CMD,
            {
                "command": int(command),
                "content": content,
            },
        )

    @staticmethod
    def ui_request(
        request: UIRequest,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:
        return Protocol._base_message(
            MessageType.UI_REQ,
            {
                "event": int(request),
                "data": data,
            },
        )

    # =========================
    # DB <-> Main PC2
    # =========================
    @staticmethod
    def db_request(
        action: DBAction,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:
        return Protocol._base_message(
            MessageType.DB_REQ,
            {
                "action": int(action),
                "data": data,
            },
        )

    @staticmethod
    def db_response(
        status: bool,
        data: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"status": status}

        if data is not None:
            payload["data"] = data
        if error:
            payload["error"] = error

        return Protocol._base_message(MessageType.DB_RES, payload)

    # =========================
    # Parsing & Validation
    # =========================
    @staticmethod
    def parse(raw_json: str) -> Dict[str, Any]:
        """
        Parses and validates a JSON message string.

        :raises ValueError: If JSON is malformed or protocol validation fails.
        :return: The parsed message as a dictionary.
        """
        try:
            message = json.loads(raw_json)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {e}")

        if not Protocol.validate(message):
            raise ValueError("Message failed protocol validation.")

        return message

    @staticmethod
    def validate(message: Dict[str, Any]) -> bool:
        try:
            header = message["header"]
            payload = message["payload"]

            MessageType(header["type"])

            return (
                isinstance(header, dict)
                and isinstance(payload, dict)
                and isinstance(header.get("type"), int)
                and header["version"] == Protocol.VERSION
            )
        except Exception:
            return False
