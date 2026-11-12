import jdatetime
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()


class Products(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)

    product_name_fa = db.Column(db.String(50), unique=True)
    product_name_en = db.Column(db.String(50), unique=True)
    product_name_ar = db.Column(db.String(50), unique=True)

    product_description_fa = db.Column(db.Text)
    product_description_en = db.Column(db.Text)
    product_description_ar = db.Column(db.Text)

    product_long_description_fa = db.Column(db.Text)
    product_long_description_en = db.Column(db.Text)
    product_long_description_ar = db.Column(db.Text)

    image_location = db.Column(db.String(200))

    # موجودی و فروش
    stock_quantity = db.Column(db.Integer, default=0, nullable=False)
    reserved_quantity = db.Column(db.Integer, default=0, nullable=False)
    stock_status = db.Column(db.String(100), default='موجود در انبار')
    is_active_for_sale = db.Column(db.Boolean, default=True)

    price = db.relationship('Price', backref='product', uselist=False, lazy=True)
    cart_items = db.relationship('CartItem', backref='product', lazy=True)
    order_items = db.relationship('OrderItem', backref='product', lazy=True)

    @property
    def available_quantity(self):
        return max(0, (self.stock_quantity or 0) - (self.reserved_quantity or 0))


class ProductFAQ(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category_fa = db.Column(db.String(100))
    category_en = db.Column(db.String(100))
    category_ar = db.Column(db.String(100))

    question_fa = db.Column(db.Text, nullable=False)
    question_en = db.Column(db.Text, nullable=False)
    question_ar = db.Column(db.Text, nullable=False)

    answer_fa = db.Column(db.Text, nullable=False)
    answer_en = db.Column(db.Text, nullable=False)
    answer_ar = db.Column(db.Text, nullable=False)


class Softes(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    slide_img_location = db.Column(db.String(200))


# نگه داشتن نام قبلی برای سازگاری
class Slides(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    slide_img_location = db.Column(db.String(200))


class Collaboration(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    phone = db.Column(db.String(20))
    collaboration_type = db.Column(db.String(150))
    collaboration_data = db.Column(db.Text)
    status = db.Column(db.String(50), default='جدید')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    admin_note = db.Column(db.Text)


class Admins(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(200), unique=True)
    password = db.Column(db.Text)
    access = db.Column(db.Text)
    last_login = db.Column(db.String(50), nullable=True)


class PageView(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    page_route = db.Column(db.String(100), nullable=False)
    jalali_date = db.Column(db.String(10), nullable=False)

    view_num_fa = db.Column(db.Integer, default=0)
    view_num_en = db.Column(db.Integer, default=0)
    view_num_ar = db.Column(db.Integer, default=0)

    @staticmethod
    def get_current_jalali_date():
        return jdatetime.date.today().strftime('%Y-%m-%d')


class Achievements(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    achievement_name_fa = db.Column(db.String(200))
    achievement_name_en = db.Column(db.String(200))
    achievement_name_ar = db.Column(db.String(200))

    achievement_code = db.Column(db.String(100))
    achievement_img = db.Column(db.String(1000))


class Price(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_price = db.Column(db.Integer, nullable=False)

    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), unique=True, nullable=False)


# ==================== تنظیمات سایت / حالت آزمایشی ====================

class SiteSetting(db.Model):
    """کلید-مقدار برای تنظیمات سیستم (حالت آزمایشی و غیره)"""
    __tablename__ = 'site_settings'

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False, index=True)
    value = db.Column(db.Text, nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # کلیدهای پیش‌فرض و معنی‌شان:
    # otp_test_mode          -> "1" / "0"  : OTP واقعی ارسال نشود؛ کد ثابت استفاده شود
    # otp_test_code          -> مثلاً "12345"
    # zarinpal_sandbox       -> "1" / "0"  : استفاده از درگاه آزمایشی زرین‌پال
    # payment_simulate       -> "1" / "0"  : امکان تأیید دستی/شبیه‌سازی پرداخت بدون درگاه
    # zarinpal_merchant_id   -> کد درگاه (اختیاری تا زمان دریافت)


def get_setting(key, default=None):
    row = SiteSetting.query.filter_by(key=key).first()
    if not row or row.value is None:
        return default
    return row.value


def get_setting_bool(key, default=False):
    val = get_setting(key, None)
    if val is None:
        return default
    return str(val).strip().lower() in ("1", "true", "yes", "on")


def set_setting(key, value):
    row = SiteSetting.query.filter_by(key=key).first()
    if not row:
        row = SiteSetting(key=key, value=str(value) if value is not None else None)
        db.session.add(row)
    else:
        row.value = str(value) if value is not None else None
        row.updated_at = datetime.utcnow()
    return row


def ensure_default_settings():
    """مقادیر پیش‌فرض حالت آزمایشی — فقط اگر کلید وجود نداشته باشد"""
    defaults = {
        "otp_test_mode": "1",          # فعلاً چون OTP واقعی نداریم، پیش‌فرض آزمایشی روشن
        "otp_test_code": "12345",
        "zarinpal_sandbox": "1",       # تا گرفتن درگاه واقعی، sandbox روشن
        "payment_simulate": "1",       # شبیه‌سازی پرداخت برای تست بدون زرین‌پال
        "zarinpal_merchant_id": "",
    }
    for k, v in defaults.items():
        if not SiteSetting.query.filter_by(key=k).first():
            db.session.add(SiteSetting(key=k, value=v))
    db.session.commit()


# ==================== بخش فروشگاه و مشتریان ====================

class Customer(db.Model, UserMixin):
    __tablename__ = 'customers'

    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(15), unique=True, nullable=False, index=True)
    password = db.Column(db.Text, nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)

    addresses = db.relationship('Address', backref='customer', lazy=True, cascade='all, delete-orphan')
    cart = db.relationship('Cart', backref='customer', uselist=False, lazy=True, cascade='all, delete-orphan')
    orders = db.relationship('Order', backref='customer', lazy=True)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class Address(db.Model):
    __tablename__ = 'addresses'

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)

    title = db.Column(db.String(50), default='منزل')
    province = db.Column(db.String(100), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    address_line = db.Column(db.Text, nullable=False)
    postal_code = db.Column(db.String(20))
    receiver_name = db.Column(db.String(150), nullable=False)
    receiver_phone = db.Column(db.String(15), nullable=False)
    is_default = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Cart(db.Model):
    __tablename__ = 'carts'

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), unique=True, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    items = db.relationship('CartItem', backref='cart', lazy=True, cascade='all, delete-orphan')

    @property
    def total_amount(self):
        return sum(item.subtotal for item in self.items)

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items)


class CartItem(db.Model):
    __tablename__ = 'cart_items'

    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey('carts.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1, nullable=False)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('cart_id', 'product_id', name='uq_cart_product'),
    )

    @property
    def unit_price(self):
        if self.product and self.product.price:
            return self.product.price.product_price
        return 0

    @property
    def subtotal(self):
        return self.unit_price * self.quantity


class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    order_code = db.Column(db.String(30), unique=True, nullable=False, index=True)

    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)

    status = db.Column(db.String(40), default='pending_payment')
    payment_status = db.Column(db.String(30), default='unpaid')

    zarinpal_authority = db.Column(db.String(100))
    zarinpal_ref_id = db.Column(db.String(100))

    shipping_cost = db.Column(db.Integer, default=0)
    items_total = db.Column(db.Integer, default=0)
    total_amount = db.Column(db.Integer, default=0)

    receiver_name = db.Column(db.String(150), nullable=False)
    receiver_phone = db.Column(db.String(15), nullable=False)
    province = db.Column(db.String(100), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    address_line = db.Column(db.Text, nullable=False)
    postal_code = db.Column(db.String(20))

    customer_note = db.Column(db.Text)
    admin_note = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    paid_at = db.Column(db.DateTime, nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')

    STATUS_LABELS = {
        'pending_payment': 'در انتظار پرداخت',
        'paid': 'پرداخت‌شده',
        'processing': 'در حال پردازش',
        'shipped': 'ارسال‌شده',
        'delivered': 'تحویل‌شده',
        'cancelled': 'لغو‌شده',
    }

    @property
    def status_label(self):
        return self.STATUS_LABELS.get(self.status, self.status)


class OrderItem(db.Model):
    __tablename__ = 'order_items'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=True)

    product_name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Integer, nullable=False)
    total_price = db.Column(db.Integer, nullable=False)
