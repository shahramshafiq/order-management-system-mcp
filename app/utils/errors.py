class AppError(Exception):
    code = "APP_ERROR"

    def __init__(self, message: str):
        self.message = message
        super().__init__(f"{self.code}: {message}")


class NotFoundError(AppError):
    code = "NOT_FOUND"


class DuplicateError(AppError):
    code = "DUPLICATE"


class ValidationError(AppError):
    code = "VALIDATION_ERROR"


class InvalidTransitionError(AppError):
    code = "INVALID_TRANSITION"


class InsufficientStockError(AppError):
    code = "INSUFFICIENT_STOCK"

    def __init__(self, sku: str, requested: int, available: int):
        self.sku = sku
        self.requested = requested
        self.available = available
        super().__init__(f"Cannot reserve {requested} unit(s) of {sku}, only {available} available")