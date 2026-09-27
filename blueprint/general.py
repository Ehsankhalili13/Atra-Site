import config
from models import *
from ext import *
from flask import Blueprint, render_template, redirect

app = Blueprint("general", __name__)

########## Persian Route ##########
@app.route('/')
def home():
    set_view("خانه", "fa")
    return render_template(
        "general/persian/index.html",
        slides = Slides.query.all(),
        sd=config.SITE_DESCRIPTION_FA,
        achievements = Achievements.query.all()
    )

@app.route("/about-us")
def about_us():
    return render_template("general/persian/about_us.html", sd=config.SITE_DESCRIPTION_FA)

@app.route('/products')
def products():
    set_view("محصولات", "fa")
    all_products = Products.query.all()
    return render_template("general/persian/products.html", p = all_products)

@app.route('/product/<pid>')
def product(pid):
    set_view("محصول", "fa")
    prd = Products.query.filter_by(id = pid).first()
    return render_template("general/persian/product.html", p = prd)

@app.route("/customer-service")
def customer_service():
    set_view("امور مشتریان", "fa")
    faqs = ProductFAQ.query.order_by(ProductFAQ.category_fa).all()
    return render_template("general/persian/customer.html", faqs = faqs)

@app.route("/collaboration")
def collaboration():
    set_view("همکاری با ما", "fa")
    return render_template("general/persian/collaboration.html")

@app.route("/ai")
def ai():
    set_view("هوش مصنوعی", "fa")
    return render_template("general/persian/ai.html")    


########## English Route ##########
@app.route('/en/')
def en_home():
    set_view("خانه", "en")
    return render_template(
        "general/english/index.html",
        slides = Slides.query.all(),
        sd=config.SITE_DESCRIPTION_EN,
        achievements = Achievements.query.all()
    )

@app.route("/en/about-us")
def en_about_us():
    return render_template("general/english/about_us.html", sd=config.SITE_DESCRIPTION_EN)

@app.route('/en/products')
def en_products():
    set_view("محصولات", "en")
    all_products = Products.query.all()
    return render_template("general/english/products.html", p = all_products)

@app.route('/en/product/<pid>')
def en_product(pid):
    set_view("محصول", "en")
    prd = Products.query.filter_by(id = pid).first()
    return render_template("general/english/product.html", p = prd)

@app.route("/en/customer-service")
def en_customer_service():
    set_view("امور مشتریان", "en")
    faqs = ProductFAQ.query.order_by(ProductFAQ.category_en).all()
    return render_template("general/english/customer.html", faqs = faqs)

@app.route("/en/collaboration")
def en_collaboration():
    return redirect("/en/")

@app.route("/en/ai")
def en_ai():
    set_view("هوش مصنوعی", "en")
    return render_template("general/english/ai.html")    


########## Arabic Route ##########
@app.route('/ar/')
def ar_home():
    set_view("خانه", "ar")
    return render_template(
        "general/arabic/index.html",
        slides = Slides.query.all(),
        sd=config.SITE_DESCRIPTION_AR,
        achievements = Achievements.query.all()
    )

@app.route("/ar/about-us")
def ar_about_us():
    return render_template("general/arabic/about_us.html", sd=config.SITE_DESCRIPTION_AR)

@app.route('/ar/products')
def ar_products():
    set_view("محصولات", "ar")
    all_products = Products.query.all()
    return render_template("general/arabic/products.html", p = all_products)

@app.route('/ar/product/<pid>')
def ar_product(pid):
    set_view("محصول", "ar")
    prd = Products.query.filter_by(id = pid).first()
    return render_template("general/arabic/product.html", p = prd)

@app.route("/ar/customer-service")
def ar_customer_service():
    set_view("امور مشتریان", "ar")
    faqs = ProductFAQ.query.order_by(ProductFAQ.category_ar).all()
    return render_template("general/arabic/customer.html", faqs = faqs)

@app.route("/ar/collaboration")
def ar_collaboration():
    return redirect("/en/")

@app.route("/ar/ai")
def ar_ai():
    set_view("هوش مصنوعی", "ar")
    return render_template("general/arabic/ai.html")    