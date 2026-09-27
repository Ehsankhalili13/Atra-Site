import json
from functools import wraps
from flask import session, abort
from flask_login import current_user
from models import db, PageView

def set_view(route, lang='fa'):
    if not session.get("page-not-view"):
        today_str = PageView.get_current_jalali_date()
        view_record = PageView.query.filter_by(page_route=route, jalali_date=today_str).first()

        if not view_record:
            view_record = PageView(
                page_route=route,
                jalali_date=today_str,
                view_num_fa=0,
                view_num_en=0,
                view_num_ar=0
            )
            db.session.add(view_record)

        if lang == 'fa':
            view_record.view_num_fa += 1
        elif lang == 'en':
            view_record.view_num_en += 1
        elif lang == 'ar':
            view_record.view_num_ar += 1

        db.session.commit()

def permission_required(permission_key):
    """دیکوریتور بررسی مجوزهای مدیریت"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
                
            user_access = json.loads(current_user.access) if current_user.access else {}
            has_permission = bool(user_access.get("is_aa") or user_access.get(permission_key))
            
            if not has_permission:
                abort(403)
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator