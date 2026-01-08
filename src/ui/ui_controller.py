# ui/ui_controller.py

import threading
import socket
import json

from PyQt6.QtCore import QObject, pyqtSignal

from ui.dashboard import CartDashboard, DangerLevel
from common.config import config
from common.protocols import (
    Protocol,
    MessageType,
    UICommand,
    UIRequest,
)


class UIEventSignals(QObject):
    """
    Qt Signals to safely update UI from background threads
    """

    product_added = pyqtSignal(dict)
    danger_updated = pyqtSignal(int)
    status_changed = pyqtSignal(str)
    reset_cart = pyqtSignal()
    cart_updated = pyqtSignal(list, float)  # items, total


class UIController:
    """
    UI Controller (PC3)

    - Runs TCP server to receive commands from MainPC2
    - Converts messages to Qt Signals
    - Connects UI buttons → MainPC2 commands
    """

    def __init__(self, dashboard: CartDashboard, main_pc2_ip: str):
        self.dashboard = dashboard
        self.main_pc2_ip = main_pc2_ip
        if config is None:
            raise RuntimeError("Configuration could not be loaded. Exiting.")

        self.signals = UIEventSignals()
        self._bind_signals()
        self._bind_buttons()

        self.server_thread = threading.Thread(
            target=self._tcp_server_loop,
            daemon=True,
        )
        self.server_thread.start()

    # =========================
    # Signal bindings
    # =========================
    def _bind_signals(self):
        self.signals.product_added.connect(self.dashboard.add_product)
        self.signals.danger_updated.connect(
            lambda lvl: self.dashboard.set_danger_level(DangerLevel(lvl))
        )
        self.signals.status_changed.connect(self.dashboard.set_status)
        self.signals.reset_cart.connect(self.dashboard.reset_cart)
        self.signals.cart_updated.connect(self.dashboard.update_cart_display)

    # =========================
    # Button → MainPC2
    # =========================
    def _bind_buttons(self):
        self.dashboard.start_btn.clicked.connect(self._send_start)
        self.dashboard.end_btn.clicked.connect(self._send_checkout)

    def _send_start(self):
        msg = Protocol.ui_request(UIRequest.START_SESSION, {})
        self._send_to_main(msg)
        self.dashboard.set_status("IN USE")

    def _send_checkout(self):
        msg = Protocol.ui_request(UIRequest.CHECKOUT, {})
        self._send_to_main(msg)
        self.dashboard.set_status("CHECKOUT")

    def _send_to_main(self, message: dict):
        port = config.network.pc2_main.ui_port
        try:
            # Connect to the main hub's UI request port
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((self.main_pc2_ip, port))
                s.sendall(json.dumps(message).encode())
        except Exception as e:
            print(f"[UI] Send error to {self.main_pc2_ip}:{port}: {e}", flush=True)

    # =========================
    # TCP Server (MainPC2 → UI)
    # =========================
    def _tcp_server_loop(self):
        # Listen on the UI's designated command port
        port = config.network.pc3_ui.ui_port
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(("0.0.0.0", port))
        sock.listen(5)

        print(f"[UI] TCP server listening for commands on port {port}", flush=True)

        while True:
            conn, _ = sock.accept()
            with conn:
                # Read 4-byte header (length prefix)
                header = conn.recv(4)
                if not header or len(header) != 4:
                    continue

                import struct

                payload_length = struct.unpack(">I", header)[0]

                # Read the full payload
                data = bytearray()
                while len(data) < payload_length:
                    chunk = conn.recv(min(8192, payload_length - len(data)))
                    if not chunk:
                        break
                    data.extend(chunk)

                if len(data) < payload_length:
                    print("[UI] Incomplete message received", flush=True)
                    continue

                self._handle_message(bytes(data))

    def _handle_message(self, raw: bytes):
        try:
            message = Protocol.parse(raw.decode())
        except ValueError as e:
            print(f"[UI] Error parsing message: {e}", flush=True)
            return
        except Exception as e:
            print(f"[UI] An unexpected error occurred: {e}", flush=True)
            return

        if MessageType(message["header"]["type"]) != MessageType.UI_CMD:
            return

        payload = message["payload"]
        cmd = UICommand(payload["command"])

        print(f"[UI] Received command: {cmd}", flush=True)

        if cmd == UICommand.ADD_TO_CART:
            print(f"[UI] ADD_TO_CART: {payload['content']}", flush=True)
            self.signals.product_added.emit(payload["content"])

        elif cmd == UICommand.UPDATE_CART:
            # New handler for UPDATE_CART command
            items = payload["content"]["items"]
            total = payload["content"]["total"]
            print(f"[UI] UPDATE_CART: {len(items)} items, total={total}", flush=True)
            print(f"[UI] Items: {items}", flush=True)
            self.signals.cart_updated.emit(items, total)

        elif cmd == UICommand.SHOW_ALARM:
            self.signals.danger_updated.emit(payload["content"]["level"])

        elif cmd == UICommand.CHECKOUT_DONE:
            self.signals.reset_cart.emit()
            self.signals.status_changed.emit("READY")
