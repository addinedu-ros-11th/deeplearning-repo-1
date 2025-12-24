"""
User UI - Cart display interface for customers
사용자 UI - 고객용 카트 표시 인터페이스
"""

import sys
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QScrollArea,
    QFrame,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap
import socket
import json
import threading


class UserUI(QMainWindow):
    """사용자 UI 메인 윈도우"""

    # 시그널 정의
    cart_updated = pyqtSignal(dict)
    alarm_triggered = pyqtSignal(str, str)

    def __init__(self, server_host="localhost", server_port=5000):
        super().__init__()
        self.server_host = server_host
        self.server_port = server_port
        self.session_id = None
        self.tcp_socket = None

        self.init_ui()
        self.connect_to_server()

        # 시그널 연결
        self.cart_updated.connect(self.update_cart_display)
        self.alarm_triggered.connect(self.show_alarm)

    def init_ui(self):
        """UI 초기화"""
        self.setWindowTitle("스마트 카트 - 사용자 화면")
        self.setGeometry(100, 100, 800, 600)

        # 중앙 위젯
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 메인 레이아웃
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        # 헤더
        header = QLabel("🛒 스마트 카트")
        header.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("background-color: #4CAF50; color: white; padding: 20px;")
        main_layout.addWidget(header)

        # 알람 영역
        self.alarm_label = QLabel("")
        self.alarm_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.alarm_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.alarm_label.setStyleSheet(
            "background-color: #ff5252; color: white; padding: 15px;"
        )
        self.alarm_label.setVisible(False)
        main_layout.addWidget(self.alarm_label)

        # 카트 정보 영역
        info_layout = QHBoxLayout()

        self.session_label = QLabel("세션: -")
        self.session_label.setFont(QFont("Arial", 12))
        info_layout.addWidget(self.session_label)

        info_layout.addStretch()

        self.total_label = QLabel("총액: 0원")
        self.total_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        self.total_label.setStyleSheet("color: #4CAF50;")
        info_layout.addWidget(self.total_label)

        main_layout.addLayout(info_layout)

        # 구분선
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        main_layout.addWidget(line)

        # 상품 목록 테이블
        self.cart_table = QTableWidget()
        self.cart_table.setColumnCount(5)
        self.cart_table.setHorizontalHeaderLabels(
            ["상품명", "카테고리", "수량", "단가", "합계"]
        )
        self.cart_table.setColumnWidth(0, 200)
        self.cart_table.setColumnWidth(1, 100)
        self.cart_table.setColumnWidth(2, 80)
        self.cart_table.setColumnWidth(3, 100)
        self.cart_table.setColumnWidth(4, 100)
        self.cart_table.setFont(QFont("Arial", 11))
        main_layout.addWidget(self.cart_table)

        # 버튼 영역
        button_layout = QHBoxLayout()

        self.start_button = QPushButton("쇼핑 시작")
        self.start_button.setFont(QFont("Arial", 12))
        self.start_button.setStyleSheet(
            "background-color: #4CAF50; color: white; padding: 10px;"
        )
        self.start_button.clicked.connect(self.start_shopping)
        button_layout.addWidget(self.start_button)

        self.refresh_button = QPushButton("새로고침")
        self.refresh_button.setFont(QFont("Arial", 12))
        self.refresh_button.setStyleSheet(
            "background-color: #2196F3; color: white; padding: 10px;"
        )
        self.refresh_button.clicked.connect(self.refresh_cart)
        button_layout.addWidget(self.refresh_button)

        self.purchase_button = QPushButton("구매 완료")
        self.purchase_button.setFont(QFont("Arial", 12))
        self.purchase_button.setStyleSheet(
            "background-color: #FF9800; color: white; padding: 10px;"
        )
        self.purchase_button.clicked.connect(self.complete_purchase)
        self.purchase_button.setEnabled(False)
        button_layout.addWidget(self.purchase_button)

        main_layout.addLayout(button_layout)

        # 상태바
        self.statusBar().showMessage("서버에 연결 중...")

    def connect_to_server(self):
        """서버에 연결"""
        try:
            self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.tcp_socket.connect((self.server_host, self.server_port))
            self.statusBar().showMessage("서버에 연결되었습니다")

            # 수신 스레드 시작
            receive_thread = threading.Thread(target=self.receive_messages)
            receive_thread.daemon = True
            receive_thread.start()
        except Exception as e:
            self.statusBar().showMessage(f"서버 연결 실패: {e}")

    def start_shopping(self):
        """쇼핑 시작"""
        message = {"type": "cart_start"}
        self.send_message(message)
        self.start_button.setEnabled(False)
        self.purchase_button.setEnabled(True)

    def refresh_cart(self):
        """카트 새로고침"""
        if self.session_id:
            message = {"type": "get_cart_info", "session_id": self.session_id}
            self.send_message(message)

    def complete_purchase(self):
        """구매 완료"""
        if self.session_id:
            message = {
                "type": "purchase_complete",
                "session_id": self.session_id,
                "payment_method": "card",
            }
            self.send_message(message)
            self.start_button.setEnabled(True)
            self.purchase_button.setEnabled(False)

    def send_message(self, message: dict):
        """메시지 전송"""
        try:
            data = json.dumps(message) + "\n"
            self.tcp_socket.send(data.encode("utf-8"))
        except Exception as e:
            self.statusBar().showMessage(f"메시지 전송 실패: {e}")

    def receive_messages(self):
        """메시지 수신"""
        buffer = ""
        while True:
            try:
                data = self.tcp_socket.recv(4096).decode("utf-8")
                if not data:
                    break

                buffer += data

                while "\n" in buffer:
                    message, buffer = buffer.split("\n", 1)
                    if message:
                        self.process_message(json.loads(message))
            except Exception as e:
                print(f"Error receiving message: {e}")
                break

    def process_message(self, message: dict):
        """수신한 메시지 처리"""
        # 세션 ID 저장
        if "session_id" in message:
            self.session_id = message["session_id"]
            self.session_label.setText(f"세션: {self.session_id}")

        # 카트 정보 업데이트
        if "cart_info" in message:
            self.cart_updated.emit(message["cart_info"])

        # 총액 업데이트
        if "cart_total" in message:
            self.total_label.setText(f"총액: {message['cart_total']:,}원")

    def update_cart_display(self, cart_info: dict):
        """카트 화면 업데이트"""
        items = cart_info.get("items", [])
        self.cart_table.setRowCount(len(items))

        for i, item in enumerate(items):
            self.cart_table.setItem(i, 0, QTableWidgetItem(item["product_name"]))
            self.cart_table.setItem(i, 1, QTableWidgetItem(item["category"]))
            self.cart_table.setItem(i, 2, QTableWidgetItem(str(item["quantity"])))
            self.cart_table.setItem(i, 3, QTableWidgetItem(f"{item['unit_price']:,}원"))
            self.cart_table.setItem(
                i, 4, QTableWidgetItem(f"{item['total_price']:,}원")
            )

        # 총액 업데이트
        total = cart_info.get("total_amount", 0)
        self.total_label.setText(f"총액: {total:,}원")

    def show_alarm(self, level: str, message: str):
        """알람 표시"""
        self.alarm_label.setText(f"⚠️ {message}")
        self.alarm_label.setVisible(True)

        # 3초 후 알람 숨김
        QTimer.singleShot(3000, lambda: self.alarm_label.setVisible(False))

    def closeEvent(self, event):
        """창 종료 이벤트"""
        if self.tcp_socket:
            self.tcp_socket.close()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = UserUI()
    window.show()
    sys.exit(app.exec())
