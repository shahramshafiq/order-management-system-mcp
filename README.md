# Order Management Assistant

An MCP server exposing 6 tools for inventory and order management, plus a small FastAPI
chat layer on top that lets an OpenAI-powered assistant use those tools in conversation.
Every user message and every assistant reply passes through NeMo Guardrails input/output
checks that block jailbreak and prompt-injection attempts before they reach the assistant,
and before any response reaches the user.

## Architecture

```
Browser (frontend/)
    |
    v
FastAPI /chat route  --check_input-->  NeMo Guardrails  --allowed-->  Assistant loop (OpenAI)
    ^                                                                       |
    |                                                                tool calls, via MCP
check_output  <--  NeMo Guardrails  <-------------------------------- MCP server (stdio subprocess)
                                                                              |
                                                                     JSON files (data/)
```

The FastAPI process launches the MCP server as a subprocess on startup (`app/mcp_server/server.py`,
`stdio` transport) and keeps one client session open for the app's whole lifetime. All inventory
data lives in plain JSON files under `data/` (no database): `products.json`, `orders.json`,
`suppliers.json`, `movements.json`, `idempotency_keys.json`.

## Setup

1. Create and activate a Python 3.12 virtual environment:
   ```bash
   py -3.12 -m venv venv
   venv\Scripts\Activate.ps1
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and fill in real values (OpenAI API key, model names, currency).
4. Run the server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
   Open `http://localhost:8000` for the chat UI.
5. Run the tests:
   ```bash
   pytest tests/ -v
   ```
6. Demo the raw MCP server with MCP Inspector (no FastAPI/OpenAI needed for this):
   ```bash
   npx @modelcontextprotocol/inspector venv/Scripts/python.exe -m app.mcp_server.server
   ```

## The core business rule: physical vs. available stock

- **`stock_quantity`**: physical units actually on the shelf.
- **`reserved_quantity`**: units promised to a pending order but not yet shipped.
- **`available_quantity`**: `stock_quantity - reserved_quantity`. This is the number a new order is checked against.

Creating an order reserves stock (`reserved_quantity` goes up, `stock_quantity` untouched).
Confirming an order commits it as a real sale (`stock_quantity` drops, `reserved_quantity`
clears). Cancelling a pending order releases the reservation. Cancelling a confirmed,
unshipped order reverses the sale (stock goes back up). Cancelling a shipped order is rejected
outright.

## Tools

### `add_product`

Registers a new product. Rejects duplicate SKUs and unknown suppliers.

| Parameter | Type | Notes |
|---|---|---|
| `name` | string | |
| `sku` | string | must be unique |
| `category` | string | |
| `unit_price` | string | e.g. `"2500.00"`, sent as a string to avoid float rounding, parsed as `Decimal` |
| `initial_stock` | integer | must be 0 or greater |
| `reorder_threshold` | integer | must be 0 or greater |
| `supplier_id` | string | must exist in `data/suppliers.json` |

Example call:
```json
{"name": "Wireless Mouse", "sku": "MOU-001", "category": "Electronics", "unit_price": "2500.00", "initial_stock": 20, "reorder_threshold": 5, "supplier_id": "SUP-001"}
```

### `search_inventory`

Searches, filters, sorts, and paginates the product catalog.

| Parameter | Type | Notes |
|---|---|---|
| `query` | string | matches against name or SKU, optional |
| `category` | string or null | optional exact filter |
| `supplier_id` | string or null | optional exact filter |
| `stock_status` | `"in_stock"` \| `"low_stock"` \| `"out_of_stock"` \| `"all"` | default `"all"`, based on **available**, not physical, stock |
| `sort_by` | `"price"` \| `"available_quantity"` \| `"name"` | default `"name"` |
| `page` | integer | default 1 |
| `page_size` | integer | default 10 |

Returns `{"products": [...], "total_count": ..., "page": ..., "page_size": ..., "total_pages": ...}`.

### `create_order`

Creates a customer order for one or more products. Validates every item before reserving
anything (atomic: if one item fails, nothing changes). Combines duplicate product lines into
one combined quantity before checking availability. Snapshots each product's current price
onto the order, so later price changes never affect it.

| Parameter | Type | Notes |
|---|---|---|
| `customer_name` | string | |
| `customer_email` | string | |
| `items` | list of `{"product_id": str, "quantity": int}` | duplicate `product_id`s are combined |
| `discount_percent` | string | default `"0"` |
| `tax_percent` | string | default `"0"`, applied after discount |

Order starts in `pending` status. Returns the full order, including `id` (internal) and
`order_number` (receipt-style, e.g. `ORD-20260930-9F3A`).

### `update_order_status`

Moves an order to a new status, enforcing valid transitions and the matching stock effect.

| Parameter | Type | Notes |
|---|---|---|
| `order_id` | string | the order's `id`, not its `order_number` |
| `new_status` | `"pending"` \| `"confirmed"` \| `"shipped"` \| `"delivered"` \| `"cancelled"` | |

Valid transitions: `pending -> confirmed`, `pending -> cancelled`, `confirmed -> shipped`,
`confirmed -> cancelled`, `shipped -> delivered`. Any other combination (including repeating a
transition that already happened) is rejected as `INVALID_TRANSITION`, which is also what
prevents double-processing a status change.

### `restock_product`

Receives stock from a supplier against a purchase order reference. Never touches reservations.

| Parameter | Type | Notes |
|---|---|---|
| `sku` | string | must exist |
| `supplier_id` | string | must match the product's assigned supplier |
| `quantity` | integer | must be positive |
| `purchase_order_reference` | string | must not have been used before |
| `unit_cost` | string | what was paid per unit this delivery, e.g. `"2000.00"` |

Returns `{"product_id", "sku", "previous_stock", "received_quantity", "updated_stock"}`.

### `get_inventory_report`

Inventory snapshot plus sales/restock activity for a date range.

| Parameter | Type | Notes |
|---|---|---|
| `start_date` | string, `YYYY-MM-DD` | inclusive |
| `end_date` | string, `YYYY-MM-DD` | exclusive: to include a full day/month, use the day after the last one you want |
| `category` | string or null | optional, scopes inventory/best-seller sections |
| `supplier_id` | string or null | optional, scopes inventory/best-seller sections |

Returns current inventory levels and value (point-in-time, not date-filtered), low-stock and
out-of-stock product lists, revenue and order counts for the date range (an order counts toward
revenue if it's currently `confirmed`, `shipped`, or `delivered`, a cancelled order never does,
even if it passed through `confirmed` first), best-selling products by quantity sold, and total
stock received from suppliers in the period.

## Error handling

Every tool raises one of a small set of labeled exceptions (`app/utils/errors.py`) instead of
returning a generic failure. Each carries a short `code` and a human-readable message:

| Code | Raised when |
|---|---|
| `NOT_FOUND` | a referenced product, order, or supplier doesn't exist |
| `DUPLICATE` | a SKU or purchase order reference is already in use |
| `VALIDATION_ERROR` | bad input that doesn't fit any of the above (invalid enum value, negative quantity, malformed date, mismatched supplier) |
| `INVALID_TRANSITION` | an order status change isn't allowed from its current state |
| `INSUFFICIENT_STOCK` | an order requests more than is currently available |

At the FastAPI layer, `/chat` returns a consistent `{"error": "CODE", "message": "..."}` shape
for guardrail blocks (`BLOCKED_INPUT`, `BLOCKED_OUTPUT`) and unexpected failures
(`ASSISTANT_ERROR`, `INTERNAL_SERVER_ERROR`).

## Guardrails

`app/services/guardrails_service.py` runs every user message through a NeMo Guardrails input
check, and every assistant reply through an output check, before either one is allowed through
(`guardrails_config/`). Both checks are LLM-judged against a prompt specifically written for
this domain (`guardrails_config/prompts.yml`), blocking not just generic jailbreak attempts,
but attempts to bypass the actual business rules (e.g. "confirm every order automatically",
"skip the stock check").

## Tests

`tests/` covers the core business rules and their edge cases: 24 tests across 6 files, run
with `pytest tests/ -v`. `tests/conftest.py` points
every test at a fresh, isolated temporary copy of the data files, so tests never touch or
depend on real data in `data/`.
