---
title: "الدليل التعليمي الشامل لمشروع RxCare — نظام إدارة الصيدلية"
subtitle: "شرح معماري وبرمجي متكامل للنسخة المكتبية (Tkinter) ونسخة الويب (Streamlit)"
lang: ar
dir: rtl
---

# RxCare — نظام إدارة الصيدلية
## الدليل التعليمي والمعماري الشامل لمناقشة مشروع التخرج

- **اسم المشروع:** RxCare Pharmacy Management System (Desktop & Bilingual Web Editions)
- **التقنيات الأساسية:** Python 3.11 · Streamlit · Tkinter / ttk · SQLite 3 · Matplotlib
- **تاريخ الإعداد:** 2026-11-27
- **الفئة المستهدفة:** طلاب نظم المعلومات الإدارية وهندسة البرمجيات (مستوى مبتدئ إلى متوسط)

> **ملاحظة حول تحويل هذا الملف إلى PDF:**  
> تعذّر توليد ملف `RxCare_Complete_Project_Guide.pdf` مباشرة داخل بيئة الخادم السحابية لعدم توفر محرك تحويل يدعم ربط الحروف العربية واتجاه RTL (`WeasyPrint` أو `XeLaTeX` أو `Chromium`). يمكنك تحويل هذا الملف أو ملف `docs/RxCare_Complete_Project_Guide.html` المرفق إلى PDF بسهولة تامة عبر التعليمات الموجودة في نهاية هذا الدليل.

---

## فهرس المحتويات

1. [الفصل الأول — مقدمة المشروع (Project Introduction)](#الفصل-الأول--مقدمة-المشروع)
2. [الفصل الثاني — حزمة التقنيات المستخدمة (Technology Stack)](#الفصل-الثاني--حزمة-التقنيات-المستخدمة)
3. [الفصل الثالث — معمارية المشروع (Project Architecture)](#الفصل-الثالث--معمارية-المشروع)
4. [الفصل الرابع — تصميم قاعدة البيانات (Database Design)](#الفصل-الرابع--تصميم-قاعدة-البيانات)
5. [الفصل الخامس — مفاهيم برمجة بايثون المستخدمة في الكود](#الفصل-الخامس--مفاهيم-برمجة-بايثون-المستخدمة)
6. [الفصل السادس — شرح وحدات التطبيق (Application Modules)](#الفصل-السادس--شرح-وحدات-التطبيق)
7. [الفصل السابع — جولة تفصيلية في أهم دوال الكود الحقيقي](#الفصل-السابع--جولة-تفصيلية-في-أهم-دوال-الكود)
8. [الفصل الثامن — آلية تشغيل التطبيق والنشر السحابي](#الفصل-الثامن--آلية-تشغيل-التطبيق-والنشر)
9. [الفصل التاسع — الاختبارات ومعالجة الأخطاء (Testing & Error Handling)](#الفصل-التاسع--الاختبارات-ومعالجة-الأخطاء)
10. [الفصل العاشر — الأمان والقيود الحالية (Security & Limitations)](#الفصل-العاشر--الأمان-والقيود)
11. [الفصل الحادي عشر — دليل التشغيل والصيانة (Run & Maintenance)](#الفصل-الحادي-عشر--دليل-التشغيل-والصيانة)
12. [الفصل الثاني عشر — التحسينات المستقبلية (Future Improvements)](#الفصل-الثاني-عشر--التحسينات-المستقبلية)
13. [الفصل الثالث عشر — بنك أسئلة المناقشة الجامعية (45 سؤالاً وإجابة)](#الفصل-الثالث-عشر--أسئلة-المناقشة-الجامعية)
14. [الفصل الرابع عشر — نص العرض العملي أمام لجنة المناقشة (Demo Script)](#الفصل-الرابع-عشر--نص-العرض-العملي)

---

## الفصل الأول — مقدمة المشروع

### 1.1 ما هو نظام RxCare؟
**RxCare** هو نظام متكامل لإدارة الصيدليات (Pharmacy Management System) صُمّم وبُرمج بلغة **Python 3** مع قاعدة بيانات علائقية **SQLite**. يضم المشروع نسختين تشغيليتين متكاملتين تتشاركان نفس منطق الأعمال (Business Logic):
1. **النسخة المكتبية (Desktop Edition):** تعمل محلياً باستخدام مكتبة الواجهات الرسومية القياسية `Tkinter / ttk` عبر نقطة الدخول `main.py` وقاعدة بيانات `data/pharmacy.db`.
2. **نسخة الويب ثنائية اللغة (Bilingual Web Edition):** تعمل عبر المتصفح باستخدام إطار العمل `Streamlit` عبر نقطة الدخول `web_app/app.py` وقاعدة بيانات معزولة `data/pharmacy_web.db` مع دعم كامل للغة العربية (RTL) والإنجليزية (LTR).

### 1.2 المشكلة التي يعالجها النظام
تواجه الصيدليات الصغيرة والمتوسطة عند الاعتماد على الدفاتر الورقية أو جداول البيانات التقليدية (Excel) عدة مخاطر تشغيلية وصحية:
- **بيع أدوية منتهية الصلاحية (Expired Medicines):** الخطأ البشري في قراءة تاريخ الصلاحية يهدد سلامة المرضى ويعرض الصيدلية للمساءلة القانونية.
- **نقص المخزون المفاجئ (Stock-outs):** عدم وجود تنبيه مبكر عند انخفاض الرصيد عن حد إعادة الطلب (`reorder_level`).
- **تضارب الحسابات والأرباح:** صعوبة تتبع سعر التكلفة (`cost_price`) مقارنة بسعر البيع (`unit_price`) وحساب الخصومات والضرائب وصافي الربح اليومي بدقة.
- **انقطاع الترابط بين المشتريات والمبيعات:** صعوبة معرفة أي مورد (`Supplier`) يزود الصيدلية بكل تشغيلة (`Batch`).

### 1.3 لماذا تحتاج إدارة الصيدلية إلى برمجيات متخصصة؟
الصيدلية ليست متجراً عادياً؛ فهي تتعامل مع **تشغيلات دوائية (Batches)** لكل منها تاريخ صلاحية مختلف (`expiry_date`) وقيود بيع صارمة. البرمجية المتخصصة تفرض قواعد السلامة آلياً (مثل منع بيع الدواء المنتهي في نقطة البيع على مستوى الخدمة وقاعدة البيانات)، وتضمن **الذرية في المعاملات (Atomic Transactions)** بحيث لا ينقص المخزون دون إصدار فاتورة، ولا تُصدر فاتورة دون خصم المخزون.

### 1.4 أهداف المشروع
1. أتمتة دورة حياة الدواء من التوريد حتى البيع للعميل.
2. منع صرف أو بيع أي تشغيلة دوائية منتهية الصلاحية برمجياً.
3. توفير نقطة بيع سريعة (`POS`) تحسب الإجمالي والخصم والضريبة وصافي الربح تلقائياً.
4. إنشاء سجل تدقيق (`stock_adjustments`) يوثّق كل زيادة أو نقصان في المخزون.
5. تقديم لوحة تحكم وتقارير مالية ورسوم بيانية لدعم اتخاذ القرار.
6. دعم المستخدم العربي والأجنبي بواجهة ثنائية اللغة (عربي RTL / إنجليزي LTR).

### 1.5 نطاق المشروع وحدوده (Scope & Limitations)
- **ضمن النطاق:** إدارة الأدوية والتشغيلات، إدارة الموردين، نقطة البيع والفواتير، تنبيهات الصلاحية وانخفاض المخزون، شطب المخزون المنتهي، التقارير اليومية وتصدير CSV، واجهة مكتبية وواجهة ويب سحابية.
- **خارج النطاق حالياً (القيود):** لا يوجد نظام تسجيل دخول وصلاحيات مستخدمين (Authentication/RBAC) في النسخة الحالية، وقاعدة البيانات الافتراضية على الاستضافة السحابية المجانية هي ملف SQLite محلي مؤقت.

### 1.6 المتطلبات الوظيفية وغير الوظيفية
**المتطلبات الوظيفية (Functional Requirements):**
- عمليات CRUD الكاملة للأدوية والموردين.
- البحث والتصفية حسب الاسم، الاسم العلمي، رقم التشغيلة، التصنيف، أو حالة التوفر.
- التحقق في POS من الصلاحية وتوفر الكمية وحساب المجموع والخصم والضريبة والربح.
- تقارير زمنية وتصدير CSV.

**المتطلبات غير الوظيفية (Non-Functional Requirements):**
- **الموثوقية وسلامة البيانات (Data Integrity):** استخدام معاملات SQLite الذرية والقيود المرجعية (`FOREIGN KEY` و `CHECK`).
- **الأداء وتعدد الخيوط (Thread Safety):** استخدام قفل `threading.RLock` ووضع `WAL` في نسخة الويب.
- **قابلية الصيانة (Maintainability):** فصل الطبقات (UI / Services / Models / Database).
- **سهولة الوصول (Accessibility & Localization):** تصميم داكن واضح التباين مع دعم RTL كامل للغة العربية.

---

## الفصل الثاني — حزمة التقنيات المستخدمة

| التقنية | الدور في المشروع | لماذا تم اختيارها؟ |
|---|---|---|
| **Python 3 (3.11)** | اللغة الأساسية لبناء كامل المنظومة | سهلة القراءة، غنية بالمكتبات القياسية، وتدعم البرمجة كائنية التوجه (`OOP`) وتكامل الويب وسطح المكتب معاً. |
| **Tkinter / ttk** | واجهة المستخدم للنسخة المكتبية (`pharmacy/ui/`) | تأتي مدمجة مع بايثون (Standard Library) ولا تتطلب تثبيت حزم خارجية لتشغيل التطبيق محلياً. |
| **Streamlit** | إطار عمل واجهة الويب التفاعلية (`web_app/`) | يحول كود بايثون مباشرة إلى تطبيق ويب حديث ومتجاوب دون كتابة خادم REST منفصل أو كود JavaScript معقد. |
| **SQLite 3** | محرك قاعدة البيانات العلائقية المدمج | خفيف الوزن، يعمل كملف واحد (`pharmacy.db` / `pharmacy_web.db`)، يدعم معاملات `ACID` والقيود العلائقية، ولا يحتاج خادم قواعد بيانات مستقل للتشغيل الأولي. |
| **Matplotlib** | توليد الرسوم البيانية في صفحة التقارير | مكتبة قياسية موثوقة تتيح تخصيص الألوان الداكنة وإنتاج مخططات الإيرادات والأرباح وتقييم المخزون بسهولة. |
| **OOP (البرمجة كائنية التوجه)** | تنظيم الكيانات (`dataclasses`) والخدمات (`Services`) | تمنع تكرار الكود وتفصل قواعد العمل عن الواجهة الرسومية، مما سمح بإعادة استخدام نفس الخدمات في Desktop و Web. |
| **Git & GitHub** | نظام التحكم بالإصدارات واستضافة الشيفرة | يحفظ تاريخ التعديلات ويربط المشروع مباشرة بمنصة النشر السحابي. |
| **Streamlit Community Cloud** | منصة الاستضافة السحابية المجانية لنسخة الويب | تنشر تطبيقات Streamlit مباشرة من مستودع GitHub عبر تحديد ملف الدخول `web_app/app.py`. |

---

## الفصل الثالث — معمارية المشروع

### 3.1 الهيكل التنظيمي للمجلدات (Folder Structure)
```text
/
├── main.py                          # نقطة دخول النسخة المكتبية (Tkinter)
├── requirements.txt                 # متطلبات النسخة المكتبية
├── README.md                        # توثيق النسخة المكتبية
├── DISCUSSION_GUIDE.md              # ملخص معماري مختصر
├── .streamlit/
│   └── config.toml                  # إعدادات السمة الداكنة لـ Streamlit
├── pharmacy/                        # الحزمة المشتركة (المنطق الأساسي + واجهة سطح المكتب)
│   ├── config.py                    # الثوابت والإعدادات العامة
│   ├── utils.py                     # دوال التحقق، التواريخ، فحص الصلاحية، وتصدير CSV
│   ├── models/
│   │   └── entities.py              # الكيانات (Supplier, Medicine, CartItem, Sale, ...)
│   ├── database/
│   │   └── db_manager.py            # إدارة اتصال SQLite، الجداول، المعاملات، والبيانات الأولية
│   ├── services/
│   │   ├── supplier_service.py      # منطق إدارة الموردين
│   │   ├── inventory_service.py     # منطق المخزون والأدوية والتعديلات
│   │   ├── sales_service.py         # منطق نقطة البيع والحسابات والمعاملات الذرية
│   │   └── report_service.py        # إحصائيات لوحة التحكم والتقارير
│   └── ui/                          # واجهات Tkinter للنسخة المكتبية فقط
├── web_app/                         # نسخة الويب المستقلة (Streamlit)
│   ├── app.py                       # نقطة دخول نسخة الويب + التوجيه + مبدل اللغة
│   ├── config.py                    # ألوان السمة الداكنة ومسار قاعدة الويب المعزولة
│   ├── requirements.txt             # اعتماديات الاستضافة السحابية (streamlit, matplotlib)
│   ├── core/
│   │   ├── db_adapter.py            # محول SQLite آمن للخيوط + واجهة DatabaseBackend
│   │   ├── web_services.py          # تحليلات الأرباح + وحدة تحكم السلة ومنع التكرار
│   │   ├── i18n.py                  # القاموس المركزي العربي/الإنجليزي ومترجم الأخطاء
│   │   └── arabic_shape.py          # تشكيل الحروف العربية للرسوم البيانية في Matplotlib
│   ├── components/
│   │   ├── theme.py                 # تنسيقات CSS الداكنة واتجاهات RTL/LTR وبطاقات KPI
│   │   └── charts.py                # بناء مخططات Matplotlib بالوضع الداكن
│   └── pages_ui/                    # الصفحات السبع للويب
├── tests/
│   ├── test_pharmacy_system.py      # اختبارات النسخة المكتبية والخدمات الأساسية (6 اختبارات)
│   └── test_web_edition.py          # اختبارات نسخة الويب والتوطين وتعدد الخيوط (6 اختبارات)
└── docs/
    ├── RxCare_Complete_Project_Guide.md
    └── RxCare_Complete_Project_Guide.html
```

### 3.2 فصل الطبقات (Layered Architecture)
اعتمد المشروع نمط **العمارة الطبقية (Layered Architecture)** المكون من 4 طبقات:
1. **طبقة العرض (Presentation Layer):** مسؤولة فقط عن عرض البيانات واستقبال المدخلات (`pharmacy/ui/` لسطح المكتب، و `web_app/pages_ui/` للويب).
2. **طبقة الخدمات (Service Layer):** تحتوي على جميع القواعد التجارية والحسابات والتحقق (`SupplierService`, `InventoryService`, `SalesService`, `ReportService`, `WebAnalyticsService`).
3. **طبقة النماذج (Domain Models Layer):** تمثل هياكل البيانات النظيفة (`@dataclass` في `pharmacy/models/entities.py`).
4. **طبقة البيانات (Database Layer):** تتولى الاتصال بـ SQLite وتنفيذ الاستعلامات والمعاملات (`DatabaseManager` و `WebSQLiteDatabaseManager`).

### 3.3 كيف تتعايش النسخة المكتبية ونسخة الويب معاً؟
```text
+-----------------------------------+      +----------------------------------------+
|   Desktop UI (Tkinter / main.py)  |      |   Web UI (Streamlit / web_app/app.py)  |
+-----------------+-----------------+      +-------------------+--------------------+
                  |                                            |
                  |                                            v
                  |                        +----------------------------------------+
                  |                        | Web Layer: i18n, WebSessionController, |
                  |                        |            WebAnalyticsService         |
                  |                        +-------------------+--------------------+
                  |                                            |
                  +--------------------+-----------------------+
                                       |
                                       v
                  +--------------------------------------------+
                  |   Shared Business Services (pharmacy/)     |
                  | Supplier | Inventory | Sales | Report      |
                  +--------------------+-----------------------+
                                       |
               +-----------------------+-----------------------+
               |                                               |
               v                                               v
+------------------------------+             +----------------------------------+
| Desktop DatabaseManager      |             | WebSQLiteDatabaseManager         |
| check_same_thread=True       |             | check_same_thread=False + RLock  |
| -> data/pharmacy.db          |             | -> data/pharmacy_web.db          |
+------------------------------+             +----------------------------------+
```

**لماذا أنشأنا محولاً خاصاً للويب (`WebSQLiteDatabaseManager`) بدلاً من تعديل `DatabaseManager` الأصلي؟**
1. النسخة المكتبية تستخدم `check_same_thread=True` لأن Tkinter يعمل في خيط رئيسي واحد.
2. أما Streamlit فيشغل إعادة التنفيذ (`Rerun`) عبر عدة خيوط عمل (Worker Threads). استخدام اتصال SQLite مقيد بخيط واحد يسبب خطأ `sqlite3.ProgrammingError`.
3. لذلك ورث `WebSQLiteDatabaseManager` نفس مخطط الجداول ونفس منطق `SAVEPOINT` من `DatabaseManager` دون تعديل الملف الأصلي، مع إضافة `check_same_thread=False` وقفل `threading.RLock()` وعزل مسار التخزين في `data/pharmacy_web.db`.

---

## الفصل الرابع — تصميم قاعدة البيانات

تتكون قاعدة البيانات من **5 جداول فعلية** ومجموعة فهارس (`Indexes`) مع تفعيل المفتاح الأجنبي إلزامياً عبر `PRAGMA foreign_keys = ON;`.

### 4.1 الجداول الفعلية وأعمدتها

#### 1. جدول الموردين (`suppliers`)
| العمود | النوع والقيود | الوصف |
|---|---|---|
| `id` | `INTEGER PRIMARY KEY AUTOINCREMENT` | المعرف الفريد للمورد |
| `name` | `TEXT NOT NULL UNIQUE` | اسم المورد (لا يتكرر) |
| `contact_person` | `TEXT NOT NULL DEFAULT ''` | اسم الشخص المسؤول |
| `phone` | `TEXT NOT NULL DEFAULT ''` | رقم الهاتف |
| `email` | `TEXT NOT NULL DEFAULT ''` | البريد الإلكتروني |
| `address` | `TEXT NOT NULL DEFAULT ''` | العنوان |
| `created_at` | `TEXT NOT NULL` | وقت الإنشاء |

#### 2. جدول الأدوية (`medicines`)
| العمود | النوع والقيود | الوصف |
|---|---|---|
| `id` | `INTEGER PRIMARY KEY AUTOINCREMENT` | المعرف الفريد للتشغيلة الدوائية |
| `name` | `TEXT NOT NULL` | الاسم التجاري للدواء |
| `generic_name` | `TEXT NOT NULL DEFAULT ''` | الاسم العلمي للمادة الفعالة |
| `category` | `TEXT NOT NULL DEFAULT 'General'` | التصنيف الدوائي |
| `batch_number` | `TEXT NOT NULL UNIQUE` | رقم التشغيلة الفريد |
| `supplier_id` | `INTEGER REFERENCES suppliers(id) ON DELETE RESTRICT` | مفتاح أجنبي يربط الدواء بالمورد ويمنع حذف مورد مرتبط بأدوية |
| `cost_price` | `REAL NOT NULL CHECK (cost_price >= 0)` | سعر التكلفة (لا يقبل السالب) |
| `unit_price` | `REAL NOT NULL CHECK (unit_price > 0)` | سعر البيع (أكبر من صفر) |
| `quantity` | `INTEGER NOT NULL CHECK (quantity >= 0)` | الرصيد الحالي بالمخزون |
| `reorder_level` | `INTEGER NOT NULL DEFAULT 10 CHECK (reorder_level >= 0)` | حد التنبيه لانخفاض المخزون |
| `expiry_date` | `TEXT NOT NULL` | تاريخ الصلاحية بصيغة `YYYY-MM-DD` |
| `description` | `TEXT NOT NULL DEFAULT ''` | ملاحظات إضافية |
| `created_at`, `updated_at` | `TEXT NOT NULL` | طوابع زمنية للإنشاء والتحديث |

#### 3. جدول المبيعات (`sales`)
| العمود | النوع والقيود | الوصف |
|---|---|---|
| `id` | `INTEGER PRIMARY KEY AUTOINCREMENT` | معرف الفاتورة |
| `invoice_number` | `TEXT NOT NULL UNIQUE` | رقم الفاتورة مثل `INV-20261127-0001` |
| `customer_name`, `customer_phone` | `TEXT` | اسم وهاتف العميل |
| `subtotal` | `REAL NOT NULL CHECK (subtotal >= 0)` | المجموع الفرعي قبل الخصم والضريبة |
| `discount_percent`, `discount_amount` | `REAL` | نسبة وقيمة الخصم (`0..100%`) |
| `tax_percent`, `tax_amount` | `REAL` | نسبة وقيمة الضريبة (`0..100%`) |
| `total_amount` | `REAL NOT NULL CHECK (total_amount >= 0)` | الإجمالي النهائي المطلوب دفعه |
| `amount_paid`, `change_due` | `REAL` | المبلغ المدفوع والباقي للعميل |
| `payment_method` | `TEXT NOT NULL DEFAULT 'Cash'` | طريقة الدفع (`Cash`, `Card`, `Insurance / Digital`) |
| `sale_date` | `TEXT NOT NULL` | تاريخ ووقت الفاتورة |
| `notes` | `TEXT NOT NULL DEFAULT ''` | ملاحظات الفاتورة |

#### 4. جدول بنود الفاتورة (`sale_items`)
| العمود | النوع والقيود | الوصف |
|---|---|---|
| `id` | `INTEGER PRIMARY KEY AUTOINCREMENT` | معرف السطر |
| `sale_id` | `INTEGER NOT NULL REFERENCES sales(id) ON DELETE CASCADE` | ربط بالفاتورة الأم |
| `medicine_id` | `INTEGER NOT NULL REFERENCES medicines(id) ON DELETE RESTRICT` | ربط بالدواء ويمنع حذف دواء تم بيعه سابقاً |
| `medicine_name`, `batch_number` | `TEXT NOT NULL` | لقطة (Snapshot) تحفظ الاسم والتشغيلة وقت البيع |
| `quantity` | `INTEGER NOT NULL CHECK (quantity > 0)` | الكمية المباعة |
| `unit_price`, `line_total` | `REAL` | سعر الوحدة وإجمالي السطر وقت البيع |

#### 5. جدول تدقيق حركات المخزون (`stock_adjustments`)
| العمود | النوع والقيود | الوصف |
|---|---|---|
| `id` | `INTEGER PRIMARY KEY AUTOINCREMENT` | معرف حركة التدقيق |
| `medicine_id` | `INTEGER NOT NULL REFERENCES medicines(id) ON DELETE CASCADE` | الدواء المعدّل |
| `change_qty` | `INTEGER NOT NULL` | مقدار التغيير (موجب للتوريد، سالب للبيع أو الشطب) |
| `reason` | `TEXT NOT NULL` | سبب الحركة (`Initial Stock`, `Restock`, `Sale`, `Expired Write-Off`, ...) |
| `reference_note` | `TEXT NOT NULL DEFAULT ''` | رقم الفاتورة أو أمر الشراء |
| `created_at` | `TEXT NOT NULL` | وقت تسجيل الحركة |

### 4.2 مخطط العلاقات (ER Diagram)
```text
+-------------------+          1 : N          +-------------------------+
|     suppliers     |------------------------>|        medicines        |
|-------------------|  (ON DELETE RESTRICT)   |-------------------------|
| PK id             |                         | PK id                   |
|    name (UNIQUE)  |                         | FK supplier_id          |
+-------------------+                         |    batch_number(UNIQUE) |
                                              |    cost_price,unit_price|
                                              |    quantity, expiry_date|
                                              +------------+------------+
                                                           |
                     +-------------------------------------+
                     | 1 : N (ON DELETE CASCADE)           | 1 : N (ON DELETE RESTRICT)
                     v                                     v
       +---------------------------+         +---------------------------+
       |     stock_adjustments     |         |        sale_items         |
       |---------------------------|         |---------------------------|
       | PK id                     |         | PK id                     |
       | FK medicine_id            |         | FK sale_id                |
       |    change_qty, reason     |         | FK medicine_id            |
       +---------------------------+         |    quantity, line_total   |
                                             +-------------+-------------+
                                                           ^
                                                           | N : 1 (ON DELETE CASCADE)
                                             +-------------+-------------+
                                             |           sales           |
                                             |---------------------------|
                                             | PK id                     |
                                             |    invoice_number(UNIQUE) |
                                             |    total_amount, sale_date|
                                             +---------------------------+
```

### 4.3 المعاملات (Transactions) والبيانات الأولية (Seed Data)
- تم ضبط `isolation_level=None` لكي يتحكم التطبيق يدوياً بالمعاملة عبر `BEGIN IMMEDIATE` و `COMMIT` و `ROLLBACK` (أو `SAVEPOINT` عند تداخل المعاملات).
- عند أول تشغيل، تتحقق الدالة `seed_sample_data()` عبر `is_empty()` من أن جدولَي الموردين والأدوية فارغان؛ فإذا وُجدت بيانات بالفعل لا تُكرَّر البيانات أبداً عبر إعادة تشغيل Streamlit.

---

## الفصل الخامس — مفاهيم برمجة بايثون المستخدمة

1. **المتغيرات وأنواع البيانات (`Variables & Data Types`):** استخدام `int` للكميات، `float` للأسعار والنسب، `str` للتواريخ والأسماء، و`dict`/`list` لتخزين السلة والسجلات.
2. **الدوال والمعاملات (`Functions & Parameters`):** مثل `format_currency(amount: float) -> str` و`is_expired(expiry_iso: str, reference_date: date | None = None) -> bool` في `pharmacy/utils.py`.
3. **الفئات والكائنات (`Classes & Objects`) و `@dataclass`:** في `pharmacy/models/entities.py` نمذجة الكيانات مثل `Medicine` و`CartItem` مع خاصية `@property def line_total(self) -> float`.
4. **الدالة البانية (`__init__`) والتغليف (`Encapsulation`):** في `DatabaseManager.__init__` يتم فتح الاتصال وإخفاء المتغير `self._conn` كخاصية داخلية محمية.
5. **الوراثة (`Inheritance`):** الفئة `WebSQLiteDatabaseManager(DatabaseManager)` ترث تعريف الجداول ودالة التأسيس من الأب وتعيد تعريف `__init__` و`transaction` لتناسب الويب.
6. **الاستيراد والوحدات (`Imports & Modules`):** تقسيم المشروع لحزم نظيفة (`pharmacy`, `web_app`, `tests`) مع ربط جذر المشروع في `sys.path` داخل `web_app/app.py`.
7. **معالجة الاستثناءات (`Exception Handling`):** تعريف استثناءات مخصصة `ValidationError` و`BusinessRuleError` والتقاطها لإظهار رسائل واضحة للمستخدم دون انهيار التطبيق.
8. **مدير السياق (`Context Managers`):** استخدام `@contextmanager def transaction(self)` لضمان تنفيذ `COMMIT` عند النجاح أو `ROLLBACK` تلقائياً عند أي خطأ.
9. **سلامة الخيوط (`Thread Safety`):** استخدام `threading.RLock()` في `WebSQLiteDatabaseManager` لمنع تضارب الكتابة المتزامنة في Streamlit.
10. **البروتوكولات وتلميحات الأنواع (`Protocols & Type Hints`):** تعريف `class DatabaseBackend(Protocol)` في `web_app/core/db_adapter.py` لتسهيل تبديل SQLite بقاعدة بيانات سحابية مستقبلاً.

---

## الفصل السادس — شرح وحدات التطبيق

| الوحدة / الصفحة | الغرض | ملف الواجهة (Web) | ملف الخدمة المستخدم | العمليات الرئيسية وقواعد التحقق |
|---|---|---|---|---|
| **لوحة التحكم (Dashboard)** | ملخص فوري للأداء | `web_app/pages_ui/dashboard_page.py` | `ReportService`, `WebAnalyticsService` | عرض إجمالي الأدوية، النواقص، المنتهية، مبيعات اليوم، وصافي الربح. |
| **إدارة الأدوية (Medicines)** | كتالوج الأصناف CRUD | `web_app/pages_ui/medicines_page.py` | `InventoryService`, `WebAnalyticsService` | إضافة/تعديل/حذف، بحث، تصفية بالتصنيف والحالة، منع تكرار رقم التشغيلة، ومنع حذف دواء له مبيعات. |
| **نقطة البيع (POS)** | إصدار الفواتير والبيع | `web_app/pages_ui/pos_page.py` | `SalesService`, `WebSessionController`, `WebAnalyticsService` | سلة مشتريات، حساب الخصم والضريبة والربح، حظر الأدوية المنتهية، منع تجاوز الرصيد، ومعاملة ذرية تمنع التكرار. |
| **إدارة المخزون (Inventory)** | مراقبة وتعديل الأرصدة | `web_app/pages_ui/inventory_page.py` | `InventoryService` | تعديل الرصيد (+/-) مع إلزام ذكر السبب، منع الهبوط تحت الصفر، عرض سجل التدقيق، وتصدير CSV. |
| **الموردون (Suppliers)** | إدارة الموردين CRUD | `web_app/pages_ui/suppliers_page.py` | `SupplierService` | إضافة/تعديل/حذف، التحقق من صحة البريد، ومنع حذف مورد مرتبط بأدوية (`BusinessRuleError`). |
| **تنبيهات الصلاحية (Alerts)** | الحجر الدوائي والتنبيه | `web_app/pages_ui/alerts_page.py` | `InventoryService` | نافذة تحذير قابلة للتغيير (15/30/60/90 يوم)، شطب الكمية المنتهية إلى 0، وتوريد سريع للنواقص. |
| **التقارير (Reports)** | التحليل المالي والرسوم | `web_app/pages_ui/reports_page.py` | `ReportService`, `WebAnalyticsService` | تقارير زمنية، مخططات Matplotlib داكنة، أكثر الأدوية مبيعاً، تقييم المخزون، وتصدير CSV. |

---

## الفصل السابع — جولة تفصيلية في أهم دوال الكود

### 7.1 الاتصال بقاعدة البيانات والمعاملة الذرية (`pharmacy/database/db_manager.py`)
```python
@contextmanager
def transaction(self) -> Iterator[sqlite3.Connection]:
    conn = self.connection
    is_outer = self._tx_depth == 0
    savepoint_name = f"sp_{self._tx_depth}"

    if is_outer:
        conn.execute("BEGIN IMMEDIATE;")
    else:
        conn.execute(f"SAVEPOINT {savepoint_name};")

    self._tx_depth += 1
    try:
        yield conn
    except Exception:
        if is_outer:
            if conn.in_transaction:
                conn.execute("ROLLBACK;")
        else:
            conn.execute(f"ROLLBACK TO SAVEPOINT {savepoint_name};")
            conn.execute(f"RELEASE SAVEPOINT {savepoint_name};")
        raise
    else:
        if is_outer:
            if conn.in_transaction:
                conn.execute("COMMIT;")
        else:
            conn.execute(f"RELEASE SAVEPOINT {savepoint_name};")
    finally:
        self._tx_depth -= 1
```
**الشرح للمبتدئين:**
- عند بدء العملية (`is_outer = True`) يفتح الكود معاملة حصرية `BEGIN IMMEDIATE` تمنع أي كتابة متضاربة.
- إذا استُدعيت معاملة داخل معاملة أخرى (`_tx_depth > 0`) يُنشئ نقطة حفظ `SAVEPOINT`.
- داخل `try` يتم تمرير الاتصال `yield conn` لتنفيذ عمليات SQL.
- إذا حدث أي استثناء في منتصف العمل، ينتقل التنفيذ إلى `except` فيتم التراجع الكامل (`ROLLBACK`) ولا يُحفظ أي تعديل جزئي! أما عند النجاح فينفذ `COMMIT`.

### 7.2 حظر الأدوية المنتهية الصلاحية (`pharmacy/utils.py`)
```python
def is_expired(expiry_iso: str, reference_date: date | None = None) -> bool:
    ref = reference_date or today_date()
    exp = parse_iso_date(expiry_iso, "Expiry date")
    return exp <= ref
```
**الشرح:** تحوّل الدالة نص التاريخ (`YYYY-MM-DD`) إلى كائن `date` وتقارنه بتاريخ اليوم. تطبيقاً لسياسة السلامة الدوائية، إذا كان تاريخ الانتهاء اليوم أو قبله (`<=`) يُعتبر منتهي الصلاحية ويُمنع بيعه.

### 7.3 التحقق قبل الإضافة للسلة وإتمام البيع الذري (`pharmacy/services/sales_service.py`)
1. تتحقق `validate_medicine_for_cart(medicine_id, requested_qty)` من وجود الدواء، وعدم انتهاء صلاحيته عبر `is_expired`, وتوفر الكمية المطلوبة.
2. عند الدفع داخل `create_sale(...)`:
   - يُفتح سياق `with self.db.transaction() as conn:`.
   - يُعاد فحص كل صنف من قاعدة البيانات مباشرة (وليس من الذاكرة المؤقتة) للتحقق من الصلاحية والكمية والسعر الحقيقي `row["unit_price"]`.
   - تحسب `calculate_totals(...)` المجموع الفرعي، ثم الخصم `round(subtotal * (disc_pct / 100.0), 2)`، ثم الضريبة على المبلغ بعد الخصم، ثم الإجمالي النهائي والباقي.
   - تُسجّل الفاتورة في `sales`، والبنود في `sale_items`، ويُخصم الرصيد من `medicines`، وتُوثّق الحركة في `stock_adjustments`.
   - فشل أي سطر واحد (مثلاً نفاد صنف رقم 2 في السلة) يلغي الفاتورة ويلغي خصم الصنف رقم 1 بالكامل.

### 7.4 حساب صافي الربح (`web_app/core/web_services.py`)
في `WebAnalyticsService.get_profit_summary(...)` و`calculate_cart_profit(...)`:
- إيراد البنود = مجموع `(سعر البيع × الكمية)`.
- تكلفة البضاعة المباعة (COGS) = مجموع `(cost_price × الكمية)`.
- **إجمالي الربح (Gross Profit)** = إيراد البنود − التكلفة.
- **صافي الربح (Net Profit)** = إجمالي الربح − قيمة الخصم الممنوح على الفاتورة.

### 7.5 منع تكرار الفواتير عند إعادة التشغيل (`WebSessionController.complete_sale_idempotent`)
في Streamlit، كل ضغطة زر أو تغيير واجهة يعيد تشغيل السكربت من الأعلى للأسفل (`Rerun`).
- يحتفظ التطبيق برمز معاملة فريد `rxcare_pos_tx_token` في `st.session_state`.
- عند نجاح إتمام البيع، يُخزن الرمز داخل `rxcare_processed_tx_tokens` مع رقم الفاتورة، وتُفرغ السلة ويُولّد رمز جديد فوراً.
- إذا أُعيد إرسال نفس الرمز بالخطأ أثناء Rerun، يُرجع الكود الفاتورة المسجلة دون إنشاء فاتورة مكررة أو خصم المخزون مرتين!

---

## الفصل الثامن — آلية تشغيل التطبيق والنشر

1. **التشغيل في بايثون:** عند تنفيذ `streamlit run web_app/app.py`:
   - يضيف `web_app/app.py` جذر المشروع إلى `sys.path` لضمان عمل استيراد `pharmacy.*` و`web_app.*`.
   - يستدعي `get_web_app_container()` المزيّن بـ `@st.cache_resource` لإنشاء اتصال SQLite واحد مشترك لكل خادم وبذر البيانات مرة واحدة فقط إذا كانت الجداول فارغة.
2. **التفاعل وإعادة التنفيذ (Rerun) وحالة الجلسة (`Session State`):**
   - في كل نقرة للمستخدم يعيد Streamlit تنفيذ `main()`؛ هنا تحافظ `st.session_state` على اللغة المختارة (`rxcare_lang`)، الصفحة الحالية (`rxcare_page_key`)، سلة المشتريات (`rxcare_pos_cart`)، ورمز المعاملة (`rxcare_pos_tx_token`).
3. **النشر عبر GitHub و Streamlit Community Cloud:**
   - يقرأ Streamlit Community Cloud الإعدادات من `.streamlit/config.toml` في جذر المستودع، ويثبّت الاعتماديات من `web_app/requirements.txt` (`streamlit>=1.38.0`, `matplotlib>=3.8.0`)، ويشغّل `web_app/app.py`.

---

## الفصل التاسع — الاختبارات ومعالجة الأخطاء

### 9.1 الاختبارات المنفذة فعلياً
يحتوي المجلد `tests/` على ملفين للاختبار الآلي باستخدام `unittest`:
1. **`tests/test_pharmacy_system.py` (6 اختبارات للنظام الأساسي والنسخة المكتبية):**
   - `test_schema_foreign_keys_and_seed_idempotency`: فحص تفعيل `PRAGMA foreign_keys` وعدم تكرار بيانات البذر.
   - `test_supplier_crud_and_delete_protection`: إنشاء/تحديث الموردين ومنع حذف مورد مرتبط بدواء.
   - `test_medicine_crud_filtering_and_adjustments`: إضافة/تعديل الأدوية، التصفية، التوريد، الشطب المنتهي، ومنع الرصيد السالب.
   - `test_sales_calculations_and_inventory_decrement`: دقة حساب الخصم والضريبة والباقي وخصم المخزون ومنع حذف دواء مباع.
   - `test_expiry_restriction_and_atomic_rollback`: حظر المنتهي الصلاحية (بما فيها تاريخ اليوم)، والتراجع الذري الكامل عند فشل أحد بنود السلة أو نقص المخزون أو نقص الدفع.
   - `test_dashboard_reports_and_csv_export`: صحة مؤشرات لوحة التحكم والتقارير وتصدير CSV.
2. **`tests/test_web_edition.py` (6 اختبارات لنسخة الويب والتوطين):**
   - `test_web_db_isolation_and_seed_once_across_reruns`: عزل قاعدة بيانات الويب وتحليل روابط `sqlite:///` ورفض الروابط غير المدعومة بـ `NotImplementedError` واختبار رسائل الفلاش.
   - `test_thread_safe_reads_and_writes`: تشغيل 6 خيوط متزامنة للقراءة والكتابة دون أخطاء SQLite.
   - `test_medicine_category_filter_and_crud`: التصفية بالتصنيف وحذف الأدوية.
   - `test_pos_session_cart_profit_expiry_and_rerun_idempotency`: سلة الجلسة، حساب الربح، حظر المنتهي، ومنع تكرار الفاتورة عند إعادة إرسال نفس الرمز.
   - `test_reports_daily_sales_and_profit_summary`: تقارير الأرباح والسلسلة اليومية للمبيعات.
   - `test_bilingual_i18n_parity_cart_preservation_and_shaping`: تطابق مفاتيح العربية والإنجليزية 100%، وبقاء السلة والصفحة ورمز المعاملة عند تبديل اللغة، وتشكيل الحروف العربية لـ Matplotlib.

### 9.2 ما تم اختباره مقابل ما لم يُختبر هنا
- **تم تنفيذه فعلياً ونجح (12/12 اختباراً + فحص `compileall` و AST):** جميع عمليات قاعدة البيانات، CRUD، الحسابات، التراجع الذري، تعدد الخيوط، التوطين، وتصدير CSV.
- **لم يُختبر داخل حاوية الخادم السحابية:** التشغيل المباشر لنافذة `Tkinter` (لعدم وجود `python3-tk` وشاشة رسومية في الحاوية)، والتشغيل الحي لمتصفح `Streamlit` (لعدم تثبيت `streamlit`/`matplotlib` في الحاوية نفسها).

---

## الفصل العاشر — الأمان والقيود

1. **عزل قواعد البيانات:** النسخة المكتبية تستخدم `data/pharmacy.db` ونسخة الويب تستخدم `data/pharmacy_web.db` لتجنب أي تداخل.
2. **التحقق من المدخلات ومنع حقن SQL:** جميع الاستعلامات تستخدم **الاستعلامات المعلمية (Parameterized Queries)** عبر علامة `?` (مثل `WHERE id = ?`) ولا تدمج مدخلات المستخدم نصياً داخل SQL.
3. **إخفاء التفاصيل الحساسة:** في `web_app/app.py` تُلتقط الاستثناءات غير المتوقعة وتُعرض رسالة ودية مترجمة دون كشف مسارات الخادم أو تتبّع الأخطاء الكامل للمستخدم النهائي.
4. **حالة المصادقة والصلاحيات (Authentication & RBAC):** لا يحتوي النظام حالياً على تسجيل دخول أو أدوار مستخدمين (مدير/كاشير)؛ وهو مصمم كنظام تشغيلي لنقطة عمل واحدة أو عرض تعليمي.
5. **قيود SQLite على الاستضافة السحابية:** تخزين الملفات المحلي في Streamlit Community Cloud **مؤقت (Ephemeral)** وقد تُمحى البيانات عند إعادة التشغيل أو التحديث. للانتقال للإنتاج الفعلي يلزم ربط `DatabaseBackend` بقاعدة بيانات سحابية دائمة مثل PostgreSQL وإضافة نظام مصادقة.

---

## الفصل الحادي عشر — دليل التشغيل والصيانة

```bash
# 1. تشغيل النسخة المكتبية (Tkinter)
python3 main.py

# 2. تثبيت اعتماديات نسخة الويب وتشغيلها محلياً
pip install -r web_app/requirements.txt
streamlit run web_app/app.py

# 3. تشغيل جميع الاختبارات الآلية (المكتبية + الويب)
python3 -m unittest discover -s tests -v

# 4. تحديث مستودع GitHub وإعادة النشر التلقائي على Streamlit Cloud
git add .
git commit -m "Update RxCare bilingual UI and documentation"
git push origin main
```

---

## الفصل الثاني عشر — التحسينات المستقبلية

| الميزة | الحالة الحالية | مقترح التطوير المستقبلي |
|---|---|---|
| قاعدة البيانات السحابية | محلي SQLite (`sqlite:///`) | إضافة محول PostgreSQL / Supabase عبر `RXCARE_WEB_DB_URL` |
| الأمان والمستخدمون | غير منفذ | إضافة تسجيل دخول وصلاحيات (مدير، صيدلي، كاشير) |
| قارئ الباركود | غير منفذ | ربط حقل البحث في POS بقارئ Barcode لسرعة الصرف |
| تنبيهات آلية | عرض داخل الواجهة | إرسال تنبيهات بريد إلكتروني أو واتساب عند قرب الانتهاء |
| طباعة الفاتورة | ملخص فاتورة + CSV | دعم طابعات الإيصالات الحرارية (80mm) بصيغة PDF/Print |

---

## الفصل الثالث عشر — أسئلة المناقشة الجامعية (45 سؤالاً وإجابة)

### أولاً: الأسئلة الأساسية وفكرة المشروع
1. **ما هي فكرة مشروع RxCare؟** نظام لإدارة الصيدليات يدير الأدوية والموردين والمخزون والمبيعات وتنبيهات الصلاحية عبر نسخة مكتبية ونسخة ويب ثنائية اللغة.
2. **ما المشكلة الحقيقية التي يحلها النظام؟** يمنع بيع الأدوية المنتهية الصلاحية، ويتتبع النواقص والتكاليف والأرباح بدقة، ويستبدل السجلات الورقية.
3. **ما الفرق بين الواجهة الأمامية (Frontend) والخلفية (Backend) في مشروعك؟** الواجهة الأمامية (`pharmacy/ui` أو `web_app/pages_ui`) مسؤولة عن العرض وتفاعل المستخدم، بينما الخلفية (`pharmacy/services` و`database`) مسؤولة عن قواعد العمل والحسابات والتخزين في SQLite.
4. **لماذا قمت ببناء نسختين (Desktop و Web)؟** لإثبات مرونة المعمارية الطبقية؛ حيث يعمل النظام محلياً دون إنترنت عبر Tkinter، ويعمل عن بُعد عبر المتصفح والسحابة باستخدام Streamlit مع إعادة استخدام نفس طبقة الخدمات.
5. **ما هي العمليات الأربع الأساسية (CRUD)؟** Create (إنشاء)، Read (قراءة)، Update (تحديث)، Delete (حذف)، وقد طُبقت كاملة على الأدوية والموردين.

### ثانياً: أسئلة لغة بايثون والبرمجة كائنية التوجه (OOP)
6. **ما الفرق بين الفئة (Class) والكائن (Object) مع مثال من المشروع؟** الفئة هي القالب مثل `class Medicine` أو `class SalesService`، والكائن هو نسخة حية منه في الذاكرة مثل `sales_service = SalesService(db)`.
7. **ما فائدة `@dataclass` في `entities.py`؟** تُنشئ تلقائياً `__init__` و`__repr__` لتمثيل الكيانات مثل `Supplier` و`CartItem` بكود نظيف ومختصر.
8. **ما دور الدالة البانية `__init__`؟** تهيئ الكائن عند إنشائه؛ مثلاً `DatabaseManager.__init__` يفتح الاتصال بقاعدة البيانات ويفعّل المفاتيح الأجنبية وينشئ الجداول.
9. **أين استخدمت الوراثة (Inheritance) في المشروع؟** `WebSQLiteDatabaseManager` يرث من `DatabaseManager` ليعيد استخدام بناء الجداول والبيانات الأولية مع إضافة أمان الخيوط للويب.
10. **ما هو التغليف (Encapsulation) وكيف طُبق؟** إخفاء التفاصيل الداخلية مثل `self._conn` و`self._lock` داخل `DatabaseManager` والسماح بالتعامل معها عبر واجهات منظمة مثل `transaction()`.
11. **ما هو Context Manager (`with`) وأين استخدمته؟** آلية تضمن فتح المورد وإغلاقه تلقائياً؛ استخدمنا `@contextmanager def transaction()` لضمان `COMMIT` أو `ROLLBACK` تلقائياً.
12. **ما الفرق بين `ValidationError` و `BusinessRuleError`؟** الأول لأخطاء صيغة المدخلات (مثل تاريخ خاطئ أو حقل فارغ)، والثاني لانتهاك قواعد الصيدلة (مثل بيع دواء منتهي أو حذف مورد مرتبط بأدوية).
13. **ما فائدة `Protocol` في `db_adapter.py`؟** يحدد عقداً برمجياً (`DatabaseBackend`) يصف الدوال المطلوبة من أي قاعدة بيانات دون ربط الكود بنوع قاعدة بيانات واحد.
14. **كيف تعاملت مع معالجة الأخطاء (`try / except`)؟** نلتقط الأخطاء في طبقة الواجهة ونترجمها للمستخدم عبر `localize_error()` مع منع انهيار البرنامج.
15. **لماذا استخدمنا Type Hints (`-> float`, `list[Medicine]`)؟** لزيادة وضوح الكود وتسهيل اكتشاف الأخطاء قبل التشغيل.

### ثالثاً: أسئلة قواعد البيانات و SQL
16. **لماذا اخترت SQLite بدلاً من MySQL أو PostgreSQL؟** لأنه قاعدة بيانات مدمجة بلا خادم خارجي، مثالية للتطبيقات المكتبية والنماذج السحابية السريعة وتدعم معاملات ACID.
17. **ما الفرق بين المفتاح الأساسي (Primary Key) والمفتاح الأجنبي (Foreign Key)؟** الأساسي يميز كل صف داخل جدوله (`medicines.id`)، والأجنبي يربط صفاً بجدول آخر (`medicines.supplier_id -> suppliers.id`).
18. **ما فائدة `PRAGMA foreign_keys = ON;` في SQLite؟** افتراضياً لا تفرض SQLite قيود المفتاح الأجنبي ما لم يتم تفعيل هذا الأمر عند كل اتصال.
19. **لماذا استخدمنا `ON DELETE RESTRICT` بين المورد والأدوية؟** لمنع حذف مورد ما زالت له أدوية مسجلة في المخزون حفاظاً على سلامة البيانات.
20. **لماذا حفظنا `medicine_name` و`batch_number` داخل `sale_items` رغم وجود `medicine_id`؟** كـ Snapshot حتى تبقى الفواتير التاريخية دقيقة إذا تغير اسم الدواء أو سعره لاحقاً.
21. **ما هي المعاملة (Database Transaction) ولماذا هي ضرورية في نقطة البيع؟** مجموعة أوامر SQL تُنفذ كوحدة واحدة لا تتجزأ (ACID). في البيع، إذا فشل خصم الصنف الثاني في السلة تتراجع قاعدة البيانات عن الفاتورة وعن خصم الصنف الأول بالكامل.
22. **لماذا استخدمنا `BEGIN IMMEDIATE` مع `isolation_level=None`؟** للتحكم اليدوي الصريح ببداية المعاملة ونهايتها ومنع تعارض الكتابة المتزامنة.
23. **كيف تمنع حقن SQL (SQL Injection)؟** باستخدام المعاملات (`?`) في جميع استعلامات `execute(sql, params)` وعدم دمج نصوص المستخدم في الاستعلام.
24. **ما فائدة الفهارس (`CREATE INDEX`) في الجداول؟** لتسريع البحث والاستعلام عن أسماء الأدوية وتواريخ الصلاحية والفواتير عند كبر حجم البيانات.
25. **ما وظيفة جدول `stock_adjustments`؟** سجل تدقيق غير قابل للتجاوز يحفظ كل حركة تغيير في المخزون مع السبب والوقت والمرجع.

### رابعاً: أسئلة منطق الصيدلية (POS & Expiry & Profit)
26. **ماذا يحدث عندما يحاول الكاشير بيع دواء منتهي الصلاحية؟** تمنعه دالة `validate_medicine_for_cart` في الواجهة، كما تمنعه `create_sale` داخل معاملة قاعدة البيانات وترفع `BusinessRuleError`.
27. **هل يُسمح ببيع الدواء في يوم انتهاء صلاحيته نفسه؟** لا؛ وفق دالة `is_expired` الشرط هو `exp <= ref`، أي يُحظر من يوم الانتهاء فصاعداً حرصاً على سلامة المريض.
28. **كيف يحسب نظام POS الإجمالي والخصم والضريبة؟** الإجمالي الفرعي = مجموع (السعر × الكمية)، ثم يُخصم الخصم النقدي، ثم تُحسب الضريبة على المبلغ الخاضع بعد الخصم، ثم يُجمعان للحصول على الإجمالي النهائي.
29. **كيف يحسب النظام صافي الربح (Net Profit)؟** يحسب الفرق بين سعر البيع وسعر التكلفة (`unit_price - cost_price`) لكل وحدة مباعة، ثم يطرح قيمة الخصم الممنوح على الفاتورة.
30. **كيف يدعم النظام مبدأ FEFO (First Expired, First Out)؟** عبر ترتيب الاستعلامات حسب `expiry_date ASC` وعرض نافذة تنبيه قابلة للضبط (15/30/60/90 يوماً) في صفحة التنبيهات.

### خامساً: أسئلة Streamlit ونسخة الويب والتوطين
31. **ماذا يحدث عند حدوث Rerun في Streamlit؟** يعيد Streamlit تنفيذ ملف `web_app/app.py` من السطر الأول للأسفل لتحديث الواجهة بناءً على مدخلات المستخدم الجديدة.
32. **كيف تحافظ على سلة المشتريات واللغة أثناء الـ Rerun؟** باستخدام `st.session_state` عبر `WebSessionController` لتخزين السلة واللغة المختارة ومفتاح الصفحة المستقر.
33. **كيف منعت تكرار الفواتير عند إعادة التشغيل السريع في POS؟** باستخدام رمز معاملة لمرة واحدة `rxcare_pos_tx_token`؛ بعد إتمام البيع يُسجل الرمز في `rxcare_processed_tx_tokens` وتُفرغ السلة ويُستبدل الرمز.
34. **لماذا احتجنا `check_same_thread=False` و `RLock` في نسخة الويب؟** لأن Streamlit يشغل الجلسات عبر خيوط متعددة، و`RLock` يمنع تداخل معاملات SQLite بين الخيوط.
35. **كيف حققت التبديل بين العربية (RTL) والإنجليزية (LTR) دون فقدان السلة؟** بفصل مفاتيح الصفحات (`NAV_PAGE_KEYS`) عن النصوص المترجمة في `i18n.py` وتطبيق CSS ديناميكي لـ `direction: rtl/ltr`.
36. **ما فائدة `@st.cache_resource` على `get_web_app_container()`؟** يضمن إنشاء اتصال قاعدة بيانات واحد ومشترك لعملية الخادم بدلاً من فتح اتصال جديد مع كل Rerun.
37. **كيف حللت مشكلة عرض الحروف العربية في رسوم Matplotlib؟** بإنشاء وحدة `web_app/core/arabic_shape.py` لتشكيل الحروف العربية بصيغة Presentation Forms-B وعكس الترتيب البصري لـ RTL مع بقاء الأرقام LTR.

### سادساً: أسئلة الاختبارات والأمان والقيود والنشر
38. **ما الفرق بين اختبار الوحدة (Unit Test) واختبار التكامل (Integration Test)؟** اختبار الوحدة يفحص دالة صغيرة منفردة (مثل حساب المجموع)، أما التكامل فيفحص تفاعل الخدمة مع قاعدة البيانات الحقيقية (مثل `create_sale` + خصم المخزون + سجل التدقيق).
39. **ما أبرز قيود النسخة المنشورة حالياً على Streamlit Cloud؟** ملف SQLite المحلي قد يُعاد ضبطه عند إعادة تشغيل الحاوية السحابية، ولا يوجد تسجيل دخول متعدد المستخدمين بعد.
40. **كيف يمكنك ترقية النظام لاستخدام قاعدة بيانات سحابية دائمة مستقبلاً؟** بتنفيذ فئة جديدة تطابق بروتوكول `DatabaseBackend` تتصل بـ PostgreSQL وربطها داخل `create_database_backend()` عند تمرير `RXCARE_WEB_DB_URL`.
41. **ما الفرق بين ملف `data/pharmacy.db` و `data/pharmacy_web.db`؟** الأول خاص بالنسخة المكتبية، والثاني معزول لنسخة الويب حتى لا تؤثر تجربة الويب على بيانات سطح المكتب.
42. **لماذا وضعنا `.streamlit/config.toml` في جذر المستودع وليس داخل `web_app/`؟** لأن Streamlit و Streamlit Community Cloud يقرآن ملف الإعدادات من جذر مجلد التشغيل فقط.

---

## الفصل الرابع عشر — نص العرض العملي أمام لجنة المناقشة

1. **لوحة التحكم (Dashboard) ومبدل اللغة (30 ثانية):**
   - *ما تقوله للجنة:* "هذا نظام RxCare بواجهة داكنة حديثة ودعم كامل للعربية RTL والإنجليزية LTR. نلاحظ في لوحة التحكم المؤشرات الفورية: عدد الأدوية، النواقص، المنتهية، مبيعات اليوم، وصافي الربح. سأبدّل اللغة الآن إلى الإنجليزية ثم أعود للعربية لإظهار مرونة الواجهة."
2. **إدارة الأدوية (Medicines) (45 ثانية):**
   - *ما تقوله للجنة:* "في صفحة إدارة الأدوية نستعرض التشغيلات مع تصفية بالتصنيف والبحث الفوري، وسأضيف الآن دواءً جديداً برقم تشغيلة فريد وسعر تكلفة وسعر بيع."
3. **إدارة المخزون (Inventory) (30 ثانية):**
   - *ما تقوله للجنة:* "هنا نراقب الأرصدة وقيمتها بالتكلفة والبيع، وننفذ توريداً (+10) لزيادة رصيد الصنف مع توثيق الحركة تلقائياً في تبويب سجل التدقيق."
4. **الموردون (Suppliers) (25 ثانية):**
   - *ما تقوله للجنة:* "في صفحة الموردين نعرض الموردين وعدد الأصناف المرتبطة بكل مورد، مع حماية مرجعية تمنع حذف أي مورد مرتبط بأدوية حالية."
5. **نقطة البيع (POS) وإثبات حظر المنتهي (60 ثانية):**
   - *ما تقوله للجنة:* "في نقطة البيع نختار أولاً تشغيلة منتهية الصلاحية لنثبت أن النظام يحظر إضافتها للسلة لحماية المريض. الآن نضيف دواءً صالحاً، نطبّق خصماً وضريبة، نلاحظ حساب صافي الربح التقديري مباشرة، ثم نتمم البيع ليُخصم المخزون ذرياً وتصدر الفاتورة."
6. **تنبيهات الصلاحية (Expiry Alerts) (30 ثانية):**
   - *ما تقوله للجنة:* "في صفحة التنبيهات نتابع الأدوية المنتهية وقريبة الانتهاء وننخفضة المخزون، ويمكننا شطب التشغيلة المنتهية أو توريد النواقص بضغطة زر."
7. **التقارير (Reports) (30 ثانية):**
   - *ما تقوله للجنة:* "أخيراً في صفحة التقارير نحدد النطاق الزمني لعرض مخططات الإيرادات والأرباح اليومية، أكثر الأدوية مبيعاً، تقييم المخزون حسب التصنيف، وتصدير البيانات بصيغة CSV."

---

## كيفية تحويل الدليل إلى PDF محلياً بجودة طباعة احترافية

### الطريقة الأولى (الأسهل — عبر المتصفح باستخدام ملف HTML المرفق)
1. افتح الملف **`docs/RxCare_Complete_Project_Guide.html`** في متصفح **Google Chrome** أو **Microsoft Edge**.
2. اضغط **`Ctrl + P`** (أو **`Cmd + P`** على macOS).
3. اختر الوجهة **`Save as PDF`**، فعّل **`Background graphics`**، واحفظه باسم **`RxCare_Complete_Project_Guide.pdf`**.

### الطريقة الثانية (عبر Pandoc + XeLaTeX من ملف Markdown)
```bash
pandoc docs/RxCare_Complete_Project_Guide.md \
  -o RxCare_Complete_Project_Guide.pdf \
  --pdf-engine=xelatex \
  -V dir=rtl \
  -V mainfont="Cairo" \
  --toc
```
