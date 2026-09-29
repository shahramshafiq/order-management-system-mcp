from mcp.server.mcpserver import MCPServer

from app.mcp_server.tools.add_product import add_product
from app.mcp_server.tools.create_order import create_order
from app.mcp_server.tools.get_inventory_report import get_inventory_report
from app.mcp_server.tools.restock_product import restock_product
from app.mcp_server.tools.search_inventory import search_inventory
from app.mcp_server.tools.update_order_status import update_order_status

mcp = MCPServer(name="OrderManagement")

mcp.tool()(add_product)
mcp.tool()(search_inventory)
mcp.tool()(create_order)
mcp.tool()(update_order_status)
mcp.tool()(restock_product)
mcp.tool()(get_inventory_report)

if __name__ == "__main__":
    mcp.run(transport="stdio")