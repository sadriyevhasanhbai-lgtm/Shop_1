"""Sales recording and reports (Mentee 2)."""

import json
import os

import numpy as np
from pydantic import TypeAdapter, ValidationError

import inventory
from models import BestSeller, Product, Sale

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SALES_FILE = os.path.join(BASE_DIR, "sales.json")

SALE_LIST = TypeAdapter(list[Sale])
model

def load_sales() -> list[Sale]:
    """Load sales from the JSON file (empty list on any problem)."""
    try:
        with open(SALES_FILE, "r", encoding="utf-8") as f:
            return SALE_LIST.validate_json(f.read())
    except (FileNotFoundError, ValidationError):
        return []


def save_sales(sales: list[Sale]) -> None:
    """Write all sales to the JSON file."""
    data = [sale.model_dump() for sale in sales]
    with open(SALES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def record_sale(
    products: list[Product],
    sales: list[Sale],
    product_id: str,
    quantity_text: str,
) -> tuple[bool, str]:
    """Record a sale: check everything first, then change data."""
    product_id = product_id.strip()

    # Step 1: checks. Nothing is changed here.
    product = inventory.find_product(products, product_id)
    if product is None:
        return False, "Mahsulot topilmadi."

    quantity = inventory.parse_int(quantity_text)
    if quantity is None or quantity <= 0:
        return False, "Miqdor musbat butun son bo'lishi kerak."
    if quantity > product.stock:
        return False, f"Omborda faqat {product.stock} dona bor."

    # Step 2: changes. Reduce stock, then save the sale.
    ok, message = inventory.reduce_stock(products, product_id, quantity)
    if not ok:
        return False, message

    sale = Sale(
        product_id=product.id,
        name=product.name,
        quantity=quantity,
        unit_price=product.price,  # price at the time of the sale
        total=quantity * product.price,
    )
    sales.append(sale)
    save_sales(sales)
    return True, f"Sotuv yozildi: {sale.total:,} UZS"


def total_revenue(sales: list[Sale]) -> int:
    """Sum of all sale totals."""
    return sum(sale.total for sale in sales)


def best_selling_product(sales: list[Sale]) -> BestSeller | None:
    """Product with the largest total quantity sold, or None."""
    if not sales:
        return None

    totals = {}  # product_id -> [name, total quantity]
    for sale in sales:
        if sale.product_id not in totals:
            totals[sale.product_id] = [sale.name, 0]
        totals[sale.product_id][1] += sale.quantity

    best_id = max(totals, key=lambda pid: totals[pid][1])
    name, quantity = totals[best_id]
    return BestSeller(name=name, quantity=quantity)


def low_stock_products(
    products: list[Product], limit: int = 5
) -> list[Product]:
    """Products with `limit` or fewer units left."""
    return [product for product in products if product.stock <= limit]


def average_sale_amount(sales: list[Sale]) -> float | None:
    """Average sale total, calculated with NumPy. None if no sales."""
    if not sales:
        return None
    totals = np.array([sale.total for sale in sales], dtype=np.int64)
    return float(np.mean(totals))