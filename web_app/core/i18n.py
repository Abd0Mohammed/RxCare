"""Centralized Arabic / English localization dictionary and domain translators."""

from __future__ import annotations

import re

DEFAULT_LANG = "ar"
SUPPORTED_LANGS = ("ar", "en")

NAV_PAGE_KEYS = (
    "dashboard",
    "medicines",
    "pos",
    "inventory",
    "suppliers",
    "alerts",
    "reports",
)

TRANSLATIONS: dict[str, dict[str, str]] = {
    "ar": {
        # App shell & sidebar
        "app_subtitle": "نظام إدارة الصيدلية — نسخة الويب",
        "version_label": "الإصدار {version}",
        "language_label": "اللغة / Language",
        "lang_ar": "العربية",
        "lang_en": "English",
        "nav_label": "التنقل الرئيسي",
        "nav_dashboard": "لوحة التحكم",
        "nav_medicines": "إدارة الأدوية",
        "nav_pos": "نقطة البيع",
        "nav_inventory": "إدارة المخزون",
        "nav_suppliers": "الموردون",
        "nav_alerts": "تنبيهات الصلاحية ({count})",
        "nav_reports": "التقارير والتحليلات",
        "sidebar_skus": "الأصناف النشطة",
        "sidebar_today_rev": "مبيعات اليوم",
        "sidebar_db": "قاعدة البيانات",
        "sidebar_cloud_note": "ملاحظة: تخزين SQLite المحلي على الاستضافة السحابية مؤقت وقد يُعاد ضبطه عند إعادة النشر.",
        "err_startup": "تعذر تهيئة قاعدة بيانات الويب لـ RxCare. يرجى التحقق من أذونات التخزين والإعدادات.",
        "err_unexpected": "حدث خطأ غير متوقع أثناء معالجة الطلب. يرجى التحقق من المدخلات والمحاولة مجدداً.",
        # Common labels & statuses
        "status_expired": "منتهي الصلاحية (محظور)",
        "status_out_of_stock": "نفد المخزون",
        "status_expiring_soon": "قريب الانتهاء",
        "status_low_stock": "مخزون منخفض",
        "status_in_stock": "متوفر",
        "all_categories": "جميع التصنيفات",
        "unassigned": "(غير محدد)",
        "walk_in_customer": "عميل نقدي عابر",
        "not_available": "غير متاح",
        # Payment methods & reasons
        "pay_cash": "نقداً",
        "pay_card": "بطاقة",
        "pay_digital": "تأمين / دفع رقمي",
        "reason_restock": "إعادة توريد",
        "reason_return": "مرتجع للمورد",
        "reason_damage": "تلف / انتهاء",
        "reason_audit": "تصحيح جرد",
        # Dashboard page
        "dash_title": "لوحة التحكم",
        "dash_subtitle": "نظرة تنفيذية فورية على المخزون وسلامة الصلاحية والمبيعات وصافي الأرباح.",
        "kpi_total_medicines": "إجمالي الأدوية",
        "kpi_total_units_sub": "{units} وحدة متوفرة في المخزون",
        "kpi_low_stock": "أصناف منخفضة المخزون",
        "kpi_low_stock_sub": "عند حد إعادة الطلب أو دونه",
        "kpi_expired": "أدوية منتهية الصلاحية",
        "kpi_expired_sub": "محظورة تلقائياً من البيع",
        "kpi_expiring_soon": "قريبة الانتهاء (30 يوماً)",
        "kpi_expiring_soon_sub": "تتطلب تدوير المخزون",
        "kpi_today_sales": "مبيعات اليوم",
        "kpi_today_invoices_sub": "{count} فاتورة اليوم",
        "kpi_total_profit": "إجمالي صافي الربح",
        "kpi_today_profit_sub": "ربح اليوم: {amount}",
        "kpi_retail_value": "القيمة البيعية للمخزون",
        "kpi_cost_basis_sub": "بسعر التكلفة: {amount}",
        "kpi_suppliers": "الموردون النشطون",
        "kpi_all_time_rev_sub": "إجمالي الإيرادات: {amount}",
        "dash_urgent_alerts": "تنبيهات المخزون والصلاحية العاجلة",
        "dash_alerts_healthy": "جميع تشغيلات المخزون سليمة وبكميات كافية.",
        "dash_recent_sales": "أحدث فواتير المبيعات",
        "dash_no_sales": "لا توجد مبيعات مسجلة حتى الآن.",
        # Table columns
        "col_id": "المعرف",
        "col_medicine": "الدواء",
        "col_generic": "الاسم العلمي",
        "col_category": "التصنيف",
        "col_batch": "رقم التشغيلة",
        "col_supplier": "المورد",
        "col_cost": "سعر التكلفة",
        "col_price": "سعر البيع",
        "col_unit_price": "سعر الوحدة",
        "col_qty": "الكمية",
        "col_reorder": "حد الطلب",
        "col_expiry": "تاريخ الانتهاء",
        "col_status": "الحالة",
        "col_availability": "التوفر",
        "col_invoice": "رقم الفاتورة",
        "col_customer": "العميل",
        "col_payment": "الدفع",
        "col_total": "الإجمالي",
        "col_timestamp": "الوقت والتاريخ",
        "col_line_total": "إجمالي السطر",
        "col_cost_val": "قيمة التكلفة",
        "col_retail_val": "القيمة البيعية",
        "col_log_id": "رقم السجل",
        "col_change": "التغيير",
        "col_reason": "السبب",
        "col_note": "مرجع / ملاحظة",
        "col_contact": "جهة الاتصال",
        "col_phone": "الهاتف",
        "col_email": "البريد الإلكتروني",
        "col_address": "العنوان",
        "col_linked_skus": "الأصناف المرتبطة",
        "col_remaining_qty": "الكمية المتبقية",
        "col_days_overdue": "أيام التأخير",
        "col_days_left": "الأيام المتبقية",
        "col_current_qty": "الكمية الحالية",
        "col_date": "التاريخ",
        "col_transactions": "عدد العمليات",
        "col_revenue": "الإيراد",
        "col_net_profit": "صافي الربح",
        "col_rank": "الترتيب",
        "col_units_sold": "الوحدات المباعة",
        "col_gross_revenue": "إجمالي الإيراد",
        "col_sku_count": "عدد الأصناف",
        "col_subtotal": "المجموع الفرعي",
        "col_discount": "الخصم",
        "col_tax": "الضريبة",
        "col_grand_total": "الإجمالي النهائي",
        # Medicine Management page
        "med_title": "إدارة الأدوية",
        "med_subtitle": "البحث في تشغيلات الأدوية، التصفية حسب التصنيف، استعراض التفاصيل، وإدارة الأصناف.",
        "med_tab_catalog": "دليل الأدوية والتفاصيل",
        "med_tab_add": "إضافة دواء جديد",
        "med_tab_edit": "تعديل أو حذف دواء",
        "med_search_label": "البحث في الأدوية",
        "med_search_ph": "الاسم التجاري، الاسم العلمي، رقم التشغيلة، أو المورد...",
        "med_filter_cat": "التصنيف",
        "med_filter_avail": "حالة التوفر",
        "avail_all": "الكل",
        "avail_sale": "متاح للبيع",
        "avail_low": "مخزون منخفض",
        "avail_soon": "قريب الانتهاء",
        "avail_expired": "منتهي الصلاحية",
        "med_details_heading": "تفاصيل التشغيلة المحددة",
        "med_inspect_label": "اختر تشغيلة للمعاينة",
        "med_unit_margin": "هامش ربح الوحدة",
        "med_stock_reorder": "المخزون / حد الطلب",
        "med_empty_filter": "لا توجد أدوية مطابقة لمعايير البحث أو التصنيف الحالية.",
        "med_add_heading": "تسجيل تشغيلة دواء جديدة",
        "med_field_name": "اسم الدواء *",
        "med_field_generic": "الاسم العلمي",
        "med_field_category": "التصنيف",
        "med_field_batch": "رقم التشغيلة *",
        "med_field_supplier": "المورد",
        "med_field_cost": "سعر التكلفة ($)",
        "med_field_price": "سعر البيع للوحدة ($) *",
        "med_field_qty": "الكمية الابتدائية *",
        "med_field_reorder": "حد التنبيه لإعادة الطلب",
        "med_field_expiry": "تاريخ الانتهاء (YYYY-MM-DD) *",
        "med_field_desc": "الوصف / ملاحظات التخزين",
        "med_btn_add": "إضافة تشغيلة الدواء",
        "med_flash_added": "تمت إضافة '{name}' (تشغيلة {batch}) إلى المخزون.",
        "med_none_edit": "لا توجد أدوية متاحة للتعديل أو الحذف.",
        "med_select_modify": "اختر تشغيلة الدواء للتعديل",
        "med_editing_heading": "تعديل: {name} ({batch})",
        "med_btn_save": "حفظ التعديلات",
        "med_flash_updated": "تم تحديث '{name}' (تشغيلة {batch}).",
        "med_danger_zone": "منطقة الخطر — حذف تشغيلة الدواء",
        "med_delete_warn": "الحذف يزيل التشغيلة نهائياً. لا يمكن حذف التشغيلات المرتبطة بفواتير مبيعات سابقة.",
        "med_confirm_delete": "أؤكد حذف '{name}' (تشغيلة {batch})",
        "med_btn_delete": "حذف تشغيلة الدواء",
        "med_flash_deleted": "تم حذف '{name}'.",
        # POS page
        "pos_title": "نقطة البيع (POS)",
        "pos_subtitle": "ابحث عن الأدوية، أدر سلة المشتريات، عاين الربح والضريبة، وأتمم البيع بمعاملة ذرية آمنة.",
        "pos_catalog_heading": "1. كتالوج الأدوية",
        "pos_search_label": "بحث عن دواء أو تشغيلة",
        "pos_search_ph": "اكتب اسم الدواء، الاسم العلمي، أو رقم التشغيلة...",
        "pos_select_batch": "اختر تشغيلة الدواء",
        "pos_qty_label": "الكمية",
        "pos_btn_add_cart": "إضافة إلى السلة",
        "pos_flash_added": "تمت إضافة {name} إلى السلة (الكمية بالسلة: {qty}).",
        "pos_empty_catalog": "لا توجد أدوية مطابقة لبحثك.",
        "pos_cart_heading": "2. سلة البيع وإتمام الفاتورة",
        "pos_empty_cart": "السلة فارغة. أضف أدوية صالحة غير منتهية الصلاحية من الكتالوج.",
        "pos_edit_line": "تعديل صنف بالسلة",
        "pos_new_qty": "كمية جديدة",
        "pos_btn_update": "تحديث",
        "pos_btn_remove": "إزالة",
        "pos_btn_clear": "إفراغ السلة بالكامل",
        "pos_customer_name": "اسم العميل",
        "pos_customer_phone": "هاتف العميل",
        "pos_discount_pct": "نسبة الخصم (%)",
        "pos_tax_pct": "نسبة الضريبة (%)",
        "pos_payment_method": "طريقة الدفع",
        "pos_amount_paid": "المبلغ المدفوع (اتركه فارغاً للمطابقة)",
        "pos_notes": "ملاحظات الفاتورة (اختياري)",
        "pos_est_caption": "التكلفة التقديرية: {cost} | صافي الربح التقديري: {profit}",
        "pos_btn_checkout": "إتمام البيع وإصدار الفاتورة",
        "pos_flash_sale": "تمت عملية البيع بنجاح! فاتورة {invoice} — الإجمالي {total}",
        "pos_checkout_failed": "فشل إتمام البيع: {err}",
        "pos_latest_invoice": "ملخص أحدث فاتورة — {invoice}",
        "pos_change_due": "الباقي للعميل",
        # Inventory page
        "inv_title": "إدارة المخزون",
        "inv_subtitle": "مراقبة الأرصدة الفورية، معالجة تنبيهات النقص، وتسجيل حركات التعديل الموثقة.",
        "inv_kpi_skus": "إجمالي الأصناف",
        "inv_kpi_units": "إجمالي الوحدات",
        "inv_kpi_low": "تنبيهات انخفاض المخزون",
        "inv_kpi_cost": "قيمة المخزون بالتكلفة",
        "inv_tab_levels": "مستويات المخزون والتصفية",
        "inv_tab_adjust": "توريد / تعديل المخزون",
        "inv_tab_audit": "سجل تدقيق المخزون",
        "inv_search_label": "بحث في المخزون",
        "inv_search_ph": "الدواء، رقم التشغيلة، أو المورد...",
        "inv_filter_label": "تصفية المخزون",
        "inv_filter_all": "كل المخزون",
        "inv_filter_low": "منخفض المخزون فقط",
        "inv_filter_sale": "متاح للبيع",
        "inv_filter_soon": "قريب الانتهاء",
        "inv_filter_exp": "منتهي الصلاحية",
        "inv_download_csv": "تنزيل المخزون (CSV)",
        "inv_empty_filter": "لا توجد تشغيلات مطابقة للتصفية المحددة.",
        "inv_empty_adjust": "لا توجد أدوية في المخزون لتعديلها.",
        "inv_adjust_heading": "تسجيل تعديل مخزوني",
        "inv_target_batch": "تشغيلة الدواء المستهدفة",
        "inv_qty_delta": "تغيير الكمية (+ زيادة / - خصم)",
        "inv_reason_label": "سبب التعديل",
        "inv_ref_note": "ملاحظة مرجعية (رقم أمر شراء أو جرد)",
        "inv_btn_apply": "تطبيق التعديل المخزوني",
        "inv_flash_adjusted": "تم تحديث رصيد '{name}' إلى {qty} وحدة.",
        "inv_audit_empty": "لم تُسجل أي تعديلات مخزونية بعد.",
        # Suppliers page
        "sup_title": "إدارة الموردين",
        "sup_subtitle": "إدارة موردي الأدوية وبيانات التواصل وعدد الأصناف المرتبطة بكل مورد.",
        "sup_tab_list": "دليل الموردين",
        "sup_tab_add": "إضافة مورد جديد",
        "sup_tab_edit": "تعديل أو حذف مورد",
        "sup_search_label": "البحث في الموردين",
        "sup_search_ph": "الاسم، جهة الاتصال، الهاتف، أو البريد الإلكتروني...",
        "sup_empty_search": "لا يوجد موردون مطابقون لبحثك.",
        "sup_add_heading": "إضافة مورد جديد",
        "sup_field_name": "اسم المورد *",
        "sup_field_contact": "الشخص المسؤول",
        "sup_field_phone": "رقم الهاتف",
        "sup_field_email": "البريد الإلكتروني",
        "sup_field_address": "العنوان",
        "sup_btn_create": "إضافة المورد",
        "sup_flash_added": "تمت إضافة المورد '{name}'.",
        "sup_none_edit": "لا يوجد موردون متاحون للتعديل.",
        "sup_select_edit": "اختر المورد",
        "sup_editing_heading": "تعديل المورد: {name}",
        "sup_btn_update": "تحديث بيانات المورد",
        "sup_flash_updated": "تم تحديث بيانات المورد '{name}'.",
        "sup_danger_zone": "منطقة الخطر — حذف المورد",
        "sup_delete_warn": "لا يمكن حذف المورد المرتبط بتشغيلات أدوية حالية حتى يتم نقلها أو حذفها.",
        "sup_confirm_delete": "أؤكد حذف المورد '{name}'",
        "sup_btn_delete": "حذف المورد",
        "sup_flash_deleted": "تم حذف المورد '{name}'.",
        # Alerts page
        "al_title": "تنبيهات الصلاحية والمخزون",
        "al_subtitle": "عزل التشغيلات المنتهية (محظورة من نقطة البيع)، متابعة قريبة الانتهاء، وتوريد النقص.",
        "al_window_label": "نافذة التنبيه لقرب الانتهاء (بالأيام)",
        "al_kpi_expired": "منتهية الصلاحية (محظورة)",
        "al_kpi_expired_sub": "يُمنع إضافتها أو بيعها في POS",
        "al_kpi_soon": "تنتهي خلال {days} يوماً",
        "al_kpi_soon_sub": "أولوية الصرف للأقرب انتهاءً (FEFO)",
        "al_kpi_low": "أصناف منخفضة المخزون",
        "al_kpi_low_sub": "عند حد إعادة الطلب أو دونه",
        "al_tab_exp": "منتهية الصلاحية ({count})",
        "al_tab_soon": "قريبة الانتهاء ({count})",
        "al_tab_low": "مخزون منخفض ({count})",
        "al_safety_banner": "سياسة السلامة الدوائية مفعلة: الأدوية منتهية الصلاحية محظورة تماماً من البيع.",
        "al_writeoff_heading": "شطب الرصيد المنتهي الصلاحية",
        "al_writeoff_select": "اختر التشغيلة المنتهية للشطب",
        "al_writeoff_confirm": "أؤكد شطب {qty} وحدة من '{name}' لتصبح 0",
        "al_btn_writeoff": "شطب الرصيد المنتهي",
        "al_flash_writeoff": "تم شطب الرصيد المنتهي لـ '{name}' (تشغيلة {batch}).",
        "al_none_expired": "لا توجد تشغيلات منتهية الصلاحية في المخزون.",
        "al_none_soon": "لا توجد تشغيلات تنتهي خلال الـ {days} يوماً القادمة.",
        "al_none_low": "لا توجد أدوية دون حد إعادة الطلب حالياً.",
        "al_quick_restock": "إعادة توريد سريعة",
        "al_add_qty": "الكمية المضافة",
        "al_po_ref": "مرجع أمر التوريد",
        "al_po_default": "تعزيز مخزون منخفض",
        "al_btn_restock": "توريد التشغيلة",
        "al_flash_restocked": "تم توريد '{name}' ليصبح الرصيد {qty} وحدة.",
        # Reports page
        "rep_title": "التقارير والتحليلات المالية",
        "rep_subtitle": "تحليل المبيعات اليومية، الإيرادات، صافي الأرباح، الأكثر مبيعاً، وتقييم المخزون.",
        "rep_start_date": "من تاريخ",
        "rep_end_date": "إلى تاريخ",
        "rep_btn_apply": "تطبيق فلتر التاريخ",
        "rep_warn_dates": "يرجى تحديد تاريخ البداية وتاريخ النهاية.",
        "rep_err_range": "تاريخ البداية لا يمكن أن يكون بعد تاريخ النهاية.",
        "rep_kpi_tx": "عدد الفواتير",
        "rep_kpi_rev": "إجمالي الإيرادات",
        "rep_kpi_tax_sub": "الضرائب: {amount}",
        "rep_kpi_profit": "إجمالي صافي الربح",
        "rep_kpi_cogs_sub": "التكلفة: {amount}",
        "rep_kpi_disc": "إجمالي الخصومات",
        "rep_kpi_inv": "قيمة المخزون البيعية",
        "rep_kpi_inv_cost_sub": "بالتكلفة: {amount}",
        "rep_tab_daily": "المبيعات والأرباح اليومية",
        "rep_tab_best": "الأدوية الأكثر مبيعاً",
        "rep_tab_val": "تقييم المخزون حسب التصنيف",
        "rep_tab_invoices": "سجل الفواتير والتصدير",
        "rep_empty_daily": "لا توجد عمليات بيع ضمن الفترة الزمنية المحددة.",
        "rep_empty_best": "لا توجد مبيعات أصناف ضمن الفترة المحددة.",
        "rep_empty_inv": "لا توجد سجلات مخزون.",
        "rep_empty_invoices": "لا توجد فواتير ضمن الفترة الزمنية المحددة.",
        "rep_download_csv": "تنزيل تقرير المبيعات (CSV)",
        # Charts
        "chart_daily_title": "الإيرادات اليومية مقابل صافي الربح",
        "chart_daily_empty": "لا توجد بيانات مبيعات في الفترة المحددة.",
        "chart_amount_axis": "المبلغ ($)",
        "chart_legend_rev": "الإيراد ($)",
        "chart_legend_profit": "صافي الربح ($)",
        "chart_top_title": "أعلى الأدوية مبيعاً (الإيراد)",
        "chart_top_empty": "لا توجد مبيعات أصناف في الفترة المحددة.",
        "chart_rev_axis": "الإيراد ($)",
        "chart_cat_title": "القيمة البيعية للمخزون حسب التصنيف",
        "chart_cat_empty": "لا توجد تصنيفات مخزون متاحة.",
        "chart_val_axis": "القيمة البيعية ($)",
    },
    "en": {
        # App shell & sidebar
        "app_subtitle": "Pharmacy Management Web Edition",
        "version_label": "v{version}",
        "language_label": "Language / اللغة",
        "lang_ar": "العربية",
        "lang_en": "English",
        "nav_label": "Navigation",
        "nav_dashboard": "Dashboard",
        "nav_medicines": "Medicines",
        "nav_pos": "Point of Sale",
        "nav_inventory": "Inventory",
        "nav_suppliers": "Suppliers",
        "nav_alerts": "Expiry Alerts ({count})",
        "nav_reports": "Reports",
        "sidebar_skus": "Active SKUs",
        "sidebar_today_rev": "Today's Revenue",
        "sidebar_db": "Web DB",
        "sidebar_cloud_note": "Note: Local SQLite storage on ephemeral cloud containers resets on redeploy.",
        "err_startup": "Unable to initialize the RxCare Web database. Please verify storage permissions and configuration.",
        "err_unexpected": "An unexpected error occurred while processing your request. Please check your inputs and try again.",
        # Common labels & statuses
        "status_expired": "EXPIRED (Blocked)",
        "status_out_of_stock": "Out of Stock",
        "status_expiring_soon": "Expiring Soon",
        "status_low_stock": "Low Stock",
        "status_in_stock": "In Stock",
        "all_categories": "All Categories",
        "unassigned": "(Unassigned)",
        "walk_in_customer": "Walk-in Customer",
        "not_available": "N/A",
        # Payment methods & reasons
        "pay_cash": "Cash",
        "pay_card": "Card",
        "pay_digital": "Insurance / Digital",
        "reason_restock": "Restock",
        "reason_return": "Supplier Return",
        "reason_damage": "Damage / Spoilage",
        "reason_audit": "Audit Correction",
        # Dashboard page
        "dash_title": "Pharmacy Dashboard",
        "dash_subtitle": "Real-time operational overview across catalog inventory, expiry safety, sales, and net profit.",
        "kpi_total_medicines": "Total Medicines",
        "kpi_total_units_sub": "{units} total units in stock",
        "kpi_low_stock": "Low-Stock Items",
        "kpi_low_stock_sub": "At or below reorder threshold",
        "kpi_expired": "Expired Medicines",
        "kpi_expired_sub": "Automatically blocked from POS",
        "kpi_expiring_soon": "Expiring Soon (30d)",
        "kpi_expiring_soon_sub": "Requires stock rotation",
        "kpi_today_sales": "Today's Sales",
        "kpi_today_invoices_sub": "{count} invoice(s) today",
        "kpi_total_profit": "Total Profit (Net)",
        "kpi_today_profit_sub": "Today: {amount}",
        "kpi_retail_value": "Inventory Retail Value",
        "kpi_cost_basis_sub": "Cost basis: {amount}",
        "kpi_suppliers": "Active Suppliers",
        "kpi_all_time_rev_sub": "All-time revenue: {amount}",
        "dash_urgent_alerts": "Urgent Stock & Expiry Alerts",
        "dash_alerts_healthy": "All inventory batches are healthy and sufficiently stocked.",
        "dash_recent_sales": "Recent Sales Invoices",
        "dash_no_sales": "No sales recorded yet.",
        # Table columns
        "col_id": "ID",
        "col_medicine": "Medicine",
        "col_generic": "Generic Name",
        "col_category": "Category",
        "col_batch": "Batch #",
        "col_supplier": "Supplier",
        "col_cost": "Cost",
        "col_price": "Price",
        "col_unit_price": "Unit Price",
        "col_qty": "Qty",
        "col_reorder": "Reorder Level",
        "col_expiry": "Expiry",
        "col_status": "Status",
        "col_availability": "Availability",
        "col_invoice": "Invoice #",
        "col_customer": "Customer",
        "col_payment": "Payment",
        "col_total": "Total",
        "col_timestamp": "Timestamp",
        "col_line_total": "Line Total",
        "col_cost_val": "Cost Value",
        "col_retail_val": "Retail Value",
        "col_log_id": "Log ID",
        "col_change": "Change",
        "col_reason": "Reason",
        "col_note": "Reference Note",
        "col_contact": "Contact Person",
        "col_phone": "Phone",
        "col_email": "Email",
        "col_address": "Address",
        "col_linked_skus": "Linked SKUs",
        "col_remaining_qty": "Remaining Qty",
        "col_days_overdue": "Days Overdue",
        "col_days_left": "Days Left",
        "col_current_qty": "Current Qty",
        "col_date": "Date",
        "col_transactions": "Transactions",
        "col_revenue": "Revenue",
        "col_net_profit": "Net Profit",
        "col_rank": "Rank",
        "col_units_sold": "Units Sold",
        "col_gross_revenue": "Gross Revenue",
        "col_sku_count": "SKU Count",
        "col_subtotal": "Subtotal",
        "col_discount": "Discount",
        "col_tax": "Tax",
        "col_grand_total": "Grand Total",
        # Medicine Management page
        "med_title": "Medicine Management",
        "med_subtitle": "Search catalog batches, filter by therapeutic category, inspect details, and manage SKUs.",
        "med_tab_catalog": "Catalog & Details",
        "med_tab_add": "Add Medicine",
        "med_tab_edit": "Edit / Delete Medicine",
        "med_search_label": "Search Medicines",
        "med_search_ph": "Name, generic name, batch #, or supplier...",
        "med_filter_cat": "Category",
        "med_filter_avail": "Availability",
        "avail_all": "All",
        "avail_sale": "Available for Sale",
        "avail_low": "Low Stock",
        "avail_soon": "Expiring Soon",
        "avail_expired": "Expired",
        "med_details_heading": "Medicine Batch Details",
        "med_inspect_label": "Inspect Batch",
        "med_unit_margin": "Unit Margin",
        "med_stock_reorder": "Stock / Reorder",
        "med_empty_filter": "No medicines match the current search or category filters.",
        "med_add_heading": "Register New Medicine Batch",
        "med_field_name": "Medicine Name *",
        "med_field_generic": "Generic Name",
        "med_field_category": "Category",
        "med_field_batch": "Batch Number *",
        "med_field_supplier": "Supplier",
        "med_field_cost": "Cost Price ($)",
        "med_field_price": "Unit Selling Price ($) *",
        "med_field_qty": "Initial Stock Quantity *",
        "med_field_reorder": "Reorder Alert Level",
        "med_field_expiry": "Expiry Date (YYYY-MM-DD) *",
        "med_field_desc": "Description / Storage Notes",
        "med_btn_add": "Add Medicine Batch",
        "med_flash_added": "Added '{name}' (Batch {batch}) to inventory.",
        "med_none_edit": "No medicines available to edit or delete.",
        "med_select_modify": "Select Medicine Batch to Modify",
        "med_editing_heading": "Editing {name} ({batch})",
        "med_btn_save": "Save Changes",
        "med_flash_updated": "Updated '{name}' (Batch {batch}).",
        "med_danger_zone": "Danger Zone — Delete Medicine Batch",
        "med_delete_warn": "Deleting removes the batch permanently. Batches with historical sales cannot be deleted.",
        "med_confirm_delete": "I confirm deleting '{name}' (Batch {batch})",
        "med_btn_delete": "Delete Medicine Batch",
        "med_flash_deleted": "Deleted '{name}'.",
        # POS page
        "pos_title": "Point of Sale (POS)",
        "pos_subtitle": "Search medicines, manage cart quantities, preview profit & taxes, and complete atomic sales.",
        "pos_catalog_heading": "1. Medicine Catalog",
        "pos_search_label": "Search Medicine or Batch",
        "pos_search_ph": "Type medicine name, generic name, or batch #...",
        "pos_select_batch": "Select Medicine Batch",
        "pos_qty_label": "Quantity",
        "pos_btn_add_cart": "Add to Cart",
        "pos_flash_added": "Added {name} to cart (Cart Qty: {qty}).",
        "pos_empty_catalog": "No medicines found matching your query.",
        "pos_cart_heading": "2. Shopping Cart & Checkout",
        "pos_empty_cart": "Your cart is empty. Add valid non-expired medicines from the catalog.",
        "pos_edit_line": "Edit Cart Line",
        "pos_new_qty": "New Qty",
        "pos_btn_update": "Update",
        "pos_btn_remove": "Remove",
        "pos_btn_clear": "Clear Entire Cart",
        "pos_customer_name": "Customer Name",
        "pos_customer_phone": "Customer Phone",
        "pos_discount_pct": "Discount (%)",
        "pos_tax_pct": "Tax (%)",
        "pos_payment_method": "Payment Method",
        "pos_amount_paid": "Amount Tendered (blank = exact total)",
        "pos_notes": "Invoice Notes (optional)",
        "pos_est_caption": "Estimated Cost: {cost} | Estimated Net Profit: {profit}",
        "pos_btn_checkout": "Complete Sale & Generate Invoice",
        "pos_flash_sale": "Sale completed! Invoice {invoice} — Total {total}",
        "pos_checkout_failed": "Checkout failed: {err}",
        "pos_latest_invoice": "Latest Invoice Summary — {invoice}",
        "pos_change_due": "Change Due",
        # Inventory page
        "inv_title": "Inventory Management",
        "inv_subtitle": "Monitor live batch quantities, address low-stock alerts, and log audited stock adjustments.",
        "inv_kpi_skus": "Total SKUs",
        "inv_kpi_units": "Total Stock Units",
        "inv_kpi_low": "Low Stock Alerts",
        "inv_kpi_cost": "Inventory Cost Value",
        "inv_tab_levels": "Stock Levels & Filters",
        "inv_tab_adjust": "Restock / Adjust Stock",
        "inv_tab_audit": "Stock Audit Log",
        "inv_search_label": "Search Inventory",
        "inv_search_ph": "Medicine, batch #, or supplier...",
        "inv_filter_label": "Filter Inventory",
        "inv_filter_all": "All Stock",
        "inv_filter_low": "Low Stock Only",
        "inv_filter_sale": "Available for Sale",
        "inv_filter_soon": "Expiring Soon",
        "inv_filter_exp": "Expired",
        "inv_download_csv": "Download Inventory CSV",
        "inv_empty_filter": "No inventory batches match the selected filter.",
        "inv_empty_adjust": "No medicines in inventory to adjust.",
        "inv_adjust_heading": "Record Stock Adjustment",
        "inv_target_batch": "Target Medicine Batch",
        "inv_qty_delta": "Quantity Change (+ restock / - deduction)",
        "inv_reason_label": "Adjustment Reason",
        "inv_ref_note": "Reference Note (PO #, invoice, or audit ref)",
        "inv_btn_apply": "Apply Stock Adjustment",
        "inv_flash_adjusted": "Updated '{name}' stock to {qty} units.",
        "inv_audit_empty": "No stock adjustments recorded yet.",
        # Suppliers page
        "sup_title": "Suppliers",
        "sup_subtitle": "Manage wholesale pharmaceutical vendors, contact details, and linked SKU counts.",
        "sup_tab_list": "Supplier Directory",
        "sup_tab_add": "Add Supplier",
        "sup_tab_edit": "Edit / Delete Supplier",
        "sup_search_label": "Search Suppliers",
        "sup_search_ph": "Name, contact person, phone, or email...",
        "sup_empty_search": "No suppliers match your search.",
        "sup_add_heading": "Add New Supplier",
        "sup_field_name": "Supplier Name *",
        "sup_field_contact": "Contact Person",
        "sup_field_phone": "Phone Number",
        "sup_field_email": "Email Address",
        "sup_field_address": "Street Address",
        "sup_btn_create": "Create Supplier",
        "sup_flash_added": "Supplier '{name}' added.",
        "sup_none_edit": "No suppliers available to edit.",
        "sup_select_edit": "Select Supplier",
        "sup_editing_heading": "Editing {name}",
        "sup_btn_update": "Update Supplier",
        "sup_flash_updated": "Updated supplier '{name}'.",
        "sup_danger_zone": "Danger Zone — Delete Supplier",
        "sup_delete_warn": "Suppliers linked to existing medicine batches cannot be deleted until medicines are reassigned or removed.",
        "sup_confirm_delete": "I confirm deleting supplier '{name}'",
        "sup_btn_delete": "Delete Supplier",
        "sup_flash_deleted": "Deleted supplier '{name}'.",
        # Alerts page
        "al_title": "Expiry & Stock Alerts",
        "al_subtitle": "Quarantine expired stock (blocked from POS checkout), rotate near-expiry batches, and restock low inventory.",
        "al_window_label": "Expiry Warning Window (Days)",
        "al_kpi_expired": "Expired (POS Blocked)",
        "al_kpi_expired_sub": "Cannot be added to or sold via POS",
        "al_kpi_soon": "Expiring Within {days} Days",
        "al_kpi_soon_sub": "Prioritize FEFO dispensing",
        "al_kpi_low": "Low Stock Items",
        "al_kpi_low_sub": "At or below reorder level",
        "al_tab_exp": "Expired ({count})",
        "al_tab_soon": "Expiring Soon ({count})",
        "al_tab_low": "Low Stock ({count})",
        "al_safety_banner": "Safety Policy Active: Expired medicines are strictly blocked from sale in POS.",
        "al_writeoff_heading": "Write Off Expired Stock",
        "al_writeoff_select": "Select Expired Batch to Write Off",
        "al_writeoff_confirm": "Confirm writing off {qty} unit(s) of '{name}' to 0",
        "al_btn_writeoff": "Write Off Expired Stock",
        "al_flash_writeoff": "Wrote off expired stock for '{name}' (Batch {batch}).",
        "al_none_expired": "No expired medicine batches in inventory.",
        "al_none_soon": "No batches expiring within the next {days} days.",
        "al_none_low": "No medicines are currently below their reorder threshold.",
        "al_quick_restock": "Quick Restock",
        "al_add_qty": "Add Quantity",
        "al_po_ref": "PO / Restock Reference",
        "al_po_default": "Low-stock replenishment",
        "al_btn_restock": "Restock Batch",
        "al_flash_restocked": "Restocked '{name}' to {qty} units.",
        # Reports page
        "rep_title": "Reports & Financial Analytics",
        "rep_subtitle": "Analyze daily sales, revenue, net profit, best-selling medicines, and category inventory value.",
        "rep_start_date": "Start Date",
        "rep_end_date": "End Date",
        "rep_btn_apply": "Apply Date Filter",
        "rep_warn_dates": "Please select both a Start Date and an End Date.",
        "rep_err_range": "Start Date cannot be later than End Date.",
        "rep_kpi_tx": "Transactions",
        "rep_kpi_rev": "Total Revenue",
        "rep_kpi_tax_sub": "Tax: {amount}",
        "rep_kpi_profit": "Total Profit (Net)",
        "rep_kpi_cogs_sub": "COGS: {amount}",
        "rep_kpi_disc": "Discounts Given",
        "rep_kpi_inv": "Inventory Value",
        "rep_kpi_inv_cost_sub": "Cost: {amount}",
        "rep_tab_daily": "Daily Sales & Profit",
        "rep_tab_best": "Best-Selling Medicines",
        "rep_tab_val": "Inventory Valuation",
        "rep_tab_invoices": "Invoice History",
        "rep_empty_daily": "No sales transactions found in the selected date range.",
        "rep_empty_best": "No item sales found in the selected date range.",
        "rep_empty_inv": "No inventory records found.",
        "rep_empty_invoices": "No invoices found for the selected date range.",
        "rep_download_csv": "Download Sales CSV",
        # Charts
        "chart_daily_title": "Daily Revenue vs Net Profit",
        "chart_daily_empty": "No sales data in selected range.",
        "chart_amount_axis": "Amount ($)",
        "chart_legend_rev": "Revenue ($)",
        "chart_legend_profit": "Net Profit ($)",
        "chart_top_title": "Top-Selling Medicines (Revenue)",
        "chart_top_empty": "No item sales in selected range.",
        "chart_rev_axis": "Revenue ($)",
        "chart_cat_title": "Inventory Retail Value by Category",
        "chart_cat_empty": "No inventory categories available.",
        "chart_val_axis": "Retail Value ($)",
    },
}

CATEGORY_AR_MAP: dict[str, str] = {
    "Analgesics": "المسكنات",
    "Antibiotics": "المضادات الحيوية",
    "Antihistamines": "مضادات الحساسية",
    "Cardiovascular": "القلب والأوعية الدموية",
    "Dermatology": "الأمراض الجلدية",
    "Endocrinology": "الغدد الصماء والسكري",
    "Gastrointestinal": "الجهاز الهضمي",
    "Respiratory": "الجهاز التنفسي",
    "Vitamins & Supplements": "الفيتامينات والمكملات",
    "General": "عام",
}

PAYMENT_KEYS = (
    ("Cash", "pay_cash"),
    ("Card", "pay_card"),
    ("Insurance / Digital", "pay_digital"),
)

REASON_KEYS = (
    ("Restock", "reason_restock"),
    ("Supplier Return", "reason_return"),
    ("Damage / Spoilage", "reason_damage"),
    ("Audit Correction", "reason_audit"),
)


def t(key: str, lang: str = DEFAULT_LANG, **kwargs: object) -> str:
    """Translate a key into the selected language with optional formatting."""
    lang_code = lang if lang in TRANSLATIONS else DEFAULT_LANG
    template = TRANSLATIONS[lang_code].get(key) or TRANSLATIONS["en"].get(key) or key
    return template.format(**kwargs) if kwargs else template


def translate_category(category: str, lang: str) -> str:
    """Return localized category display text while keeping canonical DB value."""
    if lang == "ar":
        return CATEGORY_AR_MAP.get(category, category)
    return category


def translate_payment_method(method: str, lang: str) -> str:
    """Return localized display label for a canonical payment method."""
    for canonical, key in PAYMENT_KEYS:
        if method == canonical:
            return t(key, lang)
    return method


def translate_reason(reason: str, lang: str) -> str:
    """Return localized display label for a stock adjustment reason."""
    for canonical, key in REASON_KEYS:
        if reason == canonical:
            return t(key, lang)
    return reason


_FIELD_AR_MAP = {
    "Medicine name": "اسم الدواء",
    "Batch number": "رقم التشغيلة",
    "Supplier name": "اسم المورد",
    "Unit price": "سعر البيع",
    "Cost price": "سعر التكلفة",
    "Quantity": "الكمية",
    "Reorder level": "حد إعادة الطلب",
    "Restock quantity": "كمية التوريد",
    "Expiry date": "تاريخ الانتهاء",
    "Start date": "تاريخ البداية",
    "End date": "تاريخ النهاية",
    "Discount %": "نسبة الخصم %",
    "Tax %": "نسبة الضريبة %",
    "Amount paid": "المبلغ المدفوع",
    "Adjustment reason": "سبب التعديل",
}


def localize_error(exc: Exception | str, lang: str) -> str:
    """Translate backend ValidationError / BusinessRuleError messages cleanly to Arabic."""
    raw = str(exc)
    if lang != "ar":
        return raw

    # Common validation templates
    if raw.endswith(" cannot be empty."):
        field = raw[: -len(" cannot be empty.")]
        return f"حقل «{_FIELD_AR_MAP.get(field, field)}» لا يمكن أن يكون فارغاً."
    if raw.endswith(" must be a whole number."):
        field = raw[: -len(" must be a whole number.")]
        return f"حقل «{_FIELD_AR_MAP.get(field, field)}» يجب أن يكون رقماً صحيحاً."
    if raw.endswith(" cannot be negative."):
        field = raw[: -len(" cannot be negative.")]
        return f"حقل «{_FIELD_AR_MAP.get(field, field)}» لا يمكن أن يكون سالباً."
    if raw.endswith(" must be greater than zero."):
        field = raw[: -len(" must be greater than zero.")]
        return f"حقل «{_FIELD_AR_MAP.get(field, field)}» يجب أن يكون أكبر من صفر."
    if raw.endswith(" must be a valid number."):
        field = raw[: -len(" must be a valid number.")]
        return f"حقل «{_FIELD_AR_MAP.get(field, field)}» يجب أن يكون رقماً صالحاً."
    if "YYYY-MM-DD" in raw:
        return "يجب إدخال التاريخ بصيغة صحيحة (YYYY-MM-DD)."
    if raw == "Email address format is invalid.":
        return "صيغة البريد الإلكتروني غير صحيحة."
    if raw == "Cannot complete checkout with an empty cart.":
        return "لا يمكن إتمام البيع وسلة المشتريات فارغة."
    if raw == "Discount percentage cannot exceed 100%.":
        return "نسبة الخصم لا يمكن أن تتجاوز 100%."
    if raw == "Tax percentage cannot exceed 100%.":
        return "نسبة الضريبة لا يمكن أن تتجاوز 100%."
    if raw == "Stock adjustment quantity cannot be zero.":
        return "كمية التعديل المخزوني لا يمكن أن تكون صفراً."

    m = re.match(r"^Sale blocked: '(.+)' \(Batch (.+)\) expired on (.+)\.$", raw)
    if m:
        return f"تم حظر البيع: الدواء '{m.group(1)}' (تشغيلة {m.group(2)}) منتهي الصلاحية بتاريخ {m.group(3)}."

    m = re.match(r"^'(.+)' \(Batch (.+)\) is out of stock\.$", raw)
    if m:
        return f"الدواء '{m.group(1)}' (تشغيلة {m.group(2)}) نفد من المخزون."

    m = re.match(r"^Insufficient stock for '(.+)': requested (\d+), available (\d+)\.$", raw)
    if m:
        return f"المخزون غير كافٍ للدواء '{m.group(1)}': المطلوب {m.group(2)}، المتوفر {m.group(3)}."

    m = re.match(r"^Amount paid \((.+)\) is less than grand total \((.+)\)\.$", raw)
    if m:
        return f"المبلغ المدفوع ({m.group(1)}) أقل من الإجمالي النهائي ({m.group(2)})."

    m = re.match(r"^Batch number '(.+)' already exists in inventory\.$", raw)
    if m:
        return f"رقم التشغيلة '{m.group(1)}' مسجل مسبقاً في المخزون."

    m = re.match(r"^Another medicine already uses batch number '(.+)'\.$", raw)
    if m:
        return f"يوجد دواء آخر يستخدم رقم التشغيلة '{m.group(1)}'."

    m = re.match(r"^A supplier named '(.+)' already exists\.$", raw)
    if m:
        return f"يوجد مورد مسجل مسبقاً باسم '{m.group(1)}'."

    m = re.match(r"^Cannot delete '(.+)' because (\d+) medicine record\(s\) are assigned to this supplier\.$", raw)
    if m:
        return f"لا يمكن حذف المورد '{m.group(1)}' لوجود {m.group(2)} صنف دوائي مرتبط به."

    m = re.match(r"^Cannot delete '(.+)' because it appears on (\d+) historical sale line\(s\)\.", raw)
    if m:
        return f"لا يمكن حذف '{m.group(1)}' لارتباطه بـ {m.group(2)} عملية بيع تاريخية. يمكنك تصفير المخزون بدلاً من ذلك."

    m = re.match(r"^Cannot reduce '(.+)' below 0 \(current stock: (\d+)\)\.$", raw)
    if m:
        return f"لا يمكن خفض مخزون '{m.group(1)}' إلى أقل من صفر (الرصيد الحالي: {m.group(2)})."

    return raw
