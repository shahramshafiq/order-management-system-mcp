import json
import threading
import uuid
from datetime import datetime, timezone
from typing import TypeVar

from pydantic import BaseModel

from app.config import settings
from app.mcp_server.models import InventoryMovement, MovementType, Order, Product, Supplier

_write_lock = threading.Lock()

ModelType = TypeVar("ModelType", bound=BaseModel)


def read_all(file_path: str, key: str, model: type[ModelType]) -> list[ModelType]:
    with open(file_path, encoding="utf-8") as f:
        data = json.load(f)
    return [model.model_validate(item) for item in data[key]]


def write_all(file_path: str, key: str, items: list[BaseModel]) -> None:
    with _write_lock:
        data = {key: [item.model_dump(mode="json") for item in items]}
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)


def find_by_id(items: list[ModelType], item_id: str) -> ModelType | None:
    return next((item for item in items if item.id == item_id), None)


def generate_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


def read_products() -> list[Product]:
    return read_all(settings.products_file, "products", Product)


def save_products(products: list[Product]) -> None:
    write_all(settings.products_file, "products", products)


def read_orders() -> list[Order]:
    return read_all(settings.orders_file, "orders", Order)


def save_orders(orders: list[Order]) -> None:
    write_all(settings.orders_file, "orders", orders)


def read_suppliers() -> list[Supplier]:
    return read_all(settings.suppliers_file, "suppliers", Supplier)


def read_movements() -> list[InventoryMovement]:
    return read_all(settings.movements_file, "movements", InventoryMovement)


def save_movements(movements: list[InventoryMovement]) -> None:
    write_all(settings.movements_file, "movements", movements)


def record_movement(
    product_id: str, movement_type: MovementType, quantity: int, reference: str, note: str = ""
) -> InventoryMovement:
    movement = InventoryMovement(
        id=generate_id("MOV"),
        product_id=product_id,
        movement_type=movement_type,
        quantity=quantity,
        reference=reference,
        timestamp=datetime.now(timezone.utc),
        note=note,
    )
    movements = read_movements()
    movements.append(movement)
    save_movements(movements)
    return movement


def read_idempotency_keys() -> dict:
    with open(settings.idempotency_file, encoding="utf-8") as f:
        return json.load(f)["keys"]


def save_idempotency_key(key: str, result: dict) -> None:
    with _write_lock:
        with open(settings.idempotency_file, encoding="utf-8") as f:
            data = json.load(f)
        data["keys"][key] = result
        with open(settings.idempotency_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)