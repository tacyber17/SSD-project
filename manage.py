"""
Flask CLI management script for database migrations and seeding.
"""
import os
from flask.cli import FlaskGroup
from app import create_app, db
from app.models import User, Product, Category, Order, OrderItem, CartItem

app = create_app()
cli = FlaskGroup(app)


@cli.command()
def init_db():
    """Initialize the database."""
    db.create_all()
    print("Database initialized.")


@cli.command()
def seed():
    """Seed the database with sample data."""
    print("Seeding database...")
    
    # Create admin user
    admin = User.query.filter_by(email='admin@example.com').first()
    if not admin:
        admin = User(
            username='admin',
            email='admin@example.com',
            first_name='Admin',
            last_name='User',
            role='admin'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        print("Created admin user (email: admin@example.com, password: admin123)")
    
    # Create test customer
    customer = User.query.filter_by(email='customer@example.com').first()
    if not customer:
        customer = User(
            username='customer',
            email='customer@example.com',
            first_name='John',
            last_name='Doe',
            role='customer',
            address='123 Main St, City, State 12345'
        )
        customer.set_password('customer123')
        db.session.add(customer)
        print("Created customer user (email: customer@example.com, password: customer123)")
    
    # Create categories
    categories_data = [
        {'name': 'Electronics', 'description': 'Electronic devices and gadgets'},
        {'name': 'Clothing', 'description': 'Apparel and fashion items'},
        {'name': 'Books', 'description': 'Books and reading materials'},
        {'name': 'Home & Garden', 'description': 'Home improvement and garden supplies'},
    ]
    
    for cat_data in categories_data:
        category = Category.query.filter_by(name=cat_data['name']).first()
        if not category:
            category = Category(**cat_data)
            category.slug = category.name.lower().replace(' ', '-')
            db.session.add(category)
    
    db.session.commit()
    
    # Create products - Expanded list with many products
    products_data = [
        # Electronics
        {
            'name': 'Laptop Computer',
            'description': 'High-performance laptop with 16GB RAM and 512GB SSD. Perfect for work and gaming.',
            'price': 999.99,
            'stock': 10,
            'category': 'Electronics'
        },
        {
            'name': 'Wireless Mouse',
            'description': 'Ergonomic wireless mouse with long battery life and precise tracking.',
            'price': 29.99,
            'stock': 50,
            'category': 'Electronics'
        },
        {
            'name': 'Mechanical Keyboard',
            'description': 'RGB backlit mechanical keyboard with Cherry MX switches. Perfect for gaming and typing.',
            'price': 129.99,
            'stock': 35,
            'category': 'Electronics'
        },
        {
            'name': 'Wireless Headphones',
            'description': 'Premium noise-cancelling wireless headphones with 30-hour battery life.',
            'price': 199.99,
            'stock': 25,
            'category': 'Electronics'
        },
        {
            'name': 'Smartphone',
            'description': 'Latest generation smartphone with 128GB storage, dual camera, and fast charging.',
            'price': 699.99,
            'stock': 15,
            'category': 'Electronics'
        },
        {
            'name': 'Tablet',
            'description': '10-inch tablet with high-resolution display, perfect for reading and entertainment.',
            'price': 399.99,
            'stock': 20,
            'category': 'Electronics'
        },
        {
            'name': 'Smart Watch',
            'description': 'Fitness tracking smartwatch with heart rate monitor and GPS.',
            'price': 249.99,
            'stock': 30,
            'category': 'Electronics'
        },
        {
            'name': 'USB-C Cable',
            'description': 'Fast charging USB-C cable, 6 feet long, compatible with all USB-C devices.',
            'price': 12.99,
            'stock': 100,
            'category': 'Electronics'
        },
        {
            'name': 'Webcam HD',
            'description': '1080p HD webcam with built-in microphone for video calls and streaming.',
            'price': 49.99,
            'stock': 40,
            'category': 'Electronics'
        },
        {
            'name': 'Portable Power Bank',
            'description': '20000mAh portable power bank with fast charging support for all devices.',
            'price': 34.99,
            'stock': 60,
            'category': 'Electronics'
        },
        # Clothing
        {
            'name': 'Cotton T-Shirt',
            'description': 'Comfortable 100% cotton t-shirt available in multiple colors and sizes.',
            'price': 19.99,
            'stock': 100,
            'category': 'Clothing'
        },
        {
            'name': 'Jeans',
            'description': 'Classic fit denim jeans with stretch for comfort.',
            'price': 49.99,
            'stock': 75,
            'category': 'Clothing'
        },
        {
            'name': 'Hoodie',
            'description': 'Warm and comfortable hoodie with front pocket and adjustable drawstring.',
            'price': 39.99,
            'stock': 50,
            'category': 'Clothing'
        },
        {
            'name': 'Running Shoes',
            'description': 'Lightweight running shoes with cushioned sole and breathable mesh upper.',
            'price': 79.99,
            'stock': 40,
            'category': 'Clothing'
        },
        {
            'name': 'Winter Jacket',
            'description': 'Waterproof winter jacket with insulated lining, perfect for cold weather.',
            'price': 129.99,
            'stock': 30,
            'category': 'Clothing'
        },
        {
            'name': 'Baseball Cap',
            'description': 'Classic baseball cap with adjustable strap, available in multiple colors.',
            'price': 14.99,
            'stock': 80,
            'category': 'Clothing'
        },
        {
            'name': 'Sneakers',
            'description': 'Casual sneakers with comfortable insole and durable rubber sole.',
            'price': 59.99,
            'stock': 45,
            'category': 'Clothing'
        },
        {
            'name': 'Dress Shirt',
            'description': 'Formal dress shirt, wrinkle-free fabric, available in white and blue.',
            'price': 34.99,
            'stock': 55,
            'category': 'Clothing'
        },
        {
            'name': 'Sweatpants',
            'description': 'Comfortable sweatpants with elastic waistband and drawstring.',
            'price': 29.99,
            'stock': 65,
            'category': 'Clothing'
        },
        {
            'name': 'Leather Belt',
            'description': 'Genuine leather belt with classic buckle, available in black and brown.',
            'price': 24.99,
            'stock': 70,
            'category': 'Clothing'
        },
        # Books
        {
            'name': 'Python Programming Book',
            'description': 'Comprehensive guide to Python programming for beginners and advanced users.',
            'price': 39.99,
            'stock': 30,
            'category': 'Books'
        },
        {
            'name': 'JavaScript: The Definitive Guide',
            'description': 'Complete reference guide to JavaScript programming language.',
            'price': 49.99,
            'stock': 25,
            'category': 'Books'
        },
        {
            'name': 'Web Development Handbook',
            'description': 'Modern web development guide covering HTML, CSS, and JavaScript.',
            'price': 34.99,
            'stock': 35,
            'category': 'Books'
        },
        {
            'name': 'Data Structures and Algorithms',
            'description': 'Comprehensive guide to data structures and algorithms with examples.',
            'price': 54.99,
            'stock': 20,
            'category': 'Books'
        },
        {
            'name': 'Mystery Novel',
            'description': 'Bestselling mystery novel with thrilling plot and unexpected twists.',
            'price': 14.99,
            'stock': 50,
            'category': 'Books'
        },
        {
            'name': 'Science Fiction Collection',
            'description': 'Collection of classic science fiction short stories from renowned authors.',
            'price': 19.99,
            'stock': 40,
            'category': 'Books'
        },
        {
            'name': 'Cookbook: Italian Cuisine',
            'description': 'Authentic Italian recipes with step-by-step instructions and beautiful photos.',
            'price': 24.99,
            'stock': 30,
            'category': 'Books'
        },
        {
            'name': 'History of Technology',
            'description': 'Fascinating journey through the history of technological innovations.',
            'price': 29.99,
            'stock': 25,
            'category': 'Books'
        },
        {
            'name': 'Self-Help Guide',
            'description': 'Practical guide to personal development and achieving your goals.',
            'price': 16.99,
            'stock': 45,
            'category': 'Books'
        },
        {
            'name': 'Children\'s Storybook',
            'description': 'Colorful children\'s storybook with engaging stories and illustrations.',
            'price': 12.99,
            'stock': 60,
            'category': 'Books'
        },
        # Home & Garden
        {
            'name': 'Garden Tools Set',
            'description': 'Complete set of gardening tools including shovel, rake, and pruning shears.',
            'price': 79.99,
            'stock': 20,
            'category': 'Home & Garden'
        },
        {
            'name': 'Indoor Plant Pot',
            'description': 'Decorative ceramic plant pot, perfect for indoor plants and succulents.',
            'price': 19.99,
            'stock': 50,
            'category': 'Home & Garden'
        },
        {
            'name': 'Garden Hose',
            'description': '50-foot garden hose with spray nozzle, kink-resistant design.',
            'price': 34.99,
            'stock': 30,
            'category': 'Home & Garden'
        },
        {
            'name': 'Lawn Mower',
            'description': 'Electric lawn mower with adjustable cutting height and grass collection bag.',
            'price': 199.99,
            'stock': 10,
            'category': 'Home & Garden'
        },
        {
            'name': 'Plant Fertilizer',
            'description': 'Organic plant fertilizer, promotes healthy growth for all types of plants.',
            'price': 14.99,
            'stock': 80,
            'category': 'Home & Garden'
        },
        {
            'name': 'Garden Gloves',
            'description': 'Durable gardening gloves with reinforced fingertips, comfortable fit.',
            'price': 9.99,
            'stock': 100,
            'category': 'Home & Garden'
        },
        {
            'name': 'Outdoor Patio Set',
            'description': '4-piece patio furniture set with table and chairs, weather-resistant.',
            'price': 299.99,
            'stock': 8,
            'category': 'Home & Garden'
        },
        {
            'name': 'LED String Lights',
            'description': '20-foot LED string lights with remote control, perfect for outdoor decoration.',
            'price': 24.99,
            'stock': 40,
            'category': 'Home & Garden'
        },
        {
            'name': 'Watering Can',
            'description': '2-gallon plastic watering can with comfortable handle and precision spout.',
            'price': 12.99,
            'stock': 60,
            'category': 'Home & Garden'
        },
        {
            'name': 'Garden Bench',
            'description': 'Wooden garden bench with weather-resistant finish, seats two comfortably.',
            'price': 149.99,
            'stock': 12,
            'category': 'Home & Garden'
        },
    ]
    
    products_created = 0
    for prod_data in products_data:
        category = Category.query.filter_by(name=prod_data.pop('category')).first()
        if category:
            product = Product.query.filter_by(name=prod_data['name']).first()
            if not product:
                product = Product(**prod_data)
                product.category_id = category.id
                product.slug = product.name.lower().replace(' ', '-').replace("'", '').replace(':', '')
                product.is_active = True  # Ensure products are active and visible
                db.session.add(product)
                products_created += 1
    
    db.session.commit()
    print(f"Database seeded successfully!")
    print(f"Created {products_created} new products across {len(categories_data)} categories.")


@cli.command()
def create_admin():
    """Create an admin user."""
    email = input("Enter admin email: ")
    username = input("Enter admin username: ")
    password = input("Enter admin password: ")
    
    admin = User(
        username=username,
        email=email,
        first_name='Admin',
        last_name='User',
        role='admin'
    )
    admin.set_password(password)
    
    db.session.add(admin)
    db.session.commit()
    print(f"Admin user created: {email}")


if __name__ == '__main__':
    cli()


