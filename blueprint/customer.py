"""بخش حساب کاربری مشتری فروشگاه"""
from functools import wraps
from datetime import datetime

import bcrypt
from flask import (
    Blueprint, render_template, request, jsonify,
    session, redirect, url_for
)

from models import db, Customer, Cart, Address, Order

app = Blueprint("customer", __name__, url_prefix="/account")


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


def _normalize_phone(phone: str) -> str:
    phone = (phone or "").strip().replace(" ", "").replace("-", "")
    if phone.startswith("+98"):
        phone = "0" + phone[3:]
    if phone.startswith("98") and len(phone) == 12:
        phone = "0" + phone[2:]
    return phone


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

        # سبد خرید خالی
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
