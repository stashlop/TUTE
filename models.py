from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from sqlalchemy.sql import func

db = SQLAlchemy()

class Vendor(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(15), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    business_type = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'phone': self.phone,
            'location': self.location,
            'business_type': self.business_type
        }

class Supplier(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(15), unique=True, nullable=False)
    rating = db.Column(db.Float, default=4.5)
    hygiene_rating = db.Column(db.Float, default=4.0)
    verification_status = db.Column(db.Boolean, default=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'location': self.location,
            'phone': self.phone,
            'rating': self.rating,
            'hygiene_rating': self.hygiene_rating,
            'verification_status': self.verification_status
        }

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    unit = db.Column(db.String(20), nullable=False)
    current_price = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String(255), nullable=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'), nullable=False)
    supplier = db.relationship('Supplier', backref=db.backref('products', lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category,
            'unit': self.unit,
            'current_price': self.current_price,
            'image_url': self.image_url,
            'supplier_id': self.supplier_id,
            'supplier_name': self.supplier.name,
            'supplier_location': self.supplier.location
        }

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendor.id'), nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'), nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default='pending')
    order_type = db.Column(db.String(50), default='individual')
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    
    vendor = db.relationship('Vendor', backref=db.backref('orders', lazy=True))
    supplier = db.relationship('Supplier', backref=db.backref('orders', lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'supplier_name': self.supplier.name,
            'total_amount': self.total_amount,
            'status': self.status,
            'order_type': self.order_type,
            'created_at': self.created_at.strftime('%Y-%m-%d')
        }

class GroupOrder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(100), nullable=False)
    target_quantity = db.Column(db.Integer, nullable=False)
    current_quantity = db.Column(db.Integer, nullable=False)
    price_per_unit = db.Column(db.Float, nullable=False)
    participants_count = db.Column(db.Integer, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'product_name': self.product_name,
            'target_quantity': self.target_quantity,
            'current_quantity': self.current_quantity,
            'price_per_unit': self.price_per_unit,
            'participants_count': self.participants_count,
            'progress_percentage': (self.current_quantity / self.target_quantity) * 100
        }