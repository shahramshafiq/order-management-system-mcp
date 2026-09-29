import uuid
from datetime import datetime, timezone
from decimal import ROUND_HALF_UP, Decimal

from app.mcp_server import storage
from app.mcp_server.models import MovementType, Order, OrderItem, OrderStatus, StatusChange
from app.utils.errors import InsufficientStockError, NotFoundError, ValidationError

TWO_PLACES = Decimal("0.01")


def _round2(value: Decimal) -> Decimal:
    return value.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def create_order(
    customer_name: str,
    customer_email: str,
    items: list[dict],
    discount_percent: str = "0",
    tax_percent: str = "0",
) -> dict:
    """Create a customer order for one or more products. Reserves stock, does not deduct it yet."""
    if not items:
        raise ValidationError("Order must contain at least one item")

    combined: dict[str, int] = {}
    for entry in items:
        product_id = entry["product_id"]
        quantity = entry["quantity"]
        combined[product_id] = combined.get(product_id, 0) + quantity

    products = storage.read_products()

    validated: list[tuple] = []
    for product_id, quantity in combined.items():
        if quantity <= 0:
            raise ValidationError(f"Quantity for product '{product_id}' must be positive")
        product = storage.find_by_id(products, product_id)
        if product is None:
            raise NotFoundError(f"Product '{product_id}' does not exist")
        if product.available_quantity < quantity:
            raise InsufficientStockError(product.sku, quantity, product.available_quantity)
        validated.append((product, quantity))

    order_items = []
    for product, quantity in validated:
        line_total = _round2(product.unit_price * quantity)
        order_items.append(
            OrderItem(
                product_id=product.id,
                product_name=product.name,
                quantity=quantity,
                unit_price=product.unit_price,
                line_total=line_total,
            )
        )

    subtotal = _round2(sum(item.line_total for item in order_items))
    discount = _round2(subtotal * Decimal(discount_percent) / 100)
    tax = _round2((subtotal - discount) * Decimal(tax_percent) / 100)
    total = subtotal - discount + tax

    now = datetime.now(timezone.utc)
    order_id = storage.generate_id("ORD")
    order_number = f"ORD-{now:%Y%m%d}-{uuid.uuid4().hex[:4].upper()}"

    order = Order(
        id=order_id,
        order_number=order_number,
        customer_name=customer_name,
        customer_email=customer_email,
        items=order_items,
        subtotal=subtotal,
        discount=discount,
        tax=tax,
        total=total,
        status=OrderStatus.PENDING,
        status_history=[StatusChange(status=OrderStatus.PENDING, timestamp=now)],
        created_at=now,
    )

    for product, quantity in validated:
        product.reserved_quantity += quantity
    storage.save_products(products)

    for product, quantity in validated:
        storage.record_movement(
            product_id=product.id,
            movement_type=MovementType.RESERVATION,
            quantity=quantity,
            reference=order_number,
            note=f"Reserved for order {order_number}",
        )

    orders = storage.read_orders()
    orders.append(order)
    storage.save_orders(orders)

    return order.model_dump(mode="json")