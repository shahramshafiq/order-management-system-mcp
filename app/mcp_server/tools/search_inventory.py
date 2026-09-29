import math
from typing import Literal

from app.mcp_server import storage
from app.mcp_server.models import Product, StockStatus
from app.utils.errors import ValidationError

SORT_FIELDS = {
    "price": lambda p: p.unit_price,
    "available_quantity": lambda p: p.available_quantity,
    "name": lambda p: p.name.lower(),
}


def _serialize(product: Product) -> dict:
    data = product.model_dump(mode="json")
    data["available_quantity"] = product.available_quantity
    data["stock_status"] = product.stock_status.value
    return data


def search_inventory(
    query: str = "",
    category: str | None = None,
    supplier_id: str | None = None,
    stock_status: StockStatus = StockStatus.ALL,
    sort_by: Literal["price", "available_quantity", "name"] = "name",
    page: int = 1,
    page_size: int = 10,
) -> dict:
    """Search, filter, sort, and paginate the product catalog."""
    try:
        status_filter = StockStatus(stock_status)
    except ValueError:
        raise ValidationError(f"Invalid stock_status '{stock_status}'")

    if sort_by not in SORT_FIELDS:
        raise ValidationError(f"Invalid sort_by '{sort_by}', must be one of {list(SORT_FIELDS)}")

    if page < 1 or page_size < 1:
        raise ValidationError("page and page_size must be at least 1")

    products = storage.read_products()

    if query:
        query_lower = query.lower()
        products = [p for p in products if query_lower in p.name.lower() or query_lower in p.sku.lower()]

    if category:
        products = [p for p in products if p.category == category]

    if supplier_id:
        products = [p for p in products if p.supplier_id == supplier_id]

    if status_filter != StockStatus.ALL:
        products = [p for p in products if p.stock_status == status_filter]

    products.sort(key=SORT_FIELDS[sort_by])

    total_count = len(products)
    total_pages = math.ceil(total_count / page_size) if total_count else 0
    start = (page - 1) * page_size
    page_products = products[start : start + page_size]

    return {
        "products": [_serialize(p) for p in page_products],
        "total_count": total_count,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }