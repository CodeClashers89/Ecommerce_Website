from flask import Flask, render_template, session, redirect, url_for, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = 'sdnuv42732ry'

# -------------------- Database Setup -------------------- #
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hustlecart.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# -------------------- Models -------------------- #
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    mobile = db.Column(db.String(20), default='')
    coins = db.Column(db.Integer, default=1000)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_name = db.Column(db.String(100), nullable=False)
    product_price = db.Column(db.Float, nullable=False)
    product_image = db.Column(db.String(200))
    quantity = db.Column(db.Integer, default=1)


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    order_id = db.Column(db.String(50), unique=True, nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(50), default='cod')
    coins_used = db.Column(db.Integer, default=0)
    status = db.Column(db.String(50), default='Processing')
    order_date = db.Column(db.DateTime, default=datetime.utcnow)


class UserAddress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    address_line1 = db.Column(db.String(200), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(100), nullable=False)
    zip_code = db.Column(db.String(20), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    is_default = db.Column(db.Boolean, default=False)

with app.app_context():
    db.create_all()

# -------------------- Helper Decorators -------------------- #
def login_required_redirect(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated


def profile_completion_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login_page'))
        user = User.query.get(session['user_id'])
        if not user:
            session.clear()
            return redirect(url_for('login_page'))

        has_basic_info = bool(user.username and user.mobile)
        has_address = UserAddress.query.filter_by(user_id=user.id).first()
        if not has_basic_info or not has_address:
            return redirect(url_for('complete_profile_page'))
        return f(*args, **kwargs)
    return decorated_function

# -------------------- Basic Pages -------------------- #
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

@app.route('/cart')
@login_required_redirect
def cart():
    return render_template('cart.html')

@app.route('/account')
@profile_completion_required
def account():
    user = User.query.get(session['user_id'])
    return render_template('account.html', user=user)

# -------------------- Auth -------------------- #
@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        return handle_login()
    return render_template('login.html')


@app.route('/handle_login', methods=['POST'])
def handle_login():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            return jsonify({'success': False, 'error': 'Invalid credentials'})

        session['user_id'] = user.id
        session['user_email'] = user.email
        session['user_name'] = user.username

        has_basic_info = bool(user.username and user.mobile)
        has_address = UserAddress.query.filter_by(user_id=user.id).first()
        if not has_basic_info or not has_address:
            return jsonify({'success': True, 'redirect': '/complete_profile'})

        return jsonify({'success': True, 'redirect': '/account'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/register', methods=['GET', 'POST'])
def register_page():
    if request.method == 'POST':
        return handle_register()
    return render_template('register.html')


@app.route('/handle_register', methods=['POST'])
def handle_register():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        username = data.get('username')

        existing = User.query.filter_by(email=email).first()
        if existing:
            return jsonify({'success': False, 'error': 'Email already registered'})

        new_user = User(email=email, username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        session['user_id'] = new_user.id
        session['user_email'] = new_user.email
        session['user_name'] = new_user.username

        return jsonify({'success': True, 'redirect': '/complete_profile'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# -------------------- Complete Profile -------------------- #
@app.route('/complete_profile', methods=['GET', 'POST'])
@login_required_redirect
def complete_profile_page():
    if request.method == 'POST':
        try:
            data = request.get_json()
            user = User.query.get(session['user_id'])
            if not user:
                return jsonify({'success': False, 'error': 'User not found'})

            # Update user profile
            user.username = data.get('username', user.username)
            user.mobile = data.get('mobile', user.mobile)

            # Create default address
            addr = UserAddress(
                user_id=user.id,
                name=data.get('username'),
                address_line1=data.get('address_line1'),
                city=data.get('city'),
                state=data.get('state'),
                zip_code=data.get('zip_code'),
                phone=data.get('mobile'),
                is_default=True
            )
            db.session.add(addr)
            db.session.commit()

            return jsonify({'success': True, 'redirect': '/account'})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
    return render_template('complete_profile.html')

# -------------------- Cart / Auth Check -------------------- #

@app.route('/check_auth')
def check_auth():
    """Return JSON telling if the user is logged in"""
    if 'user_id' in session:
        return jsonify({'authenticated': True})
    return jsonify({'authenticated': False})


@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    """Add product to cart, requires login"""
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': 'Please login first'}), 401

        data = request.get_json()
        user_id = session['user_id']
        product_name = data.get('name')
        product_price = float(data.get('price', 0))
        product_image = data.get('img', '')
        quantity = int(data.get('quantity', 1))

        existing = CartItem.query.filter_by(user_id=user_id, product_name=product_name).first()
        if existing:
            existing.quantity += quantity
        else:
            db.session.add(CartItem(
                user_id=user_id,
                product_name=product_name,
                product_price=product_price,
                product_image=product_image,
                quantity=quantity
            ))

        db.session.commit()
        
        # Get updated cart count
        cart_count = CartItem.query.filter_by(user_id=user_id).count()
        return jsonify({'success': True, 'message': f'{product_name} added to cart!', 'cart_count': cart_count})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/get_cart_count')
@login_required_redirect
def get_cart_count():
    try:
        count = CartItem.query.filter_by(user_id=session['user_id']).count()
        return jsonify({'count': count})
    except Exception as e:
        return jsonify({'count': 0})

@app.route('/get_cart_data')
@login_required_redirect
def get_cart_data():
    try:
        cart_items = CartItem.query.filter_by(user_id=session['user_id']).all()
        items_data = []
        for item in cart_items:
            items_data.append({
                'name': item.product_name,
                'price': item.product_price,
                'img': item.product_image,
                'quantity': item.quantity
            })
        return jsonify(items_data)
    except Exception as e:
        return jsonify([])

@app.route('/update_cart_quantity', methods=['POST'])
@login_required_redirect
def update_cart_quantity():
    try:
        data = request.get_json()
        product_name = data.get('name')
        change = data.get('change', 0)
        
        cart_item = CartItem.query.filter_by(user_id=session['user_id'], product_name=product_name).first()
        if cart_item:
            new_quantity = cart_item.quantity + change
            if new_quantity <= 0:
                db.session.delete(cart_item)
            else:
                cart_item.quantity = new_quantity
            db.session.commit()
        
        # Get updated cart count
        cart_count = CartItem.query.filter_by(user_id=session['user_id']).count()
        return jsonify({'success': True, 'cart_count': cart_count})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/remove_from_cart', methods=['POST'])
@login_required_redirect
def remove_from_cart():
    try:
        data = request.get_json()
        product_name = data.get('name')
        
        cart_item = CartItem.query.filter_by(user_id=session['user_id'], product_name=product_name).first()
        if cart_item:
            db.session.delete(cart_item)
            db.session.commit()
        
        cart_count = CartItem.query.filter_by(user_id=session['user_id']).count()
        return jsonify({'success': True, 'cart_count': cart_count})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# -------------------- Account Management -------------------- #
@app.route('/get_user_data')
@login_required_redirect
def get_user_data():
    try:
        user = User.query.get(session['user_id'])
        if not user:
            return jsonify({'error': 'User not found'})
        
        # Get default address
        default_address = UserAddress.query.filter_by(user_id=user.id, is_default=True).first()
        address_display = "No address set"
        if default_address:
            address_display = f"{default_address.address_line1}, {default_address.city}, {default_address.state} - {default_address.zip_code}"
        
        return jsonify({
            'username': user.username or '',
            'email': user.email or '',
            'mobile': user.mobile or '',
            'address': address_display,
            'coins': user.coins or 0
        })
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/update_profile', methods=['POST'])
@login_required_redirect
def update_profile():
    try:
        data = request.get_json()
        user = User.query.get(session['user_id'])
        if not user:
            return jsonify({'success': False, 'error': 'User not found'})
        
        user.username = data.get('username', user.username)
        user.mobile = data.get('mobile', user.mobile)
        
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/get_user_addresses')
@login_required_redirect
def get_user_addresses():
    try:
        addresses = UserAddress.query.filter_by(user_id=session['user_id']).all()
        addresses_data = []
        for addr in addresses:
            addresses_data.append({
                'id': addr.id,
                'name': addr.name,
                'full_address': f"{addr.address_line1}, {addr.city}, {addr.state} - {addr.zip_code}",
                'phone': addr.phone,
                'is_default': addr.is_default
            })
        return jsonify({'success': True, 'addresses': addresses_data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/add_address', methods=['POST'])
@login_required_redirect
def add_address():
    try:
        data = request.get_json()
        
        # If this is set as default, unset other defaults
        if data.get('is_default'):
            UserAddress.query.filter_by(user_id=session['user_id']).update({'is_default': False})
        
        new_address = UserAddress(
            user_id=session['user_id'],
            name=data.get('name'),
            address_line1=data.get('address_line1'),
            address_line2=data.get('address_line2', ''),
            city=data.get('city'),
            state=data.get('state'),
            zip_code=data.get('zip_code'),
            phone=data.get('phone'),
            is_default=data.get('is_default', False)
        )
        
        db.session.add(new_address)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/delete_address/<int:address_id>', methods=['DELETE'])
@login_required_redirect
def delete_address(address_id):
    try:
        address = UserAddress.query.filter_by(id=address_id, user_id=session['user_id']).first()
        if not address:
            return jsonify({'success': False, 'error': 'Address not found'})
        
        db.session.delete(address)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/get_user_orders')
@login_required_redirect
def get_user_orders():
    try:
        orders = Order.query.filter_by(user_id=session['user_id']).order_by(Order.order_date.desc()).all()
        orders_data = []
        for order in orders:
            orders_data.append({
                'order_id': order.order_id,
                'total_amount': order.total_amount,
                'payment_method': order.payment_method,
                'status': order.status,
                'order_date': order.order_date.strftime('%Y-%m-%d %H:%M:%S')
            })
        return jsonify({'success': True, 'orders': orders_data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# -------------------- Payment -------------------- #
@app.route('/payment')
@login_required_redirect
def payment():
    return render_template('payment.html')

@app.route('/process_payment', methods=['POST'])
@login_required_redirect
def process_payment():
    try:
        data = request.get_json()
        method = data.get('method')
        total = float(data.get('total', 0))
        coins_used = int(data.get('coins_used', 0))

        new_order = Order(
            user_id=session['user_id'],
            order_id=f"ORD{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            total_amount=total,
            payment_method=method,
            coins_used=coins_used,
            status='Confirmed'
        )
        db.session.add(new_order)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Payment successful!', 'order': {'order_id': new_order.order_id, 'total_amount': new_order.total_amount}})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/checkout', methods=['POST'])
@login_required_redirect
def checkout():
    try:
        data = request.get_json()
        coins_used = data.get('coins_used', 0)
        payment_method = data.get('payment_method', 'cod')
        total_amount = data.get('total_amount', 0)
        cart_items = data.get('cart_items', [])

        print(f"Checkout received: coins_used={coins_used}, payment_method={payment_method}, total_amount={total_amount}")

        # Create order
        new_order = Order(
            user_id=session['user_id'],
            order_id=f"ORD{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            total_amount=total_amount,
            payment_method=payment_method,
            coins_used=coins_used,
            status='Processing'
        )
        db.session.add(new_order)

        # Clear user's cart
        CartItem.query.filter_by(user_id=session['user_id']).delete()

        db.session.commit()
        
        print(f"Order created: {new_order.order_id}")
        return jsonify({
            'success': True, 
            'order': {
                'order_id': new_order.order_id, 
                'total_amount': new_order.total_amount
            }
        })
    except Exception as e:
        print(f"Checkout error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})
    
@app.route('/get_cart_total')
@login_required_redirect
def get_cart_total():
    user_id = session.get('user_id')
    items = CartItem.query.filter_by(user_id=user_id).all()
    if not items:
        return jsonify({'success': False, 'error': 'Cart is empty'})

    subtotal = sum(item.product_price * item.quantity for item in items)
    discount = 0
    delivery = 0
    coins_used = 0
    total = subtotal - discount + delivery

    return jsonify({
        'success': True,
        'subtotal': subtotal,
        'discount': discount,
        'delivery': delivery,
        'coins_used': coins_used,
        'total': total
    })


# -------------------- Logout -------------------- #
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_page'))

# -------------------- Run -------------------- #
if __name__ == '__main__':
    app.run(debug=True)