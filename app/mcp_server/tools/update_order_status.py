from datetime import datetime, timezone

from app.mcp_server import storage
from app.mcp_server.models import MovementType, Order, OrderStatus, Product, StatusChange
from app.utils.errors import InvalidTransitionError, NotFoundError

VALID_TRANSITIONS = {
    OrderStatus.PENDING: {OrderStatus.CONFIRMED, OrderStatus.CANCELLED},
    OrderStatus.CONFIRMED: {OrderStatus.SHIPPED, OrderStatus.CANCELLED},
    OrderStatus.SHIPPED: {OrderStatus.DELIVERED},
    OrderStatus.DELIVERED: set(),
    OrderStatus.CANCELLED: set(),
}


def update_order_status(order_id: str, new_status: str) -> dict:
    """Move an order to a new status, enforcing valid transitions and applying the matching stock effect."""
    orders = storage.read_orders()
    order = storage.find_by_id(orders, order_id)
    if order is None:
        raise NotFoundError(f"Order '{order_id}' does not exist")

    try:
        target_status = OrderStatus(new_status)
    except ValueError:
        raise InvalidTransitionError(f"'{new_status}' is not a recognized order status")

    if target_status not in VALID_TRANSITIONS[order.status]:
        raise InvalidTransitionError(f"Cannot move an order from '{order.status.value}' to '{target_status.value}'")

    products = storage.read_products()

    if order.status == OrderStatus.PENDING and target_status == OrderStatus.CONFIRMED:
        _commit_as_sold(order, products)
    elif order.status == OrderStatus.PENDING and target_status == OrderStatus.CANCELLED:
        _release_reservation(order, products)
    elif order.status == OrderStatus.CONFIRMED and target_status == OrderStatus.CANCELLED:
        _reverse_sale(order, products)

    order.status = target_status
    order.status_history.append(StatusChange(status=target_status, timestamp=datetime.now(timezone.utc)))
    storage.save_orders(orders)

    return order.model_dump(mode="json")


def _commit_as_sold(order: Order, products: list[Product]) -> None:
    for item in order.items:
        product = storage.find_by_id(products, item.product_id)
        product.stock_quantity -= item.quantity
        product.reserved_quantity -= item.quantity
        storage.record_movement(
            product_id=item.product_id,
            movement_type=MovementType.SALE,
            quantity=item.quantity,
            reference=order.order_number,
            note=f"Confirmed as sold for order {order.order_number}",
        )
    storage.save_products(products)


def _release_reservation(order: Order, products: list[Product]) -> None:
    for item in order.items:
        product = storage.find_by_id(products, item.product_id)
        product.reserved_quantity -= item.quantity
        storage.record_movement(
            product_id=item.product_id,
            movement_type=MovementType.RELEASE,
            quantity=item.quantity,
            reference=order.order_number,
            note=f"Reservation released, order {order.order_number} cancelled",
        )
    storage.save_products(products)


def _reverse_sale(order: Order, products: list[Product]) -> None:
    for item in order.items:
        product = storage.find_by_id(products, item.product_id)
        product.stock_quantity += item.quantity
        storage.record_movement(
            product_id=item.product_id,
            movement_type=MovementType.SALE_REVERSAL,
            quantity=item.quantity,
            reference=order.order_number,
            note=f"Sale reversed, order {order.order_number} cancelled before shipment",
        )
    storage.save_products(products)