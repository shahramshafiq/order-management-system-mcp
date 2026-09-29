import pytest

from app.mcp_server import storage
from app.mcp_server.tools.create_order import create_order
from app.mcp_server.tools.restock_product import restock_product
from app.utils.errors import DuplicateError, ValidationError


def test_restock_increases_stock_without_touching_reservations(sample_product):
    create_order(
        customer_name="Test Customer",
        customer_email="test@example.com",
        items=[{"product_id": sample_product["id"], "quantity": 3}],
    )

    result = restock_product(
        sku=sample_product["sku"],
        supplier_id=sample_product["supplier_id"],
        quantity=10,
        purchase_order_reference="PO-1001",
        unit_cost="80.00",
    )
    assert result["previous_stock"] == sample_product["stock_quantity"]
    assert result["updated_stock"] == sample_product["stock_quantity"] + 10

    products = storage.read_products()
    product = storage.find_by_id(products, sample_product["id"])
    assert product.reserved_quantity == 3


def test_restock_rejects_repeated_purchase_order_reference(sample_product):
    restock_product(
        sku=sample_product["sku"],
        supplier_id=sample_product["supplier_id"],
        quantity=10,
        purchase_order_reference="PO-1001",
        unit_cost="80.00",
    )

    with pytest.raises(DuplicateError):
        restock_product(
            sku=sample_product["sku"],
            supplier_id=sample_product["supplier_id"],
            quantity=10,
            purchase_order_reference="PO-1001",
            unit_cost="80.00",
        )

    products = storage.read_products()
    product = storage.find_by_id(products, sample_product["id"])
    assert product.stock_quantity == sample_product["stock_quantity"] + 10


def test_restock_rejects_mismatched_supplier(sample_product):
    with pytest.raises(ValidationError):
        restock_product(
            sku=sample_product["sku"],
            supplier_id="SUP-WRONG",
            quantity=10,
            purchase_order_reference="PO-2002",
            unit_cost="80.00",
        )