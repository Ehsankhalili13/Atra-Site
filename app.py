import os
import json
import bcrypt
import jdatetime
from models import db, Admins, Products, Price, Collaboration
from blueprint import general, admin, customer
from flask import Flask, render_template, request, jsonify, session, make_response, Response
from flask_login import LoginManager, login_user

app = Flask(__name__)

# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:vKwn9XF3wKqhcHhInY9t@remote-pishgaman.runflare.com:31675/atra_site_db'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost:3306/atra_site_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.secret_key = 'j080wferyH4HUGJURH^b^btout&htb%htoiu(G'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'admin.login'
login_manager.login_message = 'لطفاً ابتدا وارد حساب کاربری خود شوید.'
login_manager.login_message_category = 'danger'

@login_manager.user_loader
def load_user(user_id):
    return Admins.query.get(int(user_id))

db.init_app(app)

app.register_blueprint(general.app)
app.register_blueprint(admin.app)
app.register_blueprint(customer.app)

with app.app_context():
    db.create_all()
    if not Admins.query.first():
        db.session.add(Admins(
            username="admin",
            password=bcrypt.hashpw("1415".encode("utf-8"), bcrypt.gensalt()).decode("utf-8"),
            access=json.dumps({"is_aa": True, "is_vsv": True, "is_mdu": True})
        ))
        db.session.commit()

STATIC_ROUTES = [
    '/', '/about-us', '/products', '/customer-service', '/collaboration',
    '/en', '/en/about-us', '/en/products', '/en/customer-service',
    '/ar', '/ar/about-us', '/ar/products', '/ar/customer-service'
]

@app.route('/sitemap.xml', methods=['GET'])
def sitemap():
    base_url = "https://atra-golfer.com"
    all_routes = list(STATIC_ROUTES)

    product_ids = [p[0] for p in Products.query.with_entities(Products.id).all()]

    for pid in product_ids:
        all_routes.append(f'/product/{pid}')
        all_routes.append(f'/en/product/{pid}')
        all_routes.append(f'/ar/product/{pid}')

    xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml_content += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'

    for route in all_routes:
        if route == '/':
            full_url = f"{base_url}/"
        else:
            clean_route = route.rstrip('/')
            full_url = f"{base_url}{clean_route}"

        xml_content += '  <url>\n'
        xml_content += f'    <loc>{full_url}</loc>\n'
        xml_content += '    <changefreq>weekly</changefreq>\n'
        xml_content += '    <priority>0.8</priority>\n'
        xml_content += '  </url>\n'

    xml_content += '</urlset>'

    response = make_response(xml_content)
    response.headers["Content-Type"] = "application/xml"
    return response

@app.route('/robots.txt')
def robots_txt():
    content = """User-agent: *
Disallow: /atra-site/admin/
Allow: /

Sitemap: https://atra-golfer.com/sitemap.xml
"""
    return Response(content, mimetype='text/plain')

########## API Route ##########
@app.route("/api/products")
def products_api():
    products = Products.query.all()
    return jsonify([
        {col.name: getattr(p, col.name) for col in p.__table__.columns}
        for p in products
    ])

@app.route("/api/product/<pid>")
def product_api(pid):
    product = Products.query.filter_by(id=pid).first()
    if not product:
        return jsonify({
            "status": "error",
            "message": "product not found."
        }), 404

    product_data = {col.name: getattr(product, col.name) for col in product.__table__.columns}
    return jsonify(product_data), 200

@app.route("/api/products/prices")
def all_price():
    prices = Price.query.all()
    result = [
        {col.name: getattr(price, col.name) for col in price.__table__.columns}
        for price in prices
    ]    
    return jsonify(result), 200

@app.route("/api/product/price/<pid>")
def product_price(pid):
    price = Price.query.filter_by(product_id=pid).first()
    if not price:
        return jsonify({
            "status": "error",
            "message": "price not found."
        }), 404

    product_data = {col.name: getattr(price, col.name) for col in price.__table__.columns}
    return jsonify(product_data), 200

@app.route("/api/collaboration-api", methods=["POST"])
def collaboration_api():
    try:
        data = request.get_json() or {}

        name = data.get("fullname")
        phone = data.get("phone")
        collaboration_type = data.get("collaborationType")
        collaboration_data = data.get("collaborationData")

        c = Collaboration(
            name=name,
            phone=phone,
            collaboration_type=collaboration_type,
            collaboration_data=json.dumps(collaboration_data)
        )

        db.session.add(c)
        db.session.commit()
        return jsonify(message="عملیات با موفقیت انجام شد.", type="success")
    except Exception as e:
        db.session.rollback()
        return jsonify(message="خطا در انجام عملیات.", type="danger", error=f"{e}"), 500

@app.route("/api/admin-login-api", methods=["POST"])
def ala():
    try:
        data = request.get_json()
        if not data:
            return jsonify(message="اطلاعاتی ارسال نشده است.", type="danger"), 400

        username = data.get("username")
        password = data.get("password")

        if not username or not password:
            return jsonify(message="نام کاربری و رمز عبور الزامی هستند.", type="danger"), 400

        user = Admins.query.filter_by(username=username).first()

        if user and bcrypt.checkpw(password.encode("utf-8"), user.password.encode("utf-8")):
            login_user(user)
            session["username"] = username
            return jsonify(message="ورود با موفقیت انجام شد.", type="success")
        else:
            return jsonify(message="نام کاربری یا رمز عبور اشتباه است.", type="danger"), 401

    except Exception as e:
        return jsonify(message="خطا در انجام عملیات.", type="danger", error=str(e)), 500

########## Handler Route ##########
@app.errorhandler(404)
def page_not_found(e):
    return render_template("sys_file/error.html", status_code=404, e=e), 404

@app.errorhandler(403)
def forbidden(e):
    return render_template("sys_file/error.html", status_code=403, e=e), 403

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")
