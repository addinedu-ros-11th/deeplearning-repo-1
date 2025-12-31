#!/usr/bin/env python3
"""
Enhanced AI Smart Cart UI Application
- Standby / Shopping / Checkout states
- Real-time cart updates with toast notifications
- DB-integrated session management
- Obstacle warnings and safety alerts
"""

import sys
import yaml
from PyQt6.QtWidgets import QApplication

from ui.dashboard_v2 import CartDashboard
from ui.ui_controller_v2 import UIController


def main():
    """Main entry point for Enhanced Smart Cart UI"""

    # Load network config
    try:
        with open("configs/network_config.yaml", "r") as f:
            net_cfg = yaml.safe_load(f)
        main_pc2_ip = net_cfg["pc2_main"]["ip"]
        print(f"[UI App] Connecting to Main Hub at {main_pc2_ip}")
    except (IOError, KeyError, TypeError) as e:
        print("=" * 60)
        print(f"WARNING: Could not load Main PC IP from config: {e}")
        print("  Defaulting to '127.0.0.1' for local testing.")
        print("=" * 60)
        main_pc2_ip = "127.0.0.1"

    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("AI Smart Cart")
    app.setOrganizationName("SmartCart")

    # Create dashboard
    dashboard = CartDashboard()

    # Create controller with DB integration
    _controller = UIController(
        dashboard=dashboard,
        main_pc2_ip=main_pc2_ip,
        cart_id=1,  # Default cart ID
    )

    print("=" * 60)
    print("🛒 AI Smart Cart UI Application Started")
    print(f"   Main Hub: {main_pc2_ip}")
    print(f"   Database: {'Connected' if _controller.db else 'Disconnected'}")
    print("=" * 60)

    # Show window
    dashboard.show()

    # Run application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
