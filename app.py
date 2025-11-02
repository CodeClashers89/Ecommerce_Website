# app.py
from flask import Flask, render_template, session, redirect, url_for, jsonify, request

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Needed for session

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
    return render_template('cart.html', cart_items=cart_items, cart_count=total_count)

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    try:
        product_data = request.get_json()
        if not product_data:
            return jsonify({'success': False, 'error': 'No data provided'})
        
        cart_items = session.get('cart_items', [])
        
        # Check if product already exists in cart
        product_exists = False
        for item in cart_items:
            if item['name'] == product_data['name']:
                item['quantity'] = item.get('quantity', 1) + 1
                product_exists = True
                break
        
        if not product_exists:
            product_data['quantity'] = 1
            cart_items.append(product_data)
        
        session['cart_items'] = cart_items
        total_count = sum(item.get('quantity', 1) for item in cart_items)
        
        return jsonify({
            'success': True, 
            'cart_count': total_count,
            'message': 'Product added to cart!'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
@app.route('/get_cart_data')
def get_cart_data():
    """Get all cart items data"""
    cart_items = session.get('cart_items', [])
    return jsonify(cart_items)

@app.route('/update_cart_quantity', methods=['POST'])
def update_cart_quantity():
    """Update product quantity in cart"""
    try:
        data = request.get_json()
        product_name = data.get('name')
        change = data.get('change', 0)
        
        cart_items = session.get('cart_items', [])
        
        for item in cart_items:
            if item['name'] == product_name:
                new_quantity = item.get('quantity', 1) + change
                if new_quantity <= 0:
                    # Remove item if quantity becomes 0 or less
                    cart_items = [i for i in cart_items if i['name'] != product_name]
                else:
                    item['quantity'] = new_quantity
                break
        
        session['cart_items'] = cart_items
        total_count = sum(item.get('quantity', 1) for item in cart_items)
        
        return jsonify({
            'success': True, 
            'cart_count': total_count
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/remove_from_cart', methods=['POST'])
def remove_from_cart():
    """Remove item from cart"""
    try:
        data = request.get_json()
        product_name = data.get('name')
        
        cart_items = session.get('cart_items', [])
        cart_items = [item for item in cart_items if item['name'] != product_name]
        
        session['cart_items'] = cart_items
        total_count = sum(item.get('quantity', 1) for item in cart_items)
        
        return jsonify({
            'success': True, 
            'cart_count': total_count
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
@app.route('/update_cart', methods=['POST'])
def update_cart():
    """Legacy endpoint - redirect to new endpoints"""
    try:
        data = request.get_json()
        action = data.get('action')
        
        if action == 'remove':
            return remove_from_cart()
        elif action == 'update_quantity':
            return update_cart_quantity()
        else:
            return jsonify({'success': False, 'error': 'Invalid action'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/get_cart_count')
def get_cart_count():
    cart_items = session.get('cart_items', [])
    total_count = sum(item.get('quantity', 1) for item in cart_items)
    return jsonify({'count': total_count})

@app.route('/clear_cart')
def clear_cart():
    session['cart_items'] = []
    return jsonify({'success': True, 'count': 0})

if __name__ == '__main__':
    app.run(debug=True)