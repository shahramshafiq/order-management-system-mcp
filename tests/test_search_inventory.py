import pytest

from app.mcp_server.tools.add_product import add_product
from app.mcp_server.tools.search_inventory import search_inventory
from app.utils.errors import ValidationError


def test_search_inventory_finds_by_name(sample_product):
    result = search_inventory(query="widget")
    assert result["total_count"] == 1
    assert result["products"][0]["sku"] == sample_product["sku"]


def test_search_inventory_filters_by_stock_status(sample_product):
    low_stock_result = search_inventory(stock_status="low_stock")
    assert low_stock_result["total_count"] == 0

    in_stock_result = search_inventory(stock_status="in_stock")
    assert in_stock_result["total_count"] == 1


def test_search_inventory_sorts_by_price():
    add_product(
        name="Cheap Item", sku="CHEAP-001", category="Test Category",
        unit_price="10.00", initial_stock=5, reorder_threshold=1, supplier_id="SUP-TEST",
    )
    add_product(
        name="Pricey Item", sku="PRICEY-001", category="Test Category",
        unit_price="500.00", initial_stock=5, reorder_threshold=1, supplier_id="SUP-TEST",
    )

    result = search_inventory(sort_by="price")
    prices = [float(p["unit_price"]) for p in result["products"]]
    assert prices == sorted(prices)


def test_search_inventory_paginates():
    for i in range(5):
        add_product(
            name=f"Product {i}", sku=f"PAG-{i}", category="Test Category",
            unit_price="10.00", initial_stock=5, reorder_threshold=1, supplier_id="SUP-TEST",
        )

    page_one = search_inventory(page=1, page_size=2)
    assert len(page_one["products"]) == 2
    assert page_one["total_count"] == 5
    assert page_one["total_pages"] == 3


def test_search_inventory_rejects_invalid_stock_status():
    with pytest.raises(ValidationError):
        search_inventory(stock_status="not_a_real_status")