from datetime import datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field
from decimal import Decimal


class OrderStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class MovementType(str, Enum):
    RESERVATION = "reservation"
    RELEASE = "release"
    SALE = "sale"
    SALE_REVERSAL = "sale_reversal"
    RESTOCK = "restock"


class StockStatus(str, Enum):
    IN_STOCK = "in_stock"
    LOW_STOCK = "low_stock"
    OUT_OF_STOCK = "out_of_stock"
    ALL = "all"


class Product(BaseModel):
    id: str
    name: str
    sku: str
    category: str
    unit_price: Decimal = Field(gt=0)
    stock_quantity: int = Field(ge=0)
    reserved_quantity: int = Field(ge=0, default=0)
    reorder_threshold: int = Field(ge=0)
    supplier_id: str
    created_at: datetime

    @property
    def available_quantity(self) -> int:
        return self.stock_quantity - self.reserved_quantity

    @property
    def stock_status(self) -> StockStatus:
        if self.available_quantity <= 0:
            return StockStatus.OUT_OF_STOCK
        if self.available_quantity <= self.reorder_threshold:
            return StockStatus.LOW_STOCK
        return StockStatus.IN_STOCK

class OrderItem(BaseModel):
    product_id: str
    product_name: str
    quantity: int = Field(gt=0)
    unit_price: Decimal = Field(gt=0)
    line_total: Decimal = Field(ge=0)


class StatusChange(BaseModel):
    status: OrderStatus
    timestamp: datetime


class Order(BaseModel):
    id: str
    order_number: str
    customer_name: str
    customer_email: str
    items: list[OrderItem]
    subtotal: Decimal = Field(ge=0)
    discount: Decimal = Field(ge=0)
    tax: Decimal = Field(ge=0)
    total: Decimal = Field(ge=0)
    status: OrderStatus
    status_history: list[StatusChange]
    created_at: datetime


class InventoryMovement(BaseModel):
    id: str
    product_id: str
    movement_type: MovementType
    quantity: int
    reference: str
    timestamp: datetime
    note: str = ""
    unit_cost: Decimal | None = None


class Supplier(BaseModel):
    id: str
    name: str
    contact_email: str

