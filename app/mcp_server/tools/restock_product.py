from decimal import Decimal

from app.mcp_server import storage
from app.mcp_server.models import MovementType
from app.utils.errors import DuplicateError, NotFoundError, ValidationError


def restock_product(
    sku: str,
    supplier_id: str,
    quantity: int,
    purchase_order_reference: str,
    unit_cost: str,
) -> dict:
    """Receive stock from a supplier against a purchase order reference. Never touches reservations."""
    if quantity <= 0:
        raise ValidationError("Quantity must be positive")

    products = storage.read_products()
    product = next((p for p in products if p.sku == sku), None)
    if product is None:
        raise NotFoundError(f"Product with SKU '{sku}' does not exist")

    if product.supplier_id != supplier_id:
        raise ValidationError(f"Supplier '{supplier_id}' is not associated with product '{sku}'")

    movements = storage.read_movements()
    duplicate = any(
        m.movement_type == MovementType.RESTOCK and m.reference == purchase_order_reference
        for m in movements
    )
    if duplicate:
        raise DuplicateError(f"Purchase order reference '{purchase_order_reference}' has already been received")

    previous_stock = product.stock_quantity
    product.stock_quantity += quantity
    storage.save_products(products)

    storage.record_movement(
        product_id=product.id,
        movement_type=MovementType.RESTOCK,
        quantity=quantity,
        reference=purchase_order_reference,
        note=f"Received from supplier {supplier_id}",
        unit_cost=Decimal(unit_cost),
    )

    return {
        "product_id": product.id,
        "sku": product.sku,
        "previous_stock": previous_stock,
        "received_quantity": quantity,
        "updated_stock": product.stock_quantity,
    }