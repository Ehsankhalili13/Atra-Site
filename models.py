import jdatetime
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

    price = db.relationship('Price', backref='product', uselist=False, lazy=True)

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

class Slides(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    slide_img_location = db.Column(db.String(200))

class Collaboration(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    phone = db.Column(db.String(20))
    collaboration_type = db.Column(db.String(150))
    collaboration_data = db.Column(db.Text)

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