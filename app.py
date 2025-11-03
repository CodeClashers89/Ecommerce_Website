# app.py
from flask import Flask, render_template, session, redirect, url_for, jsonify, request
from flask_sqlalchemy import SQLAlchemy
import json

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# --- DATABASE SETUP ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hustlecart.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- DATABASE MODELS ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(150))
    password = db.Column(db.String(100))

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    items = db.Column(db.Text)
    total = db.Column(db.Float)
    user = db.relationship('User', backref=db.backref('orders', lazy=True))

# --- ROUTES ---

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/Mobile')
def mobile():
    return render_template('mobile.html')

@app.route('/Laptop')
def laptop():
    return render_template('laptop.html')

@app.route('/TV')
def tv():
    return render_template('tv.html')

@app.route('/Sound_System')
def ss():
    return render_template('ss.html')

@app.route('/account')
def account():
    return render_template('account.html')

@app.route('/cart')
def cart():
    cart_items = session.get('cart_items', [])
    total_count = sum(item.get('quantity', 1) for item in cart_items)
    
    # Calculate totals
    subtotal = sum(item['price'] * item.get('quantity', 1) for item in cart_items)
    discount = 2000 if subtotal > 50000 else 1000 if subtotal > 20000 else 500
    delivery = 50
    applied_coins = session.get('applied_coins', 0)
    total = max(0, subtotal - discount + delivery - applied_coins)
    
    return render_template('cart.html', 
                         cart_items=cart_items, 
                         cart_count=total_count,
                         subtotal=subtotal,
                         discount=discount,
                         delivery=delivery,
                         applied_coins=applied_coins,
                         total=total)

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    product_name = request.form.get('product_name')
    product_price = float(request.form.get('product_price'))
    product_image = request.form.get('product_image')
    
    if 'cart_items' not in session:
        session['cart_items'] = []
    
    cart_items = session['cart_items']
    
    # Check if product already exists
    product_exists = False
    for item in cart_items:
        if item['name'] == product_name:
            item['quantity'] = item.get('quantity', 1) + 1
            product_exists = True
            break
    
    if not product_exists:
        cart_items.append({
            'name': product_name,
            'price': product_price,
            'img': product_image,
            'quantity': 1
        })
    
    session['cart_items'] = cart_items
    session.modified = True
    
    return redirect(request.referrer or url_for('home'))

@app.route('/remove_from_cart', methods=['POST'])
def remove_from_cart():
    product_name = request.form.get('product_name')
    
    if 'cart_items' in session:
        cart_items = session['cart_items']
        cart_items = [item for item in cart_items if item['name'] != product_name]
        session['cart_items'] = cart_items
        session.modified = True
    
    return redirect(url_for('cart'))

@app.route('/update_quantity', methods=['POST'])
def update_quantity():
    product_name = request.form.get('product_name')
    action = request.form.get('action')  # 'increase' or 'decrease'
    
    if 'cart_items' in session:
        cart_items = session['cart_items']
        for item in cart_items:
            if item['name'] == product_name:
                if action == 'increase':
                    item['quantity'] = item.get('quantity', 1) + 1
                elif action == 'decrease':
                    item['quantity'] = max(1, item.get('quantity', 1) - 1)
                break
        
        session['cart_items'] = cart_items
        session.modified = True
    
    return redirect(url_for('cart'))

@app.route('/apply_coins', methods=['POST'])
def apply_coins():
    coins = int(request.form.get('coins', 0))
    session['applied_coins'] = coins
    session.modified = True
    return redirect(url_for('cart'))

@app.route('/clear_cart', methods=['POST'])
def clear_cart():
    session['cart_items'] = []
    session['applied_coins'] = 0
    session.modified = True
    return redirect(url_for('cart'))

# ---------------- LOGIN SYSTEM ---------------- #
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        user = User.query.filter_by(username=username).first()
        if user:
            session['user_id'] = user.id
            session['username'] = user.username
            return redirect(url_for('cart'))
        else:
            return "User not found! Please register first."
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

# ---------------- CHECKOUT + PAYMENT ---------------- #
@app.route('/checkout')
def checkout():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return redirect(url_for('payment'))

@app.route('/payment')
def payment():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    cart_items = session.get('cart_items', [])
    if not cart_items:
        return redirect(url_for('cart'))
    
    # Calculate totals
    subtotal = sum(item['price'] * item.get('quantity', 1) for item in cart_items)
    discount = 2000 if subtotal > 50000 else 1000 if subtotal > 20000 else 500
    delivery = 50
    applied_coins = session.get('applied_coins', 0)
    total = max(0, subtotal - discount + delivery - applied_coins)
    
    return render_template('payment.html', 
                         cart_items=cart_items, 
                         subtotal=subtotal,
                         discount=discount,
                         delivery=delivery,
                         applied_coins=applied_coins,
                         total=total)

@app.route('/complete_payment', methods=['POST'])
def complete_payment():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    cart_items = session.get('cart_items', [])
    if not cart_items:
        return redirect(url_for('cart'))

    # Calculate total
    subtotal = sum(item['price'] * item.get('quantity', 1) for item in cart_items)
    discount = 2000 if subtotal > 50000 else 1000 if subtotal > 20000 else 500
    delivery = 50
    applied_coins = session.get('applied_coins', 0)
    total = max(0, subtotal - discount + delivery - applied_coins)

    # Create order
    new_order = Order(
        user_id=session['user_id'],
        items=json.dumps(cart_items),
        total=total
    )
    db.session.add(new_order)
    db.session.commit()

    # Clear cart
    session['cart_items'] = []
    session['applied_coins'] = 0
    session.modified = True

    return render_template('payment_success.html', order_id=new_order.id, total=total)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)