# database/transaction_dao.py
from typing import Dict, List, Optional


class TransactionDAO:
    """
    Transaction & Session Data Access Object
    """

    def __init__(self, db_handler):
        self.db = db_handler

    # =========================
    # Shopping Session
    # =========================
    def get_cart_id_by_code(self, cart_code: str) -> Optional[int]:
        """Get cart_id from cart_code"""
        sql = """
        SELECT cart_id
        FROM carts
        WHERE cart_code = %s
        LIMIT 1
        """
        result = self.db.fetch_one(sql, (cart_code,))
        return result["cart_id"] if result else None

    def start_session(self, cart_id: int) -> int:
        """Start new cart session"""
        sql = """
        INSERT INTO shopping_sessions (cart_id, start_time, status)
        VALUES (%s, NOW(), 'ACTIVE')
        """
        session_id = self.db.insert(sql, (cart_id,))
        return session_id

    def end_session(self, session_id: int) -> None:
        sql = """
        UPDATE shopping_sessions
        SET end_time = NOW(),
            status = 'COMPLETED'
        WHERE session_id = %s
        """
        self.db.execute(sql, (session_id,))

    def get_active_session(self, cart_id: int) -> Optional[Dict]:
        sql = """
        SELECT session_id
        FROM shopping_sessions
        WHERE cart_id = %s
          AND status = 'ACTIVE'
        LIMIT 1
        """
        return self.db.fetch_one(sql, (cart_id,))

    # =========================
    # Cart Items
    # =========================
    def add_cart_item(
        self,
        session_id: int,
        product_id: int,
        quantity: int = 1,
    ) -> None:
        sql = """
        INSERT INTO cart_items (session_id, product_id, quantity)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE
            quantity = quantity + VALUES(quantity)
        """
        self.db.execute(sql, (session_id, product_id, quantity))

    def list_cart_items(self, session_id: int) -> List[Dict]:
        """Get all items in cart with product info (consolidates duplicates)"""
        sql = """
        SELECT
            MIN(ci.item_id) as item_id,
            ci.product_id,
            p.name as product_name,
            p.price,
            CAST(SUM(ci.quantity) AS SIGNED) as quantity,
            CAST(SUM(ci.quantity) * p.price AS SIGNED) AS subtotal
        FROM cart_items ci
        JOIN products p ON ci.product_id = p.product_id
        WHERE ci.session_id = %s
        GROUP BY ci.product_id, p.name, p.price
        ORDER BY MIN(ci.added_at) DESC
        """
        return self.db.fetch_all(sql, (session_id,))

    def update_item_quantity(
        self, session_id: int, product_id: int, quantity: int
    ) -> bool:
        """Update quantity of a specific product in cart (handles duplicate rows)"""
        if quantity <= 0:
            return self.remove_cart_item(session_id, product_id)

        # First, consolidate any duplicate rows by summing quantities
        # Then update to the new quantity
        try:
            # Delete all existing rows for this product
            delete_sql = """
            DELETE FROM cart_items
            WHERE session_id = %s AND product_id = %s
            """
            self.db.execute(delete_sql, (session_id, product_id))

            # Insert a single row with the new quantity
            insert_sql = """
            INSERT INTO cart_items (session_id, product_id, quantity)
            VALUES (%s, %s, %s)
            """
            self.db.execute(insert_sql, (session_id, product_id, quantity))
            return True
        except Exception as e:
            print(f"[TransactionDAO] Error updating quantity: {e}")
            return False

    def remove_cart_item(self, session_id: int, product_id: int) -> bool:
        """Remove a specific product from cart"""
        sql = """
        DELETE FROM cart_items
        WHERE session_id = %s AND product_id = %s
        """
        self.db.execute(sql, (session_id, product_id))
        return True

    # =========================
    # Order / Checkout
    # =========================
    def create_order(
        self,
        session_id: int,
        total_amount: int,
        total_items: int,
    ) -> int:
        sql = """
        INSERT INTO orders (
            session_id,
            total_amount,
            total_items
        )
        VALUES (%s, %s, %s)
        """
        return self.db.insert(sql, (session_id, total_amount, total_items))

    def add_order_detail(
        self,
        order_id: int,
        product_id: int,
        snap_price: int,
    ) -> None:
        sql = """
        INSERT INTO order_details (
            order_id,
            product_id,
            snap_price
        )
        VALUES (%s, %s, %s)
        """
        self.db.execute(
            sql,
            (order_id, product_id, snap_price),
        )
