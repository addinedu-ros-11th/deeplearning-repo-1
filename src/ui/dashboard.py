# ui/dashboard.py

import sys
from enum import Enum
from typing import Dict, List

from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QFrame,
)
from PyQt6.QtCore import Qt


class DangerLevel(Enum):
    NORMAL = 0
    CAUTION = 1
    CRITICAL = 2


class LEDWidget(QFrame):
    """
    Simple LED indicator widget
    """

    def __init__(self, size: int = 60):
        super().__init__()
        self.setFixedSize(size, size)
        self.setStyleSheet("background-color: green; border-radius: 30px;")

    def set_level(self, level: DangerLevel):
        color_map = {
            DangerLevel.NORMAL: "green",
            DangerLevel.CAUTION: "yellow",
            DangerLevel.CRITICAL: "red",
        }
        color = color_map[level]
        self.setStyleSheet(f"background-color: {color}; border-radius: 30px;")


class CartDashboard(QMainWindow):
    """
    Cart Dashboard UI (PyQt6)

    UI only:
    - Shows cart items
    - Shows total price
    - Shows obstacle danger LED
    - Emits button events (start / end)
    """

    def __init__(self):
        super().__init__()

        self.setWindowTitle("AI Smart Cart Dashboard")
        self.setFixedSize(900, 600)

        # -------------------------
        # State
        # -------------------------
        self.cart_items: List[Dict] = []
        self.total_price: int = 0

        # -------------------------
        # UI
        # -------------------------
        self._build_ui()

    # =========================
    # UI setup
    # =========================
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout()
        central.setLayout(main_layout)

        # -------------------------
        # Header
        # -------------------------
        header = QHBoxLayout()

        title = QLabel("🛒 AI Smart Cart")
        title.setStyleSheet("font-size: 22px; font-weight: bold;")
        header.addWidget(title)

        header.addStretch()

        self.status_label = QLabel("Status: READY")
        self.status_label.setStyleSheet("font-size: 14px;")
        header.addWidget(self.status_label)

        main_layout.addLayout(header)

        # -------------------------
        # Body
        # -------------------------
        body = QHBoxLayout()

        # Cart table
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Product", "Price", "Qty"])
        table_header = self.table.horizontalHeader()
        assert table_header is not None
        table_header.setStretchLastSection(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        body.addWidget(self.table, stretch=3)

        # Right panel
        right = QVBoxLayout()

        # LED
        led_title = QLabel("Obstacle Status")
        led_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        led_title.setStyleSheet("font-size: 16px; font-weight: bold;")
        right.addWidget(led_title)

        self.led = LEDWidget()
        right.addWidget(self.led, alignment=Qt.AlignmentFlag.AlignCenter)

        # Total
        total_title = QLabel("Total Price")
        total_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        total_title.setStyleSheet("font-size: 16px; font-weight: bold;")
        right.addWidget(total_title)

        self.total_label = QLabel("₩ 0")
        self.total_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.total_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        right.addWidget(self.total_label)

        right.addStretch()
        body.addLayout(right, stretch=1)

        main_layout.addLayout(body)

        # -------------------------
        # Footer
        # -------------------------
        footer = QHBoxLayout()

        self.start_btn = QPushButton("Start Cart")
        self.end_btn = QPushButton("End Cart")

        footer.addWidget(self.start_btn)
        footer.addWidget(self.end_btn)
        footer.addStretch()

        main_layout.addLayout(footer)

    # =========================
    # Public API (Controller uses these)
    # =========================
    def add_product(self, product: Dict):
        """
        product = {
            product_id,
            name,
            price
        }
        """
        for item in self.cart_items:
            if item["product_id"] == product["product_id"]:
                item["quantity"] += 1
                self._refresh_table()
                return

        self.cart_items.append(
            {
                "product_id": product["product_id"],
                "name": product["name"],
                "price": product["price"],
                "quantity": 1,
            }
        )
        self._refresh_table()

    def update_cart_display(self, items: list, total: float):
        """
        Update cart display with full cart data from DB
        items = [
            {
                product_id,
                product_name,
                price,
                quantity,
                subtotal
            },
            ...
        ]
        total = total price
        """
        print(
            f"[Dashboard] update_cart_display called: {len(items)} items, total={total}",
            flush=True,
        )

        # 같은 상품을 product_id로 그룹화하고 수량 합산
        grouped_items = {}
        for item in items:
            product_id = item["product_id"]
            if product_id in grouped_items:
                # 이미 있는 상품이면 수량만 증가
                grouped_items[product_id]["quantity"] += item["quantity"]
            else:
                # 새로운 상품이면 추가
                grouped_items[product_id] = {
                    "product_name": item["product_name"],
                    "price": item["price"],
                    "quantity": item["quantity"],
                }

        print(
            f"[Dashboard] Grouped into {len(grouped_items)} unique products", flush=True
        )

        # 테이블 초기화 후 그룹화된 항목 표시
        self.table.setRowCount(0)

        for product_id, item in grouped_items.items():
            row = self.table.rowCount()
            self.table.insertRow(row)

            self.table.setItem(row, 0, QTableWidgetItem(item["product_name"]))
            self.table.setItem(row, 1, QTableWidgetItem(f"₩ {item['price']}"))
            self.table.setItem(row, 2, QTableWidgetItem(str(item["quantity"])))

        self.total_price = total
        self.total_label.setText(f"₩ {int(self.total_price)}")
        print("[Dashboard] Cart display updated successfully", flush=True)

    def set_danger_level(self, level: DangerLevel):
        self.led.set_level(level)

    def set_status(self, status: str):
        self.status_label.setText(f"Status: {status}")

    def reset_cart(self):
        self.cart_items.clear()
        self._refresh_table()

    # =========================
    # Internal
    # =========================
    def _refresh_table(self):
        self.table.setRowCount(0)
        self.total_price = 0

        for item in self.cart_items:
            row = self.table.rowCount()
            self.table.insertRow(row)

            self.table.setItem(row, 0, QTableWidgetItem(item["name"]))
            self.table.setItem(row, 1, QTableWidgetItem(f"₩ {item['price']}"))
            self.table.setItem(row, 2, QTableWidgetItem(str(item["quantity"])))

            self.total_price += item["price"] * item["quantity"]

        self.total_label.setText(f"₩ {self.total_price}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CartDashboard()
    window.show()
    sys.exit(app.exec())
