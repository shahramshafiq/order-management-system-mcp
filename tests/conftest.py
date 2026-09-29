import json

import pytest

from app.config import settings
from app.mcp_server.tools.add_product import add_product


@pytest.fixture(autouse=True)
def isolated_data_files(tmp_path, monkeypatch):
    """Point every storage file at a fresh, empty temp file for each test, so tests never touch the real data/ files."""
    products_file = tmp_path / "products.json"
    orders_file = tmp_path / "orders.json"
    suppliers_file = tmp_path / "suppliers.json"
    movements_file = tmp_path / "movements.json"
    idempotency_file = tmp_path / "idempotency_keys.json"

    products_file.write_text(json.dumps({"products": []}))
    orders_file.write_text(json.dumps({"orders": []}))
    suppliers_file.write_text(json.dumps({
        "suppliers": [{"id": "SUP-TEST", "name": "Test Supplier", "contact_email": "test@example.com"}]
    }))
    movements_file.write_text(json.dumps({"movements": []}))
    idempotency_file.write_text(json.dumps({"keys": {}}))

    monkeypatch.setattr(settings, "products_file", str(products_file))
    monkeypatch.setattr(settings, "orders_file", str(orders_file))
    monkeypatch.setattr(settings, "suppliers_file", str(suppliers_file))
    monkeypatch.setattr(settings, "movements_file", str(movements_file))
    monkeypatch.setattr(settings, "idempotency_file", str(idempotency_file))


@pytest.fixture
def sample_product():
    """A real product already added to the isolated test data, ready for other tools to act on."""
    return add_product(
        name="Test Widget",
        sku="WID-001",
        category="Test Category",
        unit_price="100.00",
        initial_stock=20,
        reorder_threshold=5,
        supplier_id="SUP-TEST",
    )