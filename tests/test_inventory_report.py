from datetime import date, datetime, timedelta, timezone

import pytest

from app.mcp_server.tools.create_order import create_order
from app.mcp_server.tools.get_inventory_report import get_inventory_report
from app.mcp_server.tools.restock_product import restock_product
from app.mcp_server.tools.update_order_status import update_order_status
from app.utils.errors import ValidationError


def test_report_includes_revenue_from_confirmed_order(sample_product):
    order = create_order(
        customer_name="Test Customer",
        customer_email="test@example.com",
        items=[{"product_id": sample_product["id"], "quantity": 2}],
    )
    update_order_status(order["id"], "confirmed")

    today = datetime.now(timezone.utc).date()
    report = get_inventory_report(
        start_date=today.isoformat(),
        end_date=(today + timedelta(days=1)).isoformat(),
    )
    assert report["orders"]["revenue"] == order["total"]
    assert report["orders"]["counts_by_status"]["confirmed"] == 1


def test_report_excludes_orders_outside_date_range(sample_product):
    order = create_order(
        customer_name="Test Customer",
        customer_email="test@example.com",
        items=[{"product_id": sample_product["id"], "quantity": 2}],
    )
    update_order_status(order["id"], "confirmed")

    past_start = date.today() - timedelta(days=30)
    past_end = date.today() - timedelta(days=20)
    report = get_inventory_report(start_date=past_start.isoformat(), end_date=past_end.isoformat())

    assert report["orders"]["revenue"] == "0.00"
    assert report["orders"]["counts_by_status"] == {}


def test_report_calculates_inventory_value_from_latest_restock(sample_product):
    restock_product(
        sku=sample_product["sku"],
        supplier_id=sample_product["supplier_id"],
        quantity=5,
        purchase_order_reference="PO-3003",
        unit_cost="50.00",
    )

    today = datetime.now(timezone.utc).date()
    report = get_inventory_report(
        start_date=today.isoformat(),
        end_date=(today + timedelta(days=1)).isoformat(),
    )
    expected_value = 50.00 * (sample_product["stock_quantity"] + 5)
    assert float(report["inventory"]["total_inventory_value"]) == expected_value


def test_report_rejects_invalid_date():
    with pytest.raises(ValidationError):
        get_inventory_report(start_date="not-a-date", end_date="2026-01-01")