import pytest

from app.mcp_server.tools.add_product import add_product
from app.utils.errors import DuplicateError, NotFoundError, ValidationError


def test_add_product_succeeds():
    product = add_product(
        name="Wireless Mouse",
        sku="MOU-001",
        category="Electronics",
        unit_price="2500.00",
        initial_stock=20,
        reorder_threshold=5,
        supplier_id="SUP-TEST",
    )
    assert product["sku"] == "MOU-001"
    assert product["stock_quantity"] == 20
    assert product["reserved_quantity"] == 0
    assert product["id"].startswith("PROD-")


def test_add_product_rejects_duplicate_sku(sample_product):
    with pytest.raises(DuplicateError):
        add_product(
            name="Another Widget",
            sku=sample_product["sku"],
            category="Test Category",
            unit_price="50.00",
            initial_stock=10,
            reorder_threshold=2,
            supplier_id="SUP-TEST",
        )


def test_add_product_rejects_unknown_supplier():
    with pytest.raises(NotFoundError):
        add_product(
            name="Orphan Product",
            sku="ORPH-001",
            category="Test Category",
            unit_price="50.00",
            initial_stock=10,
            reorder_threshold=2,
            supplier_id="SUP-DOES-NOT-EXIST",
        )


def test_add_product_rejects_negative_price():
    with pytest.raises(ValidationError):
        add_product(
            name="Bad Price Product",
            sku="BAD-001",
            category="Test Category",
            unit_price="-10.00",
            initial_stock=10,
            reorder_threshold=2,
            supplier_id="SUP-TEST",
        )