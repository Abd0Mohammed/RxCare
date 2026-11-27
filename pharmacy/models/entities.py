"""Dataclasses representing core pharmacy domain entities."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Supplier:
    id: int | None
    name: str
    contact_person: str = ""
    phone: str = ""
    email: str = ""
    address: str = ""
    created_at: str = ""
    medicine_count: int = 0


@dataclass
class Medicine:
    id: int | None
    name: str
    generic_name: str
    category: str
    batch_number: str
    supplier_id: int | None
    cost_price: float
    unit_price: float
    quantity: int
    reorder_level: int
    expiry_date: str
    description: str = ""
    created_at: str = ""
    updated_at: str = ""
    supplier_name: str = ""


@dataclass
class CartItem:
    medicine_id: int
    medicine_name: str
    batch_number: str
    unit_price: float
    quantity: int
    available_stock: int
    expiry_date: str

    @property
    def line_total(self) -> float:
        return round(self.unit_price * self.quantity, 2)


@dataclass
class SaleItem:
    id: int | None
    sale_id: int | None
    medicine_id: int
    medicine_name: str
    batch_number: str
    quantity: int
    unit_price: float
    line_total: float


@dataclass
class Sale:
    id: int | None
    invoice_number: str
    customer_name: str
    customer_phone: str
    subtotal: float
    discount_percent: float
    discount_amount: float
    tax_percent: float
    tax_amount: float
    total_amount: float
    amount_paid: float
    change_due: float
    payment_method: str
    sale_date: str
    notes: str = ""
    items: list[SaleItem] = field(default_factory=list)


@dataclass
class StockAdjustment:
    id: int | None
    medicine_id: int
    change_qty: int
    reason: str
    reference_note: str
    created_at: str
    medicine_name: str = ""


@dataclass
class DashboardStats:
    total_medicines: int
    total_stock_units: int
    inventory_retail_value: float
    inventory_cost_value: float
    low_stock_count: int
    expiring_soon_count: int
    expired_count: int
    total_suppliers: int
    today_sales_count: int
    today_revenue: float
    total_sales_count: int
    total_revenue: float
