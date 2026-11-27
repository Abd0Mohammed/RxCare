"""Automated tests for RxCare Web Edition adapters, analytics, POS session state, and reruns."""

from __future__ import annotations

import tempfile
import threading
import unittest
from datetime import timedelta
from pathlib import Path

from pharmacy.utils import BusinessRuleError, ValidationError, today_date
from web_app.config import DEFAULT_WEB_DB_PATH
from web_app.core.db_adapter import resolve_web_db_path
from web_app.core.web_services import WebAppContainer, WebSessionController


class WebEditionTestCase(unittest.TestCase):
    """Tests web DB isolation, thread-safety, analytics/profit, POS session state, and reruns."""

    def setUp(self) -> None:
        self._tmp_dir = tempfile.TemporaryDirectory()
        self.web_db_path = Path(self._tmp_dir.name) / "pharmacy_web_test.db"
        self.app = WebAppContainer(db_path=self.web_db_path, seed_if_empty=False)

        self.future_date = (today_date() + timedelta(days=180)).isoformat()
        self.soon_date = (today_date() + timedelta(days=10)).isoformat()
        self.past_date = (today_date() - timedelta(days=7)).isoformat()
        self.today_str = today_date().isoformat()

    def tearDown(self) -> None:
        self.app.close()
        self._tmp_dir.cleanup()

    def test_web_db_isolation_and_seed_once_across_reruns(self) -> None:
        resolved = resolve_web_db_path()
        self.assertEqual(resolved, DEFAULT_WEB_DB_PATH)
        self.assertNotEqual(resolved.name, "pharmacy.db")

        self.assertEqual(
            resolve_web_db_path(db_url="sqlite:///:memory:"),
            ":memory:",
        )
        self.assertEqual(
            resolve_web_db_path(db_url="sqlite:///custom/web.db"),
            Path("custom/web.db"),
        )
        with self.assertRaises(NotImplementedError):
            resolve_web_db_path(db_url="postgresql://user:pass@host/db")

        # Simulate first startup + subsequent Streamlit reruns creating container
        c1 = WebAppContainer(db_path=self.web_db_path, seed_if_empty=True)
        sup_count_1 = len(c1.supplier_service.list_suppliers())
        med_count_1 = len(c1.inventory_service.list_medicines())
        c1.close()

        c2 = WebAppContainer(db_path=self.web_db_path, seed_if_empty=True)
        self.assertEqual(len(c2.supplier_service.list_suppliers()), sup_count_1)
        self.assertEqual(len(c2.inventory_service.list_medicines()), med_count_1)
        c2.close()

        # Verify one-shot flash message lifecycle
        session_state: dict[str, object] = {}
        WebSessionController.set_flash_success(session_state, "Saved!")
        self.assertEqual(WebSessionController.consume_flash_success(session_state), "Saved!")
        self.assertIsNone(WebSessionController.consume_flash_success(session_state))

    def test_thread_safe_reads_and_writes(self) -> None:
        errors: list[Exception] = []

        def worker(idx: int) -> None:
            try:
                self.app.supplier_service.create_supplier(name=f"Thread Supplier {idx}")
                _ = self.app.report_service.get_dashboard_stats()
            except Exception as exc:  # pragma: no cover
                errors.append(exc)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(6)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(errors, [])
        self.assertEqual(len(self.app.supplier_service.list_suppliers()), 6)

    def test_medicine_category_filter_and_crud(self) -> None:
        sup = self.app.supplier_service.create_supplier("WebPharma")
        m1 = self.app.inventory_service.create_medicine(
            name="Amoxicillin 500",
            category="Antibiotics",
            batch_number="WEB-AMX-1",
            supplier_id=sup.id,
            cost_price=5.0,
            unit_price=12.0,
            quantity=30,
            reorder_level=10,
            expiry_date=self.future_date,
        )
        self.app.inventory_service.create_medicine(
            name="Vitamin C 1000",
            category="Vitamins & Supplements",
            batch_number="WEB-VTC-1",
            supplier_id=sup.id,
            cost_price=2.0,
            unit_price=6.0,
            quantity=4,
            reorder_level=10,
            expiry_date=self.soon_date,
        )

        cats = self.app.analytics_service.list_categories(self.app.inventory_service)
        self.assertEqual(cats, ["Antibiotics", "Vitamins & Supplements"])

        filtered = self.app.analytics_service.filter_medicines(
            self.app.inventory_service, category="Antibiotics"
        )
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].batch_number, "WEB-AMX-1")

        assert m1.id is not None
        self.app.inventory_service.delete_medicine(m1.id)
        self.assertIsNone(self.app.inventory_service.get_medicine(m1.id))

    def test_pos_session_cart_profit_expiry_and_rerun_idempotency(self) -> None:
        med_ok = self.app.inventory_service.create_medicine(
            name="Ibuprofen 400mg",
            category="Analgesics",
            batch_number="WEB-IBU-1",
            cost_price=4.00,
            unit_price=10.00,
            quantity=12,
            reorder_level=5,
            expiry_date=self.future_date,
        )
        med_exp = self.app.inventory_service.create_medicine(
            name="Old Cough Syrup",
            category="Respiratory",
            batch_number="WEB-EXP-1",
            cost_price=3.00,
            unit_price=8.00,
            quantity=5,
            reorder_level=2,
            expiry_date=self.past_date,
        )
        assert med_ok.id is not None and med_exp.id is not None

        session_state: dict[str, object] = {}
        WebSessionController.ensure_initialized(session_state)

        # Expired medicine blocked from cart
        with self.assertRaises(BusinessRuleError):
            WebSessionController.add_to_cart(
                session_state, self.app.sales_service, med_exp.id, 1
            )

        # Insufficient stock blocked
        with self.assertRaises(BusinessRuleError):
            WebSessionController.add_to_cart(
                session_state, self.app.sales_service, med_ok.id, 50
            )

        # Valid add + profit calculation
        WebSessionController.add_to_cart(
            session_state, self.app.sales_service, med_ok.id, 3
        )
        cart_items = list(WebSessionController.get_cart(session_state).values())
        profit_preview = self.app.analytics_service.calculate_cart_profit(
            cart_items, discount_percent=10.0
        )
        # Subtotal=30, Cost=12, Gross Profit=18, 10% disc=3 -> Net Profit=15
        self.assertEqual(profit_preview["cost"], 12.00)
        self.assertEqual(profit_preview["gross_profit"], 18.00)
        self.assertEqual(profit_preview["net_profit"], 15.00)

        # Capture token before checkout to simulate an accidental rerun replay
        token_before = session_state[WebSessionController.TOKEN_KEY]
        sale_1, created_1 = WebSessionController.complete_sale_idempotent(
            session_state=session_state,
            sales_service=self.app.sales_service,
            customer_name="Web Customer",
            customer_phone="555-0100",
            discount_percent=10.0,
            tax_percent=5.0,
            amount_paid=None,
            payment_method="Card",
        )
        self.assertTrue(created_1)
        self.assertEqual(sale_1.total_amount, 28.35)  # (30 - 3) * 1.05
        self.assertEqual(self.app.inventory_service.get_medicine(med_ok.id).quantity, 9)  # type: ignore[union-attr]
        self.assertEqual(WebSessionController.get_cart(session_state), {})

        # Simulate rerun replay with same token
        session_state[WebSessionController.TOKEN_KEY] = token_before
        sale_2, created_2 = WebSessionController.complete_sale_idempotent(
            session_state=session_state,
            sales_service=self.app.sales_service,
            customer_name="Web Customer",
            customer_phone="555-0100",
            discount_percent=10.0,
            tax_percent=5.0,
            amount_paid=None,
            payment_method="Card",
        )
        self.assertFalse(created_2)
        self.assertEqual(sale_1.id, sale_2.id)
        # Stock must still be 9 (never double-decremented)
        self.assertEqual(self.app.inventory_service.get_medicine(med_ok.id).quantity, 9)  # type: ignore[union-attr]

    def test_reports_daily_sales_and_profit_summary(self) -> None:
        med = self.app.inventory_service.create_medicine(
            name="Paracetamol 500mg",
            category="Analgesics",
            batch_number="WEB-PCM-1",
            cost_price=2.50,
            unit_price=7.50,
            quantity=20,
            reorder_level=5,
            expiry_date=self.future_date,
        )
        assert med.id is not None

        session_state: dict[str, object] = {}
        WebSessionController.add_to_cart(session_state, self.app.sales_service, med.id, 4)
        WebSessionController.complete_sale_idempotent(
            session_state=session_state,
            sales_service=self.app.sales_service,
            customer_name="Alice",
            customer_phone="",
            discount_percent=0.0,
            tax_percent=0.0,
            amount_paid=30.0,
            payment_method="Cash",
        )

        profit = self.app.analytics_service.get_profit_summary(self.today_str, self.today_str)
        self.assertEqual(profit.transaction_count, 1)
        self.assertEqual(profit.gross_revenue, 30.0)
        self.assertEqual(profit.gross_cost, 10.0)
        self.assertEqual(profit.net_profit, 20.0)

        daily = self.app.analytics_service.get_daily_sales_series(self.today_str, self.today_str)
        self.assertEqual(len(daily), 1)
        self.assertEqual(daily[0]["date"], self.today_str)
        self.assertEqual(daily[0]["revenue"], 30.0)
        self.assertEqual(daily[0]["profit"], 20.0)

        # Invalid date range validation
        with self.assertRaises(ValidationError):
            self.app.analytics_service.get_daily_sales_series("invalid-date", self.today_str)


if __name__ == "__main__":
    unittest.main()
