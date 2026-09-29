import pytest

from app.mcp_server import storage
from app.mcp_server.tools.create_order import create_order
from app.mcp_server.tools.update_order_status import update_order_status
from app.utils.errors import InvalidTransitionError


@pytest.fixture
def pending_order(sample_product):
    return create_order(
        customer_name="Test Customer",
        customer_email="test@example.com",
        items=[{"product_id": sample_product["id"], "quantity": 4}],
    )


def test_confirm_commits_stock_as_sold(sample_product, pending_order):
    update_order_status(pending_order["id"], "confirmed")

    products = storage.read_products()
    product = storage.find_by_id(products, sample_product["id"])
    assert product.reserved_quantity == 0
    assert product.stock_quantity == sample_product["stock_quantity"] - 4


def test_confirming_twice_rejected_no_duplicate_deduction(sample_product, pending_order):
    update_order_status(pending_order["id"], "confirmed")

    with pytest.raises(InvalidTransitionError):
        update_order_status(pending_order["id"], "confirmed")

    products = storage.read_products()
    product = storage.find_by_id(products, sample_product["id"])
    assert product.stock_quantity == sample_product["stock_quantity"] - 4


def test_cancel_confirmed_order_reverses_sale(sample_product, pending_order):
    update_order_status(pending_order["id"], "confirmed")
    update_order_status(pending_order["id"], "cancelled")

    products = storage.read_products()
    product = storage.find_by_id(products, sample_product["id"])
    assert product.stock_quantity == sample_product["stock_quantity"]
    assert product.reserved_quantity == 0


def test_cancel_shipped_order_rejected(pending_order):
    update_order_status(pending_order["id"], "confirmed")
    update_order_status(pending_order["id"], "shipped")

    with pytest.raises(InvalidTransitionError):
        update_order_status(pending_order["id"], "cancelled")