import os
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from collections import defaultdict
from models import db, Vendor, Product, Supplier, Order, GroupOrder
from database import init_db

# --- Product Recommendation Logic ---
PRODUCT_RECOMMENDATIONS = {
    'chaat': ['Potatoes', 'Onions', 'Chickpeas (Chana)', 'Tomatoes'],
    'dosa': ['Basmati Rice', 'Onions', 'Potatoes', 'Sunflower Oil'],
    'samosa': ['Potatoes', 'Onions', 'Sunflower Oil'],
    'vada_pav': ['Potatoes', 'Chickpeas (Chana)'],
    'tea': ['Sunflower Oil'], # Assuming oil for snacks
    'juice': ['Tomatoes'], # Can be used in some juices
    'ice_cream': [],
    'other': ['Tomatoes', 'Onions', 'Potatoes', 'Sunflower Oil']
}

# --- App Configuration ---
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///vendorconnect.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --- Extensions Initialization ---
db.init_app(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'vendor_login_page'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return Vendor.query.get(int(user_id))

# --- Page Rendering Routes ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/vendor/login', methods=['GET'])
def vendor_login_page():
    if current_user.is_authenticated:
        return redirect(url_for('vendor_dashboard'))
    return render_template('vendor_login.html')

@app.route('/vendor/register', methods=['GET'])
def vendor_register_page():
    if current_user.is_authenticated:
        return redirect(url_for('vendor_dashboard'))
    return render_template('vendor_register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('vendor_login_page'))

@app.route('/vendor/dashboard')
@login_required
def vendor_dashboard():
    return render_template('vendor_dashboard.html', vendor=current_user)

# --- API Authentication Routes ---

@app.route('/vendor/register', methods=['POST'])
def register_vendor():
    data = request.get_json()
    phone = data.get('phone')

    if Vendor.query.filter_by(phone=phone).first():
        return jsonify({'success': False, 'message': 'Phone number already registered.'}), 409

    hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    new_vendor = Vendor(
        name=data['name'],
        phone=phone,
        password=hashed_password,
        location=data['location'],
        business_type=data['business_type']
    )
    db.session.add(new_vendor)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Registration successful! Please log in.'})

@app.route('/vendor/login', methods=['POST'])
def login_vendor_api():
    data = request.get_json()
    phone = data.get('phone')
    password = data.get('password')

    vendor = Vendor.query.filter_by(phone=phone).first()

    if vendor and bcrypt.check_password_hash(vendor.password, password):
        login_user(vendor)
        return jsonify({'success': True, 'message': 'Login successful!'})
    
    return jsonify({'success': False, 'message': 'Invalid phone number or password.'}), 401

# --- API Data Routes ---

@app.route('/api/dashboard-stats')
@login_required
def dashboard_stats():
    stats = {
        'total_orders': Order.query.filter_by(vendor_id=current_user.id).count(),
        'monthly_savings': 2450, # Placeholder, real logic would be complex
        'active_group_orders': GroupOrder.query.count(),
        'verified_suppliers': Supplier.query.filter_by(verification_status=True).count()
    }
    return jsonify(stats)

@app.route('/api/products')
@login_required
def get_products():
    products = Product.query.all()
    return jsonify([p.to_dict() for p in products])

@app.route('/api/suppliers')
@login_required
def get_suppliers():
    suppliers = Supplier.query.all()
    return jsonify([s.to_dict() for s in suppliers])

@app.route('/api/group-orders')
@login_required

def get_group_orders():
    group_orders = GroupOrder.query.all()
    return jsonify([go.to_dict() for go in group_orders])

@app.route('/api/vendor/orders')
@login_required
def get_vendor_orders():
    orders = Order.query.filter_by(vendor_id=current_user.id).order_by(Order.created_at.desc()).all()
    return jsonify([o.to_dict() for o in orders])

@app.route('/api/price-alerts')
@login_required
def get_price_alerts():
    # This is mock data. In a real application, this would come from a database
    # or a dedicated notification service.
    alerts = [
        {
            "product": "Tomatoes",
            "message": "Price dropped to ₹28/kg at Krishna Mandi.",
            "timestamp": "2024-01-16 09:00 AM"
        },
        {
            "product": "Onions",
            "message": "Price expected to rise tomorrow. Current price: ₹25/kg.",
            "timestamp": "2024-01-16 08:30 AM"
        }
    ]
    return jsonify(alerts)

@app.route('/api/recommended-products')
@login_required
def get_recommended_products():
    business_type = current_user.business_type
    recommended_names = PRODUCT_RECOMMENDATIONS.get(business_type, PRODUCT_RECOMMENDATIONS['other'])
    
    products = Product.query.filter(Product.name.in_(recommended_names)).limit(6).all()
    
    return jsonify([p.to_dict() for p in products])

@app.route('/api/checkout', methods=['POST'])
@login_required
def checkout():
    cart_items = request.get_json()
    if not cart_items:
        return jsonify({'success': False, 'message': 'Cart is empty.'}), 400

    # Group items by supplier
    orders_by_supplier = defaultdict(list)
    for item in cart_items:
        orders_by_supplier[item['supplier_id']].append(item)

    # Create an order for each supplier
    for supplier_id, items in orders_by_supplier.items():
        total_amount = sum(item['current_price'] * item['quantity'] for item in items)
        
        new_order = Order(
            vendor_id=current_user.id,
            supplier_id=supplier_id,
            total_amount=total_amount
        )
        db.session.add(new_order)
    
    db.session.commit()
    return jsonify({'success': True, 'message': 'Orders placed successfully!'})

# --- Main Execution ---
if __name__ == '__main__':
    # Initialize the database and seed it with sample data if it's empty
    init_db(app)
    # Run the Flask app
    app.run(debug=True, host='0.0.0.0', port=5001)