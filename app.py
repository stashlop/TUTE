from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import json
import random
from datetime import datetime, timedelta
import requests
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'vendorconnect_secret_key_2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///vendorconnect.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
CORS(app)

# Database Models
class Vendor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(15), unique=True, nullable=False)
    location = db.Column(db.String(200), nullable=False)
    business_type = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Supplier(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    rating = db.Column(db.Float, default=0.0)
    verification_status = db.Column(db.Boolean, default=False)
    hygiene_rating = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    current_price = db.Column(db.Float, nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'), nullable=False)
    stock_available = db.Column(db.Integer, default=0)
    unit = db.Column(db.String(20), default='kg')

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendor.id'), nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'), nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')
    order_type = db.Column(db.String(20), default='individual')  # individual or group
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    price_per_unit = db.Column(db.Float, nullable=False)

class GroupOrder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    target_quantity = db.Column(db.Float, nullable=False)
    current_quantity = db.Column(db.Float, default=0)
    price_per_unit = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class GroupOrderParticipant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    group_order_id = db.Column(db.Integer, db.ForeignKey('group_order.id'), nullable=False)
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendor.id'), nullable=False)
    quantity = db.Column(db.Float, nullable=False)

# Sample data for demonstration
def create_sample_data():
    # Create sample suppliers
    suppliers_data = [
        {'name': 'Krishna Mandi', 'phone': '9876543210', 'location': 'Mumbai Central', 'rating': 4.5, 'verification_status': True, 'hygiene_rating': 4.2},
        {'name': 'Fresh Farm Supplies', 'phone': '9876543211', 'location': 'Andheri West', 'rating': 4.8, 'verification_status': True, 'hygiene_rating': 4.6},
        {'name': 'Quality Vegetables', 'phone': '9876543212', 'location': 'Bandra East', 'rating': 4.3, 'verification_status': True, 'hygiene_rating': 4.0},
        {'name': 'Organic Market', 'phone': '9876543213', 'location': 'Juhu', 'rating': 4.7, 'verification_status': True, 'hygiene_rating': 4.8},
        {'name': 'Local Grocery Store', 'phone': '9876543214', 'location': 'Santacruz', 'rating': 4.1, 'verification_status': False, 'hygiene_rating': 3.8}
    ]
    
    for supplier_data in suppliers_data:
        supplier = Supplier(**supplier_data)
        db.session.add(supplier)
    
    db.session.commit()
    
    # Create sample products
    products_data = [
        {'name': 'Tomatoes', 'category': 'vegetables', 'current_price': 28.0, 'supplier_id': 1, 'stock_available': 500, 'unit': 'kg'},
        {'name': 'Onions', 'category': 'vegetables', 'current_price': 35.0, 'supplier_id': 1, 'stock_available': 300, 'unit': 'kg'},
        {'name': 'Potatoes', 'category': 'vegetables', 'current_price': 25.0, 'supplier_id': 2, 'stock_available': 400, 'unit': 'kg'},
        {'name': 'Cooking Oil', 'category': 'oils', 'current_price': 120.0, 'supplier_id': 3, 'stock_available': 100, 'unit': 'liter'},
        {'name': 'Rice', 'category': 'grains', 'current_price': 45.0, 'supplier_id': 4, 'stock_available': 200, 'unit': 'kg'},
        {'name': 'Lentils', 'category': 'pulses', 'current_price': 85.0, 'supplier_id': 5, 'stock_available': 150, 'unit': 'kg'},
        {'name': 'Milk', 'category': 'dairy', 'current_price': 60.0, 'supplier_id': 2, 'stock_available': 100, 'unit': 'liter'},
        {'name': 'Sugar', 'category': 'essentials', 'current_price': 45.0, 'supplier_id': 3, 'stock_available': 200, 'unit': 'kg'},
        {'name': 'Ice Cream Mix', 'category': 'ice_cream', 'current_price': 150.0, 'supplier_id': 4, 'stock_available': 50, 'unit': 'kg'},
        {'name': 'Vanilla Essence', 'category': 'ice_cream', 'current_price': 500.0, 'supplier_id': 5, 'stock_available': 20, 'unit': 'liter'},
        {'name': 'Chocolate Syrup', 'category': 'ice_cream', 'current_price': 300.0, 'supplier_id': 1, 'stock_available': 30, 'unit': 'liter'},
        {'name': 'Dry Fruits', 'category': 'ice_cream', 'current_price': 800.0, 'supplier_id': 2, 'stock_available': 10, 'unit': 'kg'}
    ]
    
    for product_data in products_data:
        product = Product(**product_data)
        db.session.add(product)
    
    db.session.commit()

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/vendor/login', methods=['GET', 'POST'])
def vendor_login():
    if request.method == 'POST':
        data = request.get_json()
        phone = data.get('phone')
        password = data.get('password')
        
        vendor = Vendor.query.filter_by(phone=phone).first()
        if vendor and check_password_hash(vendor.password_hash, password):
            session['vendor_id'] = vendor.id
            return jsonify({'success': True, 'message': 'Login successful'})
        else:
            return jsonify({'success': False, 'message': 'Invalid credentials'})
    
    return render_template('vendor_login.html')

@app.route('/vendor/register', methods=['GET', 'POST'])
def vendor_register():
    if request.method == 'POST':
        data = request.get_json()
        
        # Check if vendor already exists
        existing_vendor = Vendor.query.filter_by(phone=data.get('phone')).first()
        if existing_vendor:
            return jsonify({'success': False, 'message': 'Vendor already registered with this phone number'})
        
        # Create new vendor
        vendor = Vendor(
            name=data.get('name'),
            phone=data.get('phone'),
            location=data.get('location'),
            business_type=data.get('business_type'),
            password_hash=generate_password_hash(data.get('password'))
        )
        
        db.session.add(vendor)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Registration successful'})
    
    return render_template('vendor_register.html')

@app.route('/vendor/dashboard')
def vendor_dashboard():
    if 'vendor_id' not in session:
        return redirect(url_for('vendor_login'))
    
    vendor = Vendor.query.get(session['vendor_id'])
    return render_template('vendor_dashboard.html', vendor=vendor)

@app.route('/api/suppliers')
def get_suppliers():
    suppliers = Supplier.query.all()
    suppliers_data = []
    
    for supplier in suppliers:
        suppliers_data.append({
            'id': supplier.id,
            'name': supplier.name,
            'location': supplier.location,
            'rating': supplier.rating,
            'verification_status': supplier.verification_status,
            'hygiene_rating': supplier.hygiene_rating,
            'phone': supplier.phone
        })
    
    return jsonify(suppliers_data)

@app.route('/api/products')
def get_products():
    category = request.args.get('category', '')
    supplier_id = request.args.get('supplier_id', '')
    
    query = Product.query
    
    if category:
        query = query.filter_by(category=category)
    if supplier_id:
        query = query.filter_by(supplier_id=supplier_id)
    
    products = query.all()
    products_data = []
    
    for product in products:
        supplier = Supplier.query.get(product.supplier_id)
        products_data.append({
            'id': product.id,
            'name': product.name,
            'category': product.category,
            'current_price': product.current_price,
            'stock_available': product.stock_available,
            'unit': product.unit,
            'supplier_name': supplier.name,
            'supplier_location': supplier.location,
            'supplier_rating': supplier.rating
        })
    
    return jsonify(products_data)

@app.route('/api/group-orders')
def get_group_orders():
    group_orders = GroupOrder.query.filter_by(status='active').all()
    group_orders_data = []
    
    for group_order in group_orders:
        product = Product.query.get(group_order.product_id)
        participants_count = GroupOrderParticipant.query.filter_by(group_order_id=group_order.id).count()
        
        group_orders_data.append({
            'id': group_order.id,
            'product_name': product.name,
            'target_quantity': group_order.target_quantity,
            'current_quantity': group_order.current_quantity,
            'price_per_unit': group_order.price_per_unit,
            'participants_count': participants_count,
            'progress_percentage': (group_order.current_quantity / group_order.target_quantity) * 100
        })
    
    return jsonify(group_orders_data)

@app.route('/api/create-group-order', methods=['POST'])
def create_group_order():
    if 'vendor_id' not in session:
        return jsonify({'success': False, 'message': 'Please login first'})
    
    data = request.get_json()
    
    group_order = GroupOrder(
        product_id=data.get('product_id'),
        target_quantity=data.get('target_quantity'),
        price_per_unit=data.get('price_per_unit')
    )
    
    db.session.add(group_order)
    db.session.commit()
    
    # Add the creator as first participant
    participant = GroupOrderParticipant(
        group_order_id=group_order.id,
        vendor_id=session['vendor_id'],
        quantity=data.get('quantity')
    )
    
    db.session.add(participant)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Group order created successfully'})

@app.route('/api/join-group-order', methods=['POST'])
def join_group_order():
    if 'vendor_id' not in session:
        return jsonify({'success': False, 'message': 'Please login first'})
    
    data = request.get_json()
    
    # Check if already participating
    existing_participant = GroupOrderParticipant.query.filter_by(
        group_order_id=data.get('group_order_id'),
        vendor_id=session['vendor_id']
    ).first()
    
    if existing_participant:
        return jsonify({'success': False, 'message': 'Already participating in this group order'})
    
    participant = GroupOrderParticipant(
        group_order_id=data.get('group_order_id'),
        vendor_id=session['vendor_id'],
        quantity=data.get('quantity')
    )
    
    db.session.add(participant)
    
    # Update group order current quantity
    group_order = GroupOrder.query.get(data.get('group_order_id'))
    group_order.current_quantity += data.get('quantity')
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Joined group order successfully'})

@app.route('/api/price-alerts')
def get_price_alerts():
    # Simulate price alerts based on current market data
    alerts = [
        {
            'product': 'Tomatoes',
            'message': 'Aaj tomato ₹28/kg – lowest in Krishna Mandi',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M')
        },
        {
            'product': 'Onions',
            'message': 'Onion price dropped 15% in Fresh Farm Supplies',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M')
        },
        {
            'product': 'Potatoes',
            'message': 'Buy extra potatoes today – price may rise 20% tomorrow due to rains',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M')
        }
    ]
    
    return jsonify(alerts)

@app.route('/api/vendor/orders')
def get_vendor_orders():
    if 'vendor_id' not in session:
        return jsonify({'success': False, 'message': 'Please login first'})
    
    orders = Order.query.filter_by(vendor_id=session['vendor_id']).order_by(Order.created_at.desc()).all()
    orders_data = []
    
    for order in orders:
        supplier = Supplier.query.get(order.supplier_id)
        orders_data.append({
            'id': order.id,
            'supplier_name': supplier.name,
            'total_amount': order.total_amount,
            'status': order.status,
            'order_type': order.order_type,
            'created_at': order.created_at.strftime('%Y-%m-%d %H:%M')
        })
    
    return jsonify(orders_data)

@app.route('/api/place-order', methods=['POST'])
def place_order():
    if 'vendor_id' not in session:
        return jsonify({'success': False, 'message': 'Please login first'})
    
    data = request.get_json()
    
    order = Order(
        vendor_id=session['vendor_id'],
        supplier_id=data.get('supplier_id'),
        total_amount=data.get('total_amount'),
        order_type=data.get('order_type', 'individual')
    )
    
    db.session.add(order)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Order placed successfully'})

@app.route('/api/debug/products')
def debug_products():
    products = Product.query.all()
    products_data = []
    
    for product in products:
        supplier = Supplier.query.get(product.supplier_id)
        products_data.append({
            'id': product.id,
            'name': product.name,
            'category': product.category,
            'current_price': product.current_price,
            'stock_available': product.stock_available,
            'unit': product.unit,
            'supplier_name': supplier.name if supplier else 'Unknown'
        })
    
    return jsonify(products_data)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Only create sample data if database is empty
        if not Supplier.query.first():
            create_sample_data()
    
    app.run(debug=True, host='0.0.0.0', port=5000) 