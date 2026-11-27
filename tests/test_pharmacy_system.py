"""Automated unit and integration tests for database, services, transactions, and reports."""

from __future__ import annotations

import csv
import tempfile
import unittest
from datetime import timedelta
from pathlib import Path

from pharmacy.database.db_manager import DatabaseManager
from pharmacy.models.entities import CartItem
from pharmacy.services.inventory_service import InventoryService
from pharmacy.services.report_service import ReportService
from pharmacy.services.sales_service import SalesService
from pharmacy.services.supplier_service import SupplierService
from pharmacy.utils import BusinessRuleError, ValidationError, today_date


class PharmacySystemTestCase(unittest.TestCase):
    """End-to-end backend/service verification using an isolated temp SQLite database."""

    def setUp(self) -> None:
        self._tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self._tmp_dir.name) / "test_pharmacy.db"
        self.db = DatabaseManager(self.db_path)
        self.suppliers = SupplierService(self.db)
        self.inventory = InventoryService(self.db)
        self.sales = SalesService(self.db)
        self.reports = ReportService(self.db)

        self.future_date = (today_date() + timedelta(days=180)).isoformat()
        self.soon_date = (today_date() + timedelta(days=10)).isoformat()
        self.past_date = (today_date() - timedelta(days=5)).isoformat()
        self.today_str = today_date().isoformat()

    def tearDown(self) -> None:
        self.db.close()
        self._tmp_dir.cleanup()

    def test_schema_foreign_keys_and_seed_idempotency(self) -> None:
        fk_enabled = self.db.connection.execute("PRAGMA foreign_keys").fetchone()[0]
        self.assertEqual(fk_enabled, 1)

        first_seed = self.db.seed_sample_data()
        second_seed = self.db.seed_sample_data()
        self.assertTrue(first_seed)
        self.assertFalse(second_seed)
        self.assertGreater(len(self.suppliers.list_suppliers()), 0)
        self.assertGreater(len(self.inventory.list_medicines()), 0)

    def test_supplier_crud_and_delete_protection(self) -> None:
        sup = self.suppliers.create_supplier(
            name="Nordic Meds",
            contact_person="Alice",
            phone="555-1234",
            email="alice@nordic.example",
            address="100 Main St",
        )
        self.assertIsNotNone(sup.id)
        assert sup.id is not None

        updated = self.suppliers.update_supplier(
            supplier_id=sup.id,
            name="Nordic Meds Corp",
            contact_person="Alice B.",
            phone="555-9999",
            email="alice@nordic.example",
            address="200 Oak Ave",
        )
        self.assertEqual(updated.name, "Nordic Meds Corp")

        # Assign a medicine to this supplier; deleting supplier must be blocked
        med = self.inventory.create_medicine(
            name="Ibuprofen 400mg",
            batch_number="IBU-001",
            unit_price=8.0,
            quantity=25,
            expiry_date=self.future_date,
            supplier_id=sup.id,
        )
        with self.assertRaises(BusinessRuleError):
            self.suppliers.delete_supplier(sup.id)

        # Delete medicine first, then supplier deletion succeeds
        assert med.id is not None
        self.inventory.delete_medicine(med.id)
        self.suppliers.delete_supplier(sup.id)
        self.assertIsNone(self.suppliers.get_supplier(sup.id))

    def test_medicine_crud_filtering_and_adjustments(self) -> None:
        sup = self.suppliers.create_supplier(name="Global Health")
        m_valid = self.inventory.create_medicine(
            name="Cetirizine 10mg",
            generic_name="Cetirizine",
            category="Antihistamines",
            batch_number="CTZ-100",
            supplier_id=sup.id,
            cost_price=3.0,
            unit_price=7.5,
            quantity=50,
            reorder_level=15,
            expiry_date=self.future_date,
        )
        m_low = self.inventory.create_medicine(
            name="Loratadine 10mg",
            batch_number="LOR-200",
            unit_price=9.0,
            quantity=5,
            reorder_level=10,
            expiry_date=self.soon_date,
        )
        m_exp = self.inventory.create_medicine(
            name="Aspirin 75mg",
            batch_number="ASP-OLD",
            unit_price=4.0,
            quantity=12,
            reorder_level=5,
            expiry_date=self.past_date,
        )

        self.assertEqual(len(self.inventory.list_medicines(status_filter="all")), 3)
        self.assertEqual(
            [m.batch_number for m in self.inventory.list_medicines(status_filter="low_stock")],
            ["LOR-200"],
        )
        self.assertEqual(
            [m.batch_number for m in self.inventory.list_medicines(status_filter="expiring_soon")],
            ["LOR-200"],
        )
        self.assertEqual(
            [m.batch_number for m in self.inventory.list_medicines(status_filter="expired")],
            ["ASP-OLD"],
        )

        assert m_valid.id is not None
        restocked = self.inventory.restock_medicine(m_valid.id, 15, "PO-778")
        self.assertEqual(restocked.quantity, 65)

        with self.assertRaises(BusinessRuleError):
            self.inventory.adjust_stock(m_valid.id, -100, "Audit Correction")

        assert m_exp.id is not None
        written_off = self.inventory.write_off_expired_stock(m_exp.id)
        self.assertEqual(written_off.quantity, 0)

        assert m_low.id is not None
        updated = self.inventory.update_medicine(
            medicine_id=m_low.id,
            name="Loratadine 10mg Tabs",
            batch_number="LOR-200",
            unit_price=9.5,
            quantity=20,
            expiry_date=self.soon_date,
            reorder_level=10,
        )
        self.assertEqual(updated.quantity, 20)
        self.assertEqual(updated.unit_price, 9.5)

    def test_sales_calculations_and_inventory_decrement(self) -> None:
        med1 = self.inventory.create_medicine(
            name="Amoxicillin 500mg",
            batch_number="AMX-1",
            unit_price=12.50,
            quantity=30,
            expiry_date=self.future_date,
        )
        med2 = self.inventory.create_medicine(
            name="Paracetamol 500mg",
            batch_number="PCM-1",
            unit_price=5.00,
            quantity=20,
            expiry_date=self.future_date,
        )
        assert med1.id is not None and med2.id is not None

        cart = [
            CartItem(med1.id, med1.name, med1.batch_number, med1.unit_price, 2, 30, med1.expiry_date),
            CartItem(med2.id, med2.name, med2.batch_number, med2.unit_price, 3, 20, med2.expiry_date),
        ]
        # Subtotal = 2*12.50 + 3*5.00 = 40.00
        # 10% discount = 4.00 -> taxable = 36.00
        # 5% tax = 1.80 -> total = 37.80
        # Paid = 50.00 -> change = 12.20
        sale = self.sales.create_sale(
            cart_items=cart,
            customer_name="John Doe",
            discount_percent=10,
            tax_percent=5,
            amount_paid=50,
            payment_method="Cash",
        )
        self.assertEqual(sale.subtotal, 40.00)
        self.assertEqual(sale.discount_amount, 4.00)
        self.assertEqual(sale.tax_amount, 1.80)
        self.assertEqual(sale.total_amount, 37.80)
        self.assertEqual(sale.change_due, 12.20)
        self.assertEqual(len(sale.items), 2)

        # Verify inventory decremented accurately
        self.assertEqual(self.inventory.get_medicine(med1.id).quantity, 28)  # type: ignore[union-attr]
        self.assertEqual(self.inventory.get_medicine(med2.id).quantity, 17)  # type: ignore[union-attr]

        # Historical sale prevents hard deletion of sold medicine
        with self.assertRaises(BusinessRuleError):
            self.inventory.delete_medicine(med1.id)

    def test_expiry_restriction_and_atomic_rollback(self) -> None:
        valid_med = self.inventory.create_medicine(
            name="Vitamin D3",
            batch_number="VD3-10",
            unit_price=10.00,
            quantity=10,
            expiry_date=self.future_date,
        )
        expired_med = self.inventory.create_medicine(
            name="Expired Syrup",
            batch_number="EXP-99",
            unit_price=15.00,
            quantity=8,
            expiry_date=self.past_date,
        )
        expiring_today_med = self.inventory.create_medicine(
            name="Today Expiry Drops",
            batch_number="EXP-TODAY",
            unit_price=6.00,
            quantity=5,
            expiry_date=self.today_str,
        )
        assert valid_med.id is not None
        assert expired_med.id is not None
        assert expiring_today_med.id is not None

        # Cart validation blocks expired and expiring-today items
        with self.assertRaises(BusinessRuleError):
            self.sales.validate_medicine_for_cart(expired_med.id, 1)
        with self.assertRaises(BusinessRuleError):
            self.sales.validate_medicine_for_cart(expiring_today_med.id, 1)

        # Multi-item checkout where item #2 is expired MUST roll back item #1 too
        mixed_cart = [
            CartItem(valid_med.id, valid_med.name, valid_med.batch_number, 10.0, 3, 10, self.future_date),
            CartItem(expired_med.id, expired_med.name, expired_med.batch_number, 15.0, 1, 8, self.past_date),
        ]
        with self.assertRaises(BusinessRuleError):
            self.sales.create_sale(cart_items=mixed_cart)

        # Verify atomic rollback: stock untouched and 0 sales persisted
        self.assertEqual(self.inventory.get_medicine(valid_med.id).quantity, 10)  # type: ignore[union-attr]
        self.assertEqual(len(self.sales.list_sales()), 0)

        # Insufficient stock on item #2 also rolls back
        over_cart = [
            CartItem(valid_med.id, valid_med.name, valid_med.batch_number, 10.0, 2, 10, self.future_date),
            CartItem(valid_med.id, valid_med.name, valid_med.batch_number, 10.0, 99, 10, self.future_date),
        ]
        with self.assertRaises(BusinessRuleError):
            self.sales.create_sale(cart_items=over_cart)
        self.assertEqual(self.inventory.get_medicine(valid_med.id).quantity, 10)  # type: ignore[union-attr]
        self.assertEqual(len(self.sales.list_sales()), 0)

        # Underpayment raises ValidationError and rolls back
        with self.assertRaises(ValidationError):
            self.sales.create_sale(
                cart_items=[
                    CartItem(valid_med.id, valid_med.name, valid_med.batch_number, 10.0, 2, 10, self.future_date)
                ],
                amount_paid=5.0,
            )
        self.assertEqual(self.inventory.get_medicine(valid_med.id).quantity, 10)  # type: ignore[union-attr]

    def test_dashboard_reports_and_csv_export(self) -> None:
        sup = self.suppliers.create_supplier("MediCore")
        m1 = self.inventory.create_medicine(
            name="Zinc 50mg",
            category="Vitamins & Supplements",
            batch_number="ZNC-1",
            supplier_id=sup.id,
            cost_price=2.0,
            unit_price=6.0,
            quantity=10,
            reorder_level=10,
            expiry_date=self.future_date,
        )
        assert m1.id is not None
        self.sales.create_sale(
            cart_items=[
                CartItem(m1.id, m1.name, m1.batch_number, 6.0, 4, 10, self.future_date)
            ],
            tax_percent=0,
        )

        stats = self.reports.get_dashboard_stats()
        self.assertEqual(stats.total_medicines, 1)
        self.assertEqual(stats.total_stock_units, 6)
        self.assertEqual(stats.inventory_retail_value, 36.0)
        self.assertEqual(stats.inventory_cost_value, 12.0)
        self.assertEqual(stats.low_stock_count, 1)
        self.assertEqual(stats.today_sales_count, 1)
        self.assertEqual(stats.today_revenue, 24.0)

        summary = self.reports.get_sales_summary_by_range(self.today_str, self.today_str)
        self.assertEqual(summary["invoice_count"], 1)
        self.assertEqual(summary["net_revenue"], 24.0)

        top = self.reports.get_top_selling_medicines()
        self.assertEqual(len(top), 1)
        self.assertEqual(top[0]["units_sold"], 4)

        sales_csv = Path(self._tmp_dir.name) / "sales.csv"
        inv_csv = Path(self._tmp_dir.name) / "inventory.csv"
        self.assertEqual(self.reports.export_sales_csv(sales_csv), 1)
        self.assertEqual(self.reports.export_inventory_csv(inv_csv), 1)

        with sales_csv.open("r", encoding="utf-8") as fh:
            rows = list(csv.reader(fh))
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0][0], "Invoice Number")


if __name__ == "__main__":
    unittest.main()
