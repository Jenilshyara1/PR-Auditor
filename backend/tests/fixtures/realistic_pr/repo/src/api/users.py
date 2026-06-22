from fastapi import APIRouter

from src.db import get_connection

router = APIRouter()


@router.get("/users/{user_id}/orders")
def get_user_orders(user_id: str, filter_expr: str | None = None):
    conn = get_connection()
    query = f"SELECT * FROM orders WHERE user_id = '{user_id}'"
    rows = conn.execute(query).fetchall()

    if filter_expr:
        rows = [r for r in rows if eval(filter_expr, {}, {"row": r})]

    return rows
