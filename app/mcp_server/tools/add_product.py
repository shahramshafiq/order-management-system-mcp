from datetime import datetime, timezone
from decimal import Decimal

from pydantic import ValidationError as PydanticValidationError

from app.mcp_server import storage
from app.mcp_server.models import Product
from app.utils.errors import DuplicateError, NotFoundError, ValidationError


def add_product(
    name: str,
    sku: str,
    category: str,
    unit_price: str,
    initial_stock: int,
    reorder_threshold: int,
    supplier_id: str,
) -> dict:
    """Register a new product in inventory. Rejects duplicate SKUs and unknown suppliers."""
    products = storage.read_products()
    if any(p.sku == sku for p in products):
        raise DuplicateError(f"SKU '{sku}' is already registered")

    suppliers = storage.read_suppliers()
    if not any(s.id == supplier_id for s in suppliers):
        raise NotFoundError(f"Supplier '{supplier_id}' does not exist")

    try:
        product = Product(
            id=storage.generate_id("PROD"),
            name=name,
            sku=sku,
            category=category,
            unit_price=Decimal(unit_price),
            stock_quantity=initial_stock,
            reserved_quantity=0,
            reorder_threshold=reorder_threshold,
            supplier_id=supplier_id,
            created_at=datetime.now(timezone.utc),
        )
    except PydanticValidationError as e:
        raise ValidationError(str(e)) from e

    products.append(product)
    storage.save_products(products)

    return product.model_dump(mode="json")