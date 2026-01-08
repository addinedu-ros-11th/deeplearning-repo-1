import time
import pytest
import sys
import os
# ensure src/ is on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from core.engine import SmartCartEngine


class DummyUIClient:
    def __init__(self):
        self.sent_messages = []

    def send_request(self, msg):
        self.sent_messages.append(msg)


class DummyTXDAO:
    def __init__(self):
        self.added = []
        self._items = []

    def add_cart_item(self, session_id, product_id, quantity=1):
        self.added.append((session_id, product_id, quantity))
        # append to internal list as a simple item dict
        self._items.append({"product_id": product_id, "product_name": f"P{product_id}", "quantity": 1, "price": 100, "subtotal": 100})

    def list_cart_items(self, session_id):
        return list(self._items)


class DummyProductDAO:
    def __init__(self, products):
        # products: dict id -> dict
        self.products = products

    def get_product_by_id(self, product_id):
        return self.products.get(product_id)


class DummyObstacleDAO:
    def log_obstacle(self, *args, **kwargs):
        pass


@pytest.fixture
def setup_engine():
    products = {
        1: {"product_id": 1, "name": "Cola", "price": 1500},
        2: {"product_id": 2, "name": "Water", "price": 800},
    }
    prod_dao = DummyProductDAO(products)
    tx = DummyTXDAO()
    obs = DummyObstacleDAO()
    ui_client = DummyUIClient()
    engine = SmartCartEngine(prod_dao, tx, obs, ui_client)
    return engine, tx, ui_client


def test_process_product_event_adds_item_and_sends_update(setup_engine):
    engine, tx, ui_client = setup_engine
    session_id = 42

    # Simulate product event
    event = {"product_id": 1, "confidence": 0.95}
    engine.process_product_event(event, session_id)

    # Verify DB add called
    assert (session_id, 1, 1) in tx.added

    # Verify UPDATE_CART message was sent once
    assert len(ui_client.sent_messages) == 1
    # Basic check that payload contains UPDATE_CART (protocol format is JSON-like dict)
    message = ui_client.sent_messages[0]
    assert "payload" in message
    content = message["payload"].get("content", {})
    assert content.get("items") is not None
    assert content.get("total") is not None


def test_debouncing_prevents_duplicate_add(setup_engine):
    engine, tx, ui_client = setup_engine
    session_id = 7

    # send same product twice in quick succession
    event = {"product_id": 2, "confidence": 0.9}

    engine.process_product_event(event, session_id)
    # immediate second should be debounced
    engine.process_product_event(event, session_id)

    assert len(tx.added) == 1

    # after waiting longer than debounce interval, should add again
    time.sleep(engine.DUPLICATE_PRODUCT_INTERVAL_SEC + 0.1)
    engine.process_product_event(event, session_id)
    assert len(tx.added) == 2
