"""
Admin UI - Management interface for system monitoring
관리자 UI - 시스템 모니터링 인터페이스
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
    QTabWidget,
    QTextEdit,
    QGroupBox,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
import socket
import json
import threading
from datetime import datetime


class AdminUI(QMainWindow):
    """관리자 UI 메인 윈도우"""

    def __init__(self, server_host="localhost", server_port=5000):
        super().__init__()
        self.server_host = server_host
        self.server_port = server_port
        self.tcp_socket = None

        self.init_ui()
        self.connect_to_server()

        # 자동 새로고침 타이머
        self.timer = QTimer()
        self.timer.timeout.connect(self.auto_refresh)
        self.timer.start(5000)  # 5초마다 새로고침

    def init_ui(self):
        """UI 초기화"""
        self.setWindowTitle("스마트 카트 - 관리자 화면")
        self.setGeometry(100, 100, 1200, 800)

        # 중앙 위젯
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 메인 레이아웃
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        # 헤더
        header = QLabel("📊 스마트 카트 관리자")
        header.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("background-color: #1976D2; color: white; padding: 20px;")
        main_layout.addWidget(header)

        # 시스템 상태 영역
        status_layout = QHBoxLayout()

        self.active_carts_label = QLabel("활성 카트: 0")
        self.active_carts_label.setFont(QFont("Arial", 14))
        self.active_carts_label.setStyleSheet(
            "background-color: #4CAF50; color: white; padding: 10px; border-radius: 5px;"
        )
        status_layout.addWidget(self.active_carts_label)

        self.total_sales_label = QLabel("총 매출: 0원")
        self.total_sales_label.setFont(QFont("Arial", 14))
        self.total_sales_label.setStyleSheet(
            "background-color: #FF9800; color: white; padding: 10px; border-radius: 5px;"
        )
        status_layout.addWidget(self.total_sales_label)

        self.warnings_label = QLabel("경고: 0")
        self.warnings_label.setFont(QFont("Arial", 14))
        self.warnings_label.setStyleSheet(
            "background-color: #f44336; color: white; padding: 10px; border-radius: 5px;"
        )
        status_layout.addWidget(self.warnings_label)

        main_layout.addLayout(status_layout)

        # 탭 위젯
        tabs = QTabWidget()
        main_layout.addWidget(tabs)

        # 탭 1: 카트 모니터링
        cart_tab = self.create_cart_monitoring_tab()
        tabs.addTab(cart_tab, "카트 모니터링")

        # 탭 2: 장애물 감지
        obstacle_tab = self.create_obstacle_monitoring_tab()
        tabs.addTab(obstacle_tab, "장애물 감지")

        # 탭 3: 구매 이력
        purchase_tab = self.create_purchase_history_tab()
        tabs.addTab(purchase_tab, "구매 이력")

        # 탭 4: 이벤트 로그
        log_tab = self.create_event_log_tab()
        tabs.addTab(log_tab, "이벤트 로그")

        # 버튼 영역
        button_layout = QHBoxLayout()

        self.refresh_button = QPushButton("새로고침")
        self.refresh_button.setFont(QFont("Arial", 12))
        self.refresh_button.setStyleSheet(
            "background-color: #2196F3; color: white; padding: 10px;"
        )
        self.refresh_button.clicked.connect(self.auto_refresh)
        button_layout.addWidget(self.refresh_button)

        self.clear_log_button = QPushButton("로그 지우기")
        self.clear_log_button.setFont(QFont("Arial", 12))
        self.clear_log_button.setStyleSheet(
            "background-color: #9E9E9E; color: white; padding: 10px;"
        )
        self.clear_log_button.clicked.connect(self.clear_logs)
        button_layout.addWidget(self.clear_log_button)

        main_layout.addLayout(button_layout)

        # 상태바
        self.statusBar().showMessage("서버에 연결 중...")

    def create_cart_monitoring_tab(self):
        """카트 모니터링 탭 생성"""
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)

        label = QLabel("현재 활성 카트 목록")
        label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(label)

        self.cart_table = QTableWidget()
        self.cart_table.setColumnCount(4)
        self.cart_table.setHorizontalHeaderLabels(
            ["세션 ID", "상품 수", "총액", "상태"]
        )
        self.cart_table.setFont(QFont("Arial", 10))
        layout.addWidget(self.cart_table)

        return tab

    def create_obstacle_monitoring_tab(self):
        """장애물 감지 탭 생성"""
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)

        label = QLabel("장애물 감지 현황")
        label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(label)

        self.obstacle_table = QTableWidget()
        self.obstacle_table.setColumnCount(6)
        self.obstacle_table.setHorizontalHeaderLabels(
            ["시간", "세션 ID", "유형", "거리", "방향", "경고 레벨"]
        )
        self.obstacle_table.setFont(QFont("Arial", 10))
        layout.addWidget(self.obstacle_table)

        return tab

    def create_purchase_history_tab(self):
        """구매 이력 탭 생성"""
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)

        label = QLabel("구매 이력")
        label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(label)

        self.purchase_table = QTableWidget()
        self.purchase_table.setColumnCount(4)
        self.purchase_table.setHorizontalHeaderLabels(
            ["구매 ID", "세션 ID", "총액", "시간"]
        )
        self.purchase_table.setFont(QFont("Arial", 10))
        layout.addWidget(self.purchase_table)

        return tab

    def create_event_log_tab(self):
        """이벤트 로그 탭 생성"""
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)

        label = QLabel("시스템 이벤트 로그")
        label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(label)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Courier", 10))
        layout.addWidget(self.log_text)

        return tab

    def connect_to_server(self):
        """서버에 연결"""
        try:
            self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.tcp_socket.connect((self.server_host, self.server_port))
            self.statusBar().showMessage("서버에 연결되었습니다")
            self.add_log("관리자 UI가 서버에 연결되었습니다")
        except Exception as e:
            self.statusBar().showMessage(f"서버 연결 실패: {e}")
            self.add_log(f"서버 연결 실패: {e}")

    def auto_refresh(self):
        """자동 새로고침"""
        self.add_log(f'[{datetime.now().strftime("%H:%M:%S")}] 데이터 새로고침')
        # 실제로는 서버에서 데이터를 받아와야 함
        # 여기서는 예시로 UI만 업데이트

    def clear_logs(self):
        """로그 지우기"""
        self.log_text.clear()
        self.add_log("로그가 지워졌습니다")

    def add_log(self, message: str):
        """로그 추가"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        self.log_text.append(log_entry)

    def update_cart_table(self, cart_data: list):
        """카트 테이블 업데이트"""
        self.cart_table.setRowCount(len(cart_data))
        for i, cart in enumerate(cart_data):
            self.cart_table.setItem(i, 0, QTableWidgetItem(cart.get("session_id", "")))
            self.cart_table.setItem(
                i, 1, QTableWidgetItem(str(cart.get("item_count", 0)))
            )
            self.cart_table.setItem(
                i, 2, QTableWidgetItem(f"{cart.get('total', 0):,}원")
            )
            self.cart_table.setItem(i, 3, QTableWidgetItem(cart.get("status", "")))

    def update_obstacle_table(self, obstacle_data: list):
        """장애물 테이블 업데이트"""
        self.obstacle_table.setRowCount(len(obstacle_data))
        for i, obs in enumerate(obstacle_data):
            self.obstacle_table.setItem(
                i, 0, QTableWidgetItem(obs.get("timestamp", ""))
            )
            self.obstacle_table.setItem(
                i, 1, QTableWidgetItem(obs.get("session_id", ""))
            )
            self.obstacle_table.setItem(i, 2, QTableWidgetItem(obs.get("type", "")))
            self.obstacle_table.setItem(
                i, 3, QTableWidgetItem(f"{obs.get('distance', 0):.2f}m")
            )
            self.obstacle_table.setItem(
                i, 4, QTableWidgetItem(obs.get("direction", ""))
            )
            self.obstacle_table.setItem(
                i, 5, QTableWidgetItem(obs.get("warning_level", ""))
            )

    def closeEvent(self, event):
        """창 종료 이벤트"""
        if self.tcp_socket:
            self.tcp_socket.close()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AdminUI()
    window.show()
    sys.exit(app.exec())
