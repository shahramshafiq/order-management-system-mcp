from decimal import Decimal

import pytest

from app.mcp_server import storage
from app.mcp_server.tools.create_order import create_order
from app.utils.errors import InsufficientStockError


def test_create_order_reserves_stock(sample_product):
    create_order(
        customer_name="Test Customer",
        customer_email="test@example.com",
        items=[{"product_id": sample_product["id"], "quantity": 4}],
    )

    products = storage.read_products()
    product = storage.find_by_id(products, sample_product["id"])
    assert product.reserved_quantity == 4
    assert product.stock_quantity == sample_product["stock_quantity"]


def test_create_order_rejects_insufficient_stock(sample_product):
    with pytest.raises(InsufficientStockError):
        create_order(
            customer_name="Test Customer",
            customer_email="test@example.com",
            items=[{"product_id": sample_product["id"], "quantity": 9999}],
        )

    products = storage.read_products()
    product = storage.find_by_id(products, sample_product["id"])
    assert product.reserved_quantity == 0
    assert product.stock_quantity == sample_product["stock_quantity"]


def test_create_order_combines_duplicate_product_lines(sample_product):
    order = create_order(
        customer_name="Test Customer",
        customer_email="test@example.com",
        items=[
            {"product_id": sample_product["id"], "quantity": 2},
            {"product_id": sample_product["id"], "quantity": 3},
        ],
    )
    assert len(order["items"]) == 1
    assert order["items"][0]["quantity"] == 5


def test_create_order_price_unaffected_by_later_price_change(sample_product):
    order = create_order(
        customer_name="Test Customer",
        customer_email="test@example.com",
        items=[{"product_id": sample_product["id"], "quantity": 2}],
    )
    original_total = order["total"]

    products = storage.read_products()
    product = storage.find_by_id(products, sample_product["id"])
    product.unit_price = Decimal("999999.00")
    storage.save_products(products)

    orders = storage.read_orders()
    reloaded_order = storage.find_by_id(orders, order["id"])
    assert str(reloaded_order.total) == original_total