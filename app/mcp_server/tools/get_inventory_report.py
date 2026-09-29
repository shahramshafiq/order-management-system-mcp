from datetime import date, datetime, time, timezone
from decimal import ROUND_HALF_UP, Decimal

from app.mcp_server import storage
from app.mcp_server.models import InventoryMovement, MovementType, OrderStatus, StockStatus
from app.utils.errors import ValidationError

REVENUE_STATUSES = {OrderStatus.CONFIRMED, OrderStatus.SHIPPED, OrderStatus.DELIVERED}
TWO_PLACES = Decimal("0.01")


def _round2(value: Decimal) -> Decimal:
    return value.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def _latest_unit_cost(product_id: str, movements: list[InventoryMovement]) -> Decimal | None:
    restocks = [
        m for m in movements
        if m.product_id == product_id and m.movement_type == MovementType.RESTOCK and m.unit_cost is not None
    ]
    if not restocks:
        return None
    return max(restocks, key=lambda m: m.timestamp).unit_cost


def get_inventory_report(
    start_date: str,
    end_date: str,
    category: str | None = None,
    supplier_id: str | None = None,
) -> dict:
    """Inventory snapshot plus sales/restock activity between start_date (inclusive) and end_date (exclusive)."""
    try:
        start_dt = datetime.combine(date.fromisoformat(start_date), time.min, tzinfo=timezone.utc)
        end_dt = datetime.combine(date.fromisoformat(end_date), time.min, tzinfo=timezone.utc)
    except ValueError as e:
        raise ValidationError(f"Invalid date: {e}")

    products = storage.read_products()
    if category:
        products = [p for p in products if p.category == category]
    if supplier_id:
        products = [p for p in products if p.supplier_id == supplier_id]
    filtered_ids = {p.id for p in products}

    movements = storage.read_movements()

    total_inventory_value = Decimal("0")
    for product in products:
        cost = _latest_unit_cost(product.id, movements)
        if cost is not None:
            total_inventory_value += cost * product.stock_quantity

    low_stock = [p for p in products if p.stock_status == StockStatus.LOW_STOCK]
    out_of_stock = [p for p in products if p.stock_status == StockStatus.OUT_OF_STOCK]

    orders = storage.read_orders()
    orders_in_range = [o for o in orders if start_dt <= o.created_at < end_dt]

    order_counts_by_status: dict[str, int] = {}
    for order in orders_in_range:
        order_counts_by_status[order.status.value] = order_counts_by_status.get(order.status.value, 0) + 1

    revenue = _round2(sum((o.total for o in orders_in_range if o.status in REVENUE_STATUSES), Decimal("0")))

    sold_quantities: dict[str, int] = {}
    for movement in movements:
        if (
            movement.movement_type == MovementType.SALE
            and start_dt <= movement.timestamp < end_dt
            and movement.product_id in filtered_ids
        ):
            sold_quantities[movement.product_id] = sold_quantities.get(movement.product_id, 0) + movement.quantity

    best_sellers = sorted(sold_quantities.items(), key=lambda kv: kv[1], reverse=True)[:5]
    best_selling_products = []
    for product_id, quantity_sold in best_sellers:
        product = storage.find_by_id(products, product_id)
        best_selling_products.append(
            {"product_id": product_id, "sku": product.sku, "name": product.name, "quantity_sold": quantity_sold}
        )

    stock_received = sum(
        m.quantity
        for m in movements
        if m.movement_type == MovementType.RESTOCK and start_dt <= m.timestamp < end_dt and m.product_id in filtered_ids
    )

    return {
        "period": {"start": start_date, "end": end_date},
        "filters": {"category": category, "supplier_id": supplier_id},
        "inventory": {
            "total_products": len(products),
            "total_physical_units": sum(p.stock_quantity for p in products),
            "total_reserved_units": sum(p.reserved_quantity for p in products),
            "total_available_units": sum(p.available_quantity for p in products),
            "total_inventory_value": str(_round2(total_inventory_value)),
        },
        "low_stock_products": [
            {"sku": p.sku, "name": p.name, "available_quantity": p.available_quantity, "reorder_threshold": p.reorder_threshold}
            for p in low_stock
        ],
        "out_of_stock_products": [{"sku": p.sku, "name": p.name} for p in out_of_stock],
        "orders": {
            "counts_by_status": order_counts_by_status,
            "revenue": str(revenue),
        },
        "best_selling_products": best_selling_products,
        "stock_received": stock_received,
    }