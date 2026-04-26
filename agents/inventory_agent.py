from typing import Any


def run_inventory_agent(inventory: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Scan inventory rows and return items where quantity < min_required."""
    low_stock = []
    for item in inventory:
        qty = item.get("quantity", 0)
        min_req = item.get("min_required", 0)
        if qty < min_req:
            low_stock.append({
                "item_id": item.get("id"),
                "item_name": item.get("item_name"),
                "quantity": qty,
                "min_required": min_req,
                "shortfall": min_req - qty,
                "unit": item.get("unit", ""),
            })
    return low_stock
