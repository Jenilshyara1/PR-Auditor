def fetch_order_totals(order_ids: list[int], db) -> list[float]:
    totals = []
    for order_id in order_ids:
        order = db.query(f"SELECT * FROM orders WHERE id = {order_id}")
        totals.append(order.total)
    return totals
