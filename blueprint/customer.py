"""بخش حساب کاربری، سبد خرید و ثبت سفارش مشتری"""
from functools import wraps
from datetime import datetime
import random
import string

import bcrypt
import jdatetime
from flask import (
    Blueprint, render_template, request, jsonify,
    session, redirect
)

from models import (
    db, Customer, Cart, CartItem, Address, Order, OrderItem, Products
)

app = Blueprint("customer", __name__, url_prefix="/account")

# هزینه ارسال ثابت موقت (تومان) — بعداً قابل تنظیم از پنل
DEFAULT_SHIPPING_COST = 50000


def get_current_customer():
    cid = session.get("customer_id")
    if not cid:
        return None
    return Customer.query.get(cid)


def customer_login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("customer_id"):
            return redirect("/account/login")
        customer = get_current_customer()
        if not customer or not customer.is_active:
            session.pop("customer_id", None)
            return redirect("/account/login")
        return f(*args, **kwargs)
    return decorated


def _json_login_required(f):
    """برای APIها: به‌جای redirect، 401 برمی‌گرداند"""
    @wraps(f)
    def decorated(*args, **kwargs):
        customer = get_current_customer()
        if not customer or not customer.is_active:
            return jsonify({"status": "error", "message": "لطفاً وارد حساب شوید."}), 401
        return f(*args, **kwargs)
    return decorated


def _normalize_phone(phone: str) -> str:
    phone = (phone or "").strip().replace(" ", "").replace("-", "")
    if phone.startswith("+98"):
        phone = "0" + phone[3:]
    if phone.startswith("98") and len(phone) == 12:
        phone = "0" + phone[2:]
    return phone


def _get_or_create_cart(customer):
    cart = customer.cart
    if not cart:
        cart = Cart(customer_id=customer.id)
        db.session.add(cart)
        db.session.flush()
    return cart


def _generate_order_code():
    year = jdatetime.date.today().year
    suffix = "".join(random.choices(string.digits, k=6))
    code = f"ATR-{year}-{suffix}"
    while Order.query.filter_by(order_code=code).first():
        suffix = "".join(random.choices(string.digits, k=6))
        code = f"ATR-{year}-{suffix}"
    return code


# ---------- احراز هویت ----------

@app.route("/register", methods=["GET"])
def register_page():
    if session.get("customer_id"):
        return redirect("/account/profile")
    return render_template("general/persian/account/register.html")


@app.route("/login", methods=["GET"])
def login_page():
    if session.get("customer_id"):
        return redirect("/account/profile")
    return render_template("general/persian/account/login.html")


@app.route("/api/register", methods=["POST"])
def api_register():
    try:
        data = request.get_json() or {}
        phone = _normalize_phone(data.get("phone", ""))
        password = data.get("password") or ""
        first_name = (data.get("first_name") or "").strip()
        last_name = (data.get("last_name") or "").strip()
        email = (data.get("email") or "").strip() or None

        if not phone or len(phone) < 10:
            return jsonify({"status": "error", "message": "شماره موبایل معتبر وارد کنید."}), 400
        if not password or len(password) < 6:
            return jsonify({"status": "error", "message": "رمز عبور حداقل ۶ کاراکتر باشد."}), 400
        if not first_name or not last_name:
            return jsonify({"status": "error", "message": "نام و نام خانوادگی الزامی است."}), 400

        if Customer.query.filter_by(phone=phone).first():
            return jsonify({"status": "error", "message": "این شماره قبلاً ثبت شده است."}), 400

        hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        customer = Customer(
            phone=phone,
            password=hashed,
            first_name=first_name,
            last_name=last_name,
            email=email,
        )
        db.session.add(customer)
        db.session.flush()
        db.session.add(Cart(customer_id=customer.id))
        db.session.commit()

        session["customer_id"] = customer.id
        return jsonify({"status": "success", "message": "ثبت‌نام با موفقیت انجام شد."}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": "خطا در ثبت‌نام.", "detail": str(e)}), 500


@app.route("/api/login", methods=["POST"])
def api_login():
    try:
        data = request.get_json() or {}
        phone = _normalize_phone(data.get("phone", ""))
        password = data.get("password") or ""

        customer = Customer.query.filter_by(phone=phone).first()
        if not customer or not bcrypt.checkpw(password.encode("utf-8"), customer.password.encode("utf-8")):
            return jsonify({"status": "error", "message": "شماره موبایل یا رمز عبور اشتباه است."}), 401

        if not customer.is_active:
            return jsonify({"status": "error", "message": "حساب شما غیرفعال است."}), 403

        customer.last_login = datetime.utcnow()
        db.session.commit()
        session["customer_id"] = customer.id
        return jsonify({"status": "success", "message": "ورود موفق."}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": "خطا در ورود.", "detail": str(e)}), 500


@app.route("/logout")
def logout():
    session.pop("customer_id", None)
    return redirect("/")


@app.route("/profile")
@customer_login_required
def profile():
    customer = get_current_customer()
    orders = Order.query.filter_by(customer_id=customer.id).order_by(Order.id.desc()).limit(20).all()
    addresses = Address.query.filter_by(customer_id=customer.id).all()
    return render_template(
        "general/persian/account/profile.html",
        customer=customer,
        orders=orders,
        addresses=addresses,
    )


@app.route("/api/profile", methods=["PUT"])
@customer_login_required
def api_update_profile():
    try:
        customer = get_current_customer()
        data = request.get_json() or {}

        first_name = (data.get("first_name") or "").strip()
        last_name = (data.get("last_name") or "").strip()
        email = (data.get("email") or "").strip() or None

        if not first_name or not last_name:
            return jsonify({"status": "error", "message": "نام و نام خانوادگی الزامی است."}), 400

        customer.first_name = first_name
        customer.last_name = last_name
        customer.email = email

        new_password = data.get("new_password") or ""
        if new_password:
            if len(new_password) < 6:
                return jsonify({"status": "error", "message": "رمز جدید حداقل ۶ کاراکتر باشد."}), 400
            customer.password = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

        db.session.commit()
        return jsonify({"status": "success", "message": "اطلاعات بروزرسانی شد."}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


# ---------- سبد خرید ----------

@app.route("/cart")
@customer_login_required
def cart_page():
    customer = get_current_customer()
    cart = _get_or_create_cart(customer)
    db.session.commit()
    return render_template("general/persian/account/cart.html", customer=customer, cart=cart)


@app.route("/api/cart", methods=["GET"])
@_json_login_required
def api_cart():
    customer = get_current_customer()
    cart = _get_or_create_cart(customer)
    db.session.commit()

    items = []
    for it in cart.items:
        p = it.product
        items.append({
            "id": it.id,
            "product_id": it.product_id,
            "name": p.product_name_fa if p else "—",
            "image": p.image_location if p else "",
            "quantity": it.quantity,
            "unit_price": it.unit_price,
            "subtotal": it.subtotal,
            "available": p.available_quantity if p else 0,
            "stock_status": p.stock_status if p else "",
        })

    return jsonify({
        "status": "success",
        "items": items,
        "total_amount": cart.total_amount,
        "total_items": cart.total_items,
        "shipping_cost": DEFAULT_SHIPPING_COST,
    })


@app.route("/api/cart/add", methods=["POST"])
@_json_login_required
def api_cart_add():
    try:
        customer = get_current_customer()
        data = request.get_json() or {}
        product_id = int(data.get("product_id") or 0)
        quantity = int(data.get("quantity") or 1)

        if quantity < 1:
            return jsonify({"status": "error", "message": "تعداد نامعتبر است."}), 400

        product = Products.query.get(product_id)
        if not product or not product.is_active_for_sale:
            return jsonify({"status": "error", "message": "محصول یافت نشد یا قابل فروش نیست."}), 404

        if product.available_quantity < 1:
            return jsonify({"status": "error", "message": "موجودی این محصول کافی نیست."}), 400

        cart = _get_or_create_cart(customer)
        item = CartItem.query.filter_by(cart_id=cart.id, product_id=product_id).first()

        new_qty = quantity if not item else item.quantity + quantity
        if new_qty > product.available_quantity:
            return jsonify({
                "status": "error",
                "message": f"حداکثر {product.available_quantity} عدد قابل سفارش است."
            }), 400

        if item:
            item.quantity = new_qty
        else:
            item = CartItem(cart_id=cart.id, product_id=product_id, quantity=quantity)
            db.session.add(item)

        cart.updated_at = datetime.utcnow()
        db.session.commit()

        return jsonify({
            "status": "success",
            "message": "به سبد اضافه شد.",
            "total_items": cart.total_items,
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/cart/update", methods=["PUT"])
@_json_login_required
def api_cart_update():
    try:
        customer = get_current_customer()
        data = request.get_json() or {}
        item_id = int(data.get("item_id") or 0)
        quantity = int(data.get("quantity") or 0)

        cart = _get_or_create_cart(customer)
        item = CartItem.query.filter_by(id=item_id, cart_id=cart.id).first()
        if not item:
            return jsonify({"status": "error", "message": "آیتم یافت نشد."}), 404

        if quantity < 1:
            db.session.delete(item)
        else:
            product = item.product
            if product and quantity > product.available_quantity:
                return jsonify({
                    "status": "error",
                    "message": f"حداکثر {product.available_quantity} عدد قابل سفارش است."
                }), 400
            item.quantity = quantity

        cart.updated_at = datetime.utcnow()
        db.session.commit()
        return jsonify({
            "status": "success",
            "message": "سبد بروزرسانی شد.",
            "total_amount": cart.total_amount,
            "total_items": cart.total_items,
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/cart/remove", methods=["DELETE"])
@_json_login_required
def api_cart_remove():
    try:
        customer = get_current_customer()
        data = request.get_json() or {}
        item_id = int(data.get("item_id") or 0)

        cart = _get_or_create_cart(customer)
        item = CartItem.query.filter_by(id=item_id, cart_id=cart.id).first()
        if not item:
            return jsonify({"status": "error", "message": "آیتم یافت نشد."}), 404

        db.session.delete(item)
        cart.updated_at = datetime.utcnow()
        db.session.commit()
        return jsonify({
            "status": "success",
            "message": "حذف شد.",
            "total_amount": cart.total_amount,
            "total_items": cart.total_items,
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


# ---------- ثبت سفارش ----------

@app.route("/checkout")
@customer_login_required
def checkout_page():
    customer = get_current_customer()
    cart = _get_or_create_cart(customer)
    if not cart.items:
        return redirect("/account/cart")
    addresses = Address.query.filter_by(customer_id=customer.id).all()
    return render_template(
        "general/persian/account/checkout.html",
        customer=customer,
        cart=cart,
        addresses=addresses,
        shipping_cost=DEFAULT_SHIPPING_COST,
    )


@app.route("/api/checkout", methods=["POST"])
@_json_login_required
def api_checkout():
    """ثبت سفارش و رزرو موجودی — پرداخت در مرحله بعد (زرین‌پال)"""
    try:
        customer = get_current_customer()
        cart = _get_or_create_cart(customer)

        if not cart.items:
            return jsonify({"status": "error", "message": "سبد خرید خالی است."}), 400

        data = request.get_json() or {}
        receiver_name = (data.get("receiver_name") or "").strip()
        receiver_phone = _normalize_phone(data.get("receiver_phone", ""))
        province = (data.get("province") or "").strip()
        city = (data.get("city") or "").strip()
        address_line = (data.get("address_line") or "").strip()
        postal_code = (data.get("postal_code") or "").strip()
        customer_note = (data.get("customer_note") or "").strip()

        if not all([receiver_name, receiver_phone, province, city, address_line]):
            return jsonify({"status": "error", "message": "لطفاً تمام فیلدهای آدرس را پر کنید."}), 400

        # بررسی موجودی و محاسبه
        items_total = 0
        line_items = []
        for it in cart.items:
            product = Products.query.with_for_update().get(it.product_id)
            if not product or not product.is_active_for_sale:
                return jsonify({"status": "error", "message": f"محصول «{it.product_id}» دیگر قابل فروش نیست."}), 400
            if it.quantity > product.available_quantity:
                return jsonify({
                    "status": "error",
                    "message": f"موجودی «{product.product_name_fa}» کافی نیست."
                }), 400

            unit_price = product.price.product_price if product.price else 0
            total_price = unit_price * it.quantity
            items_total += total_price
            line_items.append({
                "product": product,
                "quantity": it.quantity,
                "unit_price": unit_price,
                "total_price": total_price,
                "name": product.product_name_fa or "محصول",
            })

        shipping = DEFAULT_SHIPPING_COST
        total_amount = items_total + shipping

        order = Order(
            order_code=_generate_order_code(),
            customer_id=customer.id,
            status="pending_payment",
            payment_status="unpaid",
            shipping_cost=shipping,
            items_total=items_total,
            total_amount=total_amount,
            receiver_name=receiver_name,
            receiver_phone=receiver_phone,
            province=province,
            city=city,
            address_line=address_line,
            postal_code=postal_code,
            customer_note=customer_note or None,
        )
        db.session.add(order)
        db.session.flush()

        for li in line_items:
            db.session.add(OrderItem(
                order_id=order.id,
                product_id=li["product"].id,
                product_name=li["name"],
                quantity=li["quantity"],
                unit_price=li["unit_price"],
                total_price=li["total_price"],
            ))
            # رزرو موجودی
            li["product"].reserved_quantity = (li["product"].reserved_quantity or 0) + li["quantity"]

        # خالی کردن سبد
        for it in list(cart.items):
            db.session.delete(it)

        db.session.commit()

        return jsonify({
            "status": "success",
            "message": "سفارش ثبت شد.",
            "order_code": order.order_code,
            "order_id": order.id,
            "total_amount": total_amount,
            # در مرحله بعد به درگاه هدایت می‌شود
            "redirect": f"/account/order/{order.id}/pay",
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": "خطا در ثبت سفارش.", "detail": str(e)}), 500


@app.route("/order/<int:order_id>/pay")
@customer_login_required
def order_pay_placeholder(order_id):
    """صفحه موقت قبل از اتصال زرین‌پال"""
    customer = get_current_customer()
    order = Order.query.filter_by(id=order_id, customer_id=customer.id).first_or_404()
    return render_template(
        "general/persian/account/pay.html",
        customer=customer,
        order=order,
    )
