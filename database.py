from models import db, Vendor, Supplier, Product, Order, GroupOrder
from flask_bcrypt import Bcrypt
import datetime

def init_db(app):
    with app.app_context():
        db.create_all()
        bcrypt = Bcrypt(app)

        # Check if data already exists
        if Vendor.query.first() is None:
            print("Database is empty, seeding with sample data...")

            # Create a sample vendor
            hashed_password = bcrypt.generate_password_hash('Password123').decode('utf-8')
            vendor1 = Vendor(
                name='Ankit Sharma',
                phone='1234567890',
                password=hashed_password,
                location='Bandra West, Mumbai',
                business_type='chaat'
            )
            db.session.add(vendor1)

            # Create sample suppliers
            supplier1 = Supplier(name='Krishna Mandi', location='Dadar, Mumbai', phone='9876543210', rating=4.8, hygiene_rating=4.5)
            supplier2 = Supplier(name='Fresh Farm Supplies', location='Andheri, Mumbai', phone='9876543211', rating=4.5, hygiene_rating=4.2)
            supplier3 = Supplier(name='Quality Vegetables', location='Thane', phone='9876543212', rating=4.7, hygiene_rating=4.8)
            db.session.add_all([supplier1, supplier2, supplier3])

            # Commit to get IDs for suppliers
            db.session.commit()

            # Create sample products
            products_data = [
                {'name': 'Tomatoes', 'category': 'vegetables', 'unit': 'kg', 'current_price': 30.0, 'supplier_id': supplier1.id, 'image_url': 'https://images.unsplash.com/photo-1582284540020-8acbe03f4924?q=80&w=400&auto=format&fit=crop'},
                {'name': 'Onions', 'category': 'vegetables', 'unit': 'kg', 'current_price': 25.0, 'supplier_id': supplier1.id, 'image_url': 'https://images.unsplash.com/photo-1587049352851-8d4e89133924?q=80&w=400&auto=format&fit=crop'},
                {'name': 'Potatoes', 'category': 'vegetables', 'unit': 'kg', 'current_price': 20.0, 'supplier_id': supplier2.id, 'image_url': 'https://images.unsplash.com/photo-1518977676601-b53f82aba655?q=80&w=400&auto=format&fit=crop'},
                {'name': 'Sunflower Oil', 'category': 'oils', 'unit': 'litre', 'current_price': 150.0, 'supplier_id': supplier2.id, 'image_url': 'https://images.unsplash.com/photo-1626087383849-572265ea3553?q=80&w=400&auto=format&fit=crop'},
                {'name': 'Basmati Rice', 'category': 'grains', 'unit': 'kg', 'current_price': 80.0, 'supplier_id': supplier3.id, 'image_url': 'https://images.unsplash.com/photo-1586201375765-c124a2734441?q=80&w=400&auto=format&fit=crop'},
                {'name': 'Chickpeas (Chana)', 'category': 'pulses', 'unit': 'kg', 'current_price': 90.0, 'supplier_id': supplier3.id, 'image_url': 'https://images.unsplash.com/photo-1605591116834-8a15ac585371?q=80&w=400&auto=format&fit=crop'},
            ]
            for p_data in products_data:
                db.session.add(Product(**p_data))

            # Create sample orders for the vendor
            orders_data = [
                {'vendor_id': vendor1.id, 'supplier_id': supplier1.id, 'total_amount': 1200, 'created_at': datetime.datetime(2024, 1, 15)},
                {'vendor_id': vendor1.id, 'supplier_id': supplier2.id, 'total_amount': 800, 'created_at': datetime.datetime(2024, 1, 12)},
                {'vendor_id': vendor1.id, 'supplier_id': supplier3.id, 'total_amount': 1500, 'created_at': datetime.datetime(2024, 1, 10)},
            ]
            for o_data in orders_data:
                db.session.add(Order(**o_data))

            # Create sample group orders
            group_orders_data = [
                {
                    'product_name': 'Bulk Onions', 'target_quantity': 500, 'current_quantity': 280, 
                    'price_per_unit': 18.0, 'participants_count': 12
                },
                {
                    'product_name': 'Bulk Potatoes', 'target_quantity': 800, 'current_quantity': 750, 
                    'price_per_unit': 15.0, 'participants_count': 25
                },
                {
                    'product_name': 'Bulk Sunflower Oil', 'target_quantity': 200, 'current_quantity': 50, 
                    'price_per_unit': 135.0, 'participants_count': 5
                }
            ]
            for go_data in group_orders_data:
                db.session.add(GroupOrder(**go_data))

            db.session.commit()
            print("Sample data has been added.")
        else:
            print("Database already contains data.")