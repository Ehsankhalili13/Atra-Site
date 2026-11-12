import json
import bcrypt
import jdatetime
from datetime import datetime
from models import db, Admins, PageView, Collaboration
from config import PERMISSIONS
from ext import permission_required
from flask import Blueprint, render_template, redirect, session, jsonify, request
from flask_login import login_required, logout_user, current_user

app = Blueprint("admin", __name__, url_prefix="/atra-site/admin")


def _to_jalali_str(dt):
    """تبدیل datetime میلادی به رشته شمسی خوانا"""
    if not dt:
        return "—"
    try:
        j = jdatetime.datetime.fromgregorian(datetime=dt)
        return j.strftime("%Y/%m/%d %H:%M")
    except Exception:
        return str(dt)


@app.route("/login")
def login():
    if current_user.is_authenticated:
        return redirect("/atra-site/admin")
    return render_template("admin/login.html")


@app.route("/")
def admin():
    return redirect("/atra-site/admin/home")


@app.route("/home")
@login_required
def admin_home():
    today = jdatetime.date.today()
    today_str = today.strftime("%Y-%m-%d")
    seven_days_str = (today - jdatetime.timedelta(days=7)).strftime("%Y-%m-%d")
    month_str = today.strftime("%Y-%m-01")
    year_str = today.strftime("%Y-01-01")

    stats_raw = (
        db.session.query(
            PageView.page_route,
            db.func.sum(db.case((PageView.jalali_date == today_str, PageView.view_num_fa), else_=0)).label("today_fa"),
            db.func.sum(db.case((PageView.jalali_date == today_str, PageView.view_num_en), else_=0)).label("today_en"),
            db.func.sum(db.case((PageView.jalali_date == today_str, PageView.view_num_ar), else_=0)).label("today_ar"),
            db.func.sum(db.case((PageView.jalali_date >= seven_days_str, PageView.view_num_fa), else_=0)).label("seven_fa"),
            db.func.sum(db.case((PageView.jalali_date >= seven_days_str, PageView.view_num_en), else_=0)).label("seven_en"),
            db.func.sum(db.case((PageView.jalali_date >= seven_days_str, PageView.view_num_ar), else_=0)).label("seven_ar"),
            db.func.sum(db.case((PageView.jalali_date >= month_str, PageView.view_num_fa), else_=0)).label("month_fa"),
            db.func.sum(db.case((PageView.jalali_date >= month_str, PageView.view_num_en), else_=0)).label("month_en"),
            db.func.sum(db.case((PageView.jalali_date >= month_str, PageView.view_num_ar), else_=0)).label("month_ar"),
            db.func.sum(db.case((PageView.jalali_date >= year_str, PageView.view_num_fa), else_=0)).label("year_fa"),
            db.func.sum(db.case((PageView.jalali_date >= year_str, PageView.view_num_en), else_=0)).label("year_en"),
            db.func.sum(db.case((PageView.jalali_date >= year_str, PageView.view_num_ar), else_=0)).label("year_ar"),
            db.func.sum(PageView.view_num_fa).label("all_fa"),
            db.func.sum(PageView.view_num_en).label("all_en"),
            db.func.sum(PageView.view_num_ar).label("all_ar")
        )
        .group_by(PageView.page_route)
        .all()
    )

    views_data = [
        {
            "route": row.page_route,
            "today_fa": int(row.today_fa or 0),
            "today_en": int(row.today_en or 0),
            "today_ar": int(row.today_ar or 0),
            "seven_fa": int(row.seven_fa or 0),
            "seven_en": int(row.seven_en or 0),
            "seven_ar": int(row.seven_ar or 0),
            "month_fa": int(row.month_fa or 0),
            "month_en": int(row.month_en or 0),
            "month_ar": int(row.month_ar or 0),
            "year_fa": int(row.year_fa or 0),
            "year_en": int(row.year_en or 0),
            "year_ar": int(row.year_ar or 0),
            "all_fa": int(row.all_fa or 0),
            "all_en": int(row.all_en or 0),
            "all_ar": int(row.all_ar or 0),
        }
        for row in stats_raw
    ]

    chart_data_raw = (
        db.session.query(
            PageView.jalali_date,
            db.func.sum(PageView.view_num_fa).label("fa_views"),
            db.func.sum(PageView.view_num_en).label("en_views"),
            db.func.sum(PageView.view_num_ar).label("ar_views")
        )
        .group_by(PageView.jalali_date)
        .order_by(PageView.jalali_date.asc())
        .all()
    )

    chart_data = [
        {
            "date": row.jalali_date,
            "fa": int(row.fa_views or 0),
            "en": int(row.en_views or 0),
            "ar": int(row.ar_views or 0),
        }
        for row in chart_data_raw
    ]

    first_record = db.session.query(db.func.min(PageView.jalali_date)).scalar()
    start_year = int(first_record.split("-")[0]) if first_record else today.year

    user_access = json.loads(current_user.access) if current_user.access else {}
    user_access_level = bool(user_access.get("is_aa") or user_access.get("is_vsv"))

    suggestions = Collaboration.query.order_by(Collaboration.id.desc()).limit(5).all()

    return render_template(
        "admin/dashboard.html",
        usl=user_access_level,
        views_data=views_data,
        chart_data=chart_data,
        suggestions=suggestions,
        current_year=today.year,
        current_month=today.month,
        current_day=today.day,
        start_year=start_year
    )


# --- صفحه و APIهای درخواست‌های همکاری ---

@app.route("/collaborations")
@login_required
def collaborations_page():
    return render_template("admin/collaborations.html")


@app.route("/api/collaborations", methods=["GET"])
@login_required
def list_collaborations():
    try:
        items = Collaboration.query.order_by(Collaboration.id.desc()).all()
        data = []
        for c in items:
            data.append({
                "id": c.id,
                "name": c.name,
                "phone": c.phone,
                "collaboration_type": c.collaboration_type,
                "collaboration_data": c.collaboration_data,
                "status": c.status or "جدید",
                "admin_note": c.admin_note or "",
                "created_at_fa": _to_jalali_str(c.created_at),
            })
        return jsonify({"status": "success", "data": data}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/collaborations/<int:collab_id>", methods=["PUT"])
@login_required
def update_collaboration(collab_id):
    try:
        c = Collaboration.query.get(collab_id)
        if not c:
            return jsonify({"status": "error", "message": "درخواست یافت نشد."}), 404

        data = request.get_json() or {}
        if "status" in data:
            c.status = data["status"]
        if "admin_note" in data:
            c.admin_note = data["admin_note"]

        db.session.commit()
        return jsonify({"status": "success", "message": "با موفقیت ذخیره شد."}), 200
    except Exception:
        db.session.rollback()
        return jsonify({"status": "error", "message": "خطا در ذخیره‌سازی."}), 500


@app.route("/api/collaborations/<int:collab_id>", methods=["DELETE"])
@login_required
def delete_collaboration(collab_id):
    try:
        c = Collaboration.query.get(collab_id)
        if not c:
            return jsonify({"status": "error", "message": "درخواست یافت نشد."}), 404

        db.session.delete(c)
        db.session.commit()
        return jsonify({"status": "success", "message": "حذف شد."}), 200
    except Exception:
        db.session.rollback()
        return jsonify({"status": "error", "message": "خطا در حذف."}), 500


# --- APIهای قدیمی داشبورد برای پیشنهادها (حفظ سازگاری) ---

@app.route("/api/suggestions/<int:sug_id>", methods=["GET"])
@login_required
def get_suggestion_detail(sug_id):
    sug = Collaboration.query.get_or_404(sug_id)
    return jsonify({
        "status": "success",
        "data": {
            "id": sug.id,
            "name": sug.name or "نامشخص",
            "phone": sug.phone or "ثبت نشده",
            "type": sug.collaboration_type or "تعیین نشده",
            "data": sug.collaboration_data or "توضیحاتی وجود ندارد."
        }
    }), 200


@app.route("/api/suggestions/<int:sug_id>", methods=["DELETE"])
@login_required
def delete_suggestion(sug_id):
    try:
        sug = Collaboration.query.get(sug_id)
        if not sug:
            return jsonify({"status": "error", "message": "پیشنهاد مورد نظر یافت نشد."}), 404

        db.session.delete(sug)
        db.session.commit()
        return jsonify({"status": "success", "message": "پیشنهاد همکاری با موفقیت حذف شد."}), 200
    except Exception:
        db.session.rollback()
        return jsonify({"status": "error", "message": "خطا در حذف پیشنهاد."}), 500


@app.route("/manage-admin")
@login_required
@permission_required("is_mdu")
def manage_admin():
    return render_template("admin/admins.html", permissions=PERMISSIONS)


@app.route("/api/admins", methods=["GET"])
@login_required
def get_admins():
    try:
        current_access = json.loads(current_user.access) if current_user.access else {}
        is_super = bool(current_access.get("is_aa"))

        admins = Admins.query.all() if is_super else [current_user]

        admin_list = []
        for admin in admins:
            access_data = json.loads(admin.access) if admin.access else {}
            admin_is_super = bool(access_data.get("is_aa"))

            admin_list.append({
                "id": admin.id,
                "username": admin.username,
                "access": access_data,
                "role": "superadmin" if admin_is_super else "admin",
                "last_login": admin.last_login or "ثبت نشده",
                "is_current_user": admin.id == current_user.id
            })

        all_admins = Admins.query.all()
        all_admins_count = len(all_admins)
        all_super_count = sum(1 for a in all_admins if json.loads(a.access or '{}').get('is_aa'))

        return jsonify({
            "status": "success",
            "stats": {
                "total": all_admins_count,
                "active": all_admins_count,
                "super_admins": all_super_count
            },
            "data": admin_list,
            "permissions_config": PERMISSIONS,
            "current_user_is_super": is_super
        }), 200
    except Exception:
        return jsonify({"status": "error", "message": "خطا در دریافت اطلاعات."}), 500


@app.route("/api/add-admin", methods=["POST"])
@login_required
def add_admin_api():
    try:
        current_access = json.loads(current_user.access) if current_user.access else {}

        if not current_access.get("is_aa") and not current_access.get("is_mdu"):
            return jsonify({"message": "شما مجوز ایجاد مدیر جدید را ندارید.", "type": "danger"}), 403

        data = request.get_json() or {}
        username = data.get("username")
        password = data.get("password")
        permissions = data.get("permissions", {})

        if not username or not password:
            return jsonify({"message": "نام کاربری و رمز عبور الزامی است.", "type": "danger"}), 400

        if Admins.query.filter_by(username=username).first():
            return jsonify({"message": "این نام کاربری قبلاً ثبت شده است.", "type": "danger"}), 400

        if not current_access.get("is_aa"):
            permissions["is_aa"] = False

        hashed_pw = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

        new_admin = Admins(
            username=username,
            password=hashed_pw,
            access=json.dumps(permissions)
        )

        db.session.add(new_admin)
        db.session.commit()

        return jsonify({"message": "مدیر جدید با موفقیت ایجاد شد.", "type": "success"}), 201
    except Exception:
        db.session.rollback()
        return jsonify({"message": "خطا در ثبت اطلاعات.", "type": "danger"}), 500


@app.route("/api/edit-admin/<int:admin_id>", methods=["PUT"])
@login_required
def edit_admin_api(admin_id):
    try:
        target_admin = Admins.query.get(admin_id)
        if not target_admin:
            return jsonify({"message": "کاربر مورد نظر یافت نشد.", "type": "danger"}), 404

        current_access = json.loads(current_user.access) if current_user.access else {}
        target_access = json.loads(target_admin.access) if target_admin.access else {}

        is_current_super = bool(current_access.get("is_aa"))
        is_target_super = bool(target_access.get("is_aa"))

        if not is_current_super and current_user.id != target_admin.id:
            return jsonify({"message": "شما تنها اجازه ویرایش حساب خود را دارید.", "type": "danger"}), 403

        if is_current_super and is_target_super and current_user.id != target_admin.id:
            return jsonify({"message": "مدیران ارشد نمی‌توانند اطلاعات یکدیگر را ویرایش کنند.", "type": "danger"}), 403

        data = request.get_json() or {}
        new_username = data.get("username")
        new_password = data.get("password")
        new_permissions = data.get("permissions", {})

        if new_username and new_username != target_admin.username:
            if Admins.query.filter_by(username=new_username).first():
                return jsonify({"message": "این نام کاربری توسط شخص دیگری ثبت شده است.", "type": "danger"}), 400
            target_admin.username = new_username

        if new_password:
            target_admin.password = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

        if is_current_super and current_user.id != target_admin.id:
            target_admin.access = json.dumps(new_permissions)

        db.session.commit()
        return jsonify({"message": "اطلاعات مدیر با موفقیت بروزرسانی شد.", "type": "success"}), 200

    except Exception:
        db.session.rollback()
        return jsonify({"message": "خطا در بروزرسانی اطلاعات.", "type": "danger"}), 500


@app.route("/api/delete-admin/<int:admin_id>", methods=["DELETE"])
@login_required
def delete_admin_api(admin_id):
    try:
        target_admin = Admins.query.get(admin_id)
        if not target_admin:
            return jsonify({"message": "کاربر مورد نظر یافت نشد.", "type": "danger"}), 404

        current_access = json.loads(current_user.access) if current_user.access else {}
        target_access = json.loads(target_admin.access) if target_admin.access else {}

        is_current_super = bool(current_access.get("is_aa"))
        is_target_super = bool(target_access.get("is_aa"))

        if current_user.id == target_admin.id:
            return jsonify({"message": "شما نمی‌توانید حساب کاربری جاری خود را حذف کنید.", "type": "danger"}), 400

        if not is_current_super:
            return jsonify({"message": "شما مجوز حذف کاربران را ندارید.", "type": "danger"}), 403

        if is_current_super and is_target_super:
            return jsonify({"message": "شما نمی‌توانید حساب مدیر ارشد دیگری را حذف کنید.", "type": "danger"}), 403

        db.session.delete(target_admin)
        db.session.commit()
        return jsonify({"message": "حساب کاربری با موفقیت حذف شد.", "type": "success"}), 200
    except Exception:
        db.session.rollback()
        return jsonify({"message": "خطا در حذف کاربر.", "type": "danger"}), 500


@app.route("/page-not-view")
def page_not_view():
    session["page-not-view"] = True
    return "Done!"


@app.route("/page-view")
def page_view():
    session.pop("page-not-view", None)
    return "Done!"


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/atra-site/admin/login")
