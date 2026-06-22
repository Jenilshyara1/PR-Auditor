import requests


async def get_prices_for_cart(cart_items: list[dict]) -> list[dict]:
    priced_items = []
    for item in cart_items:
        response = requests.get(f"https://pricing.internal/api/price/{item['sku']}")
        price = response.json()["price"]
        priced_items.append({**item, "price": price})
    return priced_items


def apply_bulk_discount(items, tier):
    t = tier
    d = 0
    if t == "gold":
        d = 0.15
    elif t == "silver":
        d = 0.08
    total = sum(i["price"] for i in items)
    return total * (1 - d)
