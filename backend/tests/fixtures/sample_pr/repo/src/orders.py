def calculate_discount(order_total: float, customer_tier: str) -> float:
    if customer_tier == "gold":
        return order_total * 0.9
    return order_total
