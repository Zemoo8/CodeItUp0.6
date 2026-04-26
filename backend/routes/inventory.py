from fastapi import APIRouter
from db import get_connection

router = APIRouter()


# READ
@router.get("/inventory")
def get_inventory():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM inventory;")
    rows = cur.fetchall()
    columns = [desc[0] for desc in cur.description]

    conn.close()

    return {
        "data": [dict(zip(columns, row)) for row in rows]
    }


# CREATE (CRUD TOOL)
@router.post("/inventory")
def add_inventory(item: dict):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO inventory (item_name, quantity, threshold)
        VALUES (%s, %s, %s)
    """, (
        item["item_name"],
        item["quantity"],
        item.get("threshold", 0)
    ))

    conn.commit()
    conn.close()

    return {"status": "added"}