from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import sqlite3
import os
from werkzeug.utils import secure_filename
from config import *
from AIbrain import get_response

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

# Upload config
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'images', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database.db')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    if os.path.exists(DATABASE):
        try:
            conn = sqlite3.connect(DATABASE)
            conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            conn.close()
            print("Database OK, reusing.")
            return
        except sqlite3.DatabaseError:
            print("Database corrupted. Deleting and recreating...")
            os.remove(DATABASE)
    
    conn = sqlite3.connect(DATABASE)
    
    conn.execute('''
        CREATE TABLE products(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            price REAL,
            compare_price REAL,
            description TEXT,
            image_file TEXT,
            category TEXT,
            is_new INTEGER DEFAULT 0
        )
    ''')
    
    conn.execute('''
        CREATE TABLE news(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT
        )
    ''')
    
    conn.execute('''
        CREATE TABLE admins(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            password TEXT
        )
    ''')
    
    conn.execute('INSERT INTO admins (username, password) VALUES (?, ?)', ('admin', 'admin123'))
    conn.commit()
    conn.close()
    print("Database created successfully!")

init_db()

# ==================== CUSTOMER ROUTES ====================

@app.route('/')
def index():
    db = get_db()
    featured_products = db.execute('SELECT * FROM products WHERE is_new = 1 LIMIT 6').fetchall()
    news = db.execute('SELECT * FROM news ORDER BY id DESC').fetchall()
    db.close()
    return render_template('index.html', featured_products=featured_products, news=news, config=globals())

@app.route('/shop')
def shop():
    db = get_db()
    category = request.args.get('category', '')
    search = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)
    per_page = 12
    
    query = 'SELECT * FROM products WHERE 1=1'
    count_query = 'SELECT COUNT(*) as count FROM products WHERE 1=1'
    params = []
    
    if category:
        query += ' AND category = ?'
        count_query += ' AND category = ?'
        params.append(category)
    if search:
        query += ' AND name LIKE ?'
        count_query += ' AND name LIKE ?'
        params.append(f'%{search}%')
    
    total = db.execute(count_query, params).fetchone()['count']
    offset = (page - 1) * per_page
    query += f' LIMIT {per_page} OFFSET {offset}'
    
    products = db.execute(query, params).fetchall()
    categories = db.execute('SELECT DISTINCT category FROM products').fetchall()
    
    class Pagination:
        def __init__(self, items, page, per_page, total):
            self.items = items
            self.page = page
            self.per_page = per_page
            self.total = total
            self.pages = (total + per_page - 1) // per_page
            self.has_prev = page > 1
            self.has_next = page < self.pages
            self.prev_num = page - 1
            self.next_num = page + 1
    
    products_paginated = Pagination(products, page, per_page, total)
    db.close()
    return render_template('shop.html', products=products_paginated, categories=categories, 
                          category=category, search=search, config=globals())

@app.route('/product/<int:id>')
def product_detail(id):
    db = get_db()
    product = db.execute('SELECT * FROM products WHERE id = ?', (id,)).fetchone()
    db.close()
    return render_template('product.html', product=product, config=globals())

@app.route('/cart')
def cart():
    cart = session.get('cart', {})
    cart_items = []
    total = 0
    
    if cart:
        db = get_db()
        for pid, qty in cart.items():
            p = db.execute('SELECT * FROM products WHERE id = ?', (pid,)).fetchone()
            if p:
                cart_items.append({
                    'id': pid,
                    'name': p['name'],
                    'price': p['price'],
                    'image_file': p['image_file'],
                    'qty': qty,
                    'subtotal': p['price'] * qty
                })
                total += p['price'] * qty
        db.close()
    
    return render_template('cart.html', cart_items=cart_items, total=total, config=globals())

@app.route('/add_to_cart/<int:id>', methods=['POST'])
def add_to_cart(id):
    cart = session.get('cart', {})
    cart[str(id)] = cart.get(str(id), 0) + 1
    session['cart'] = cart
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True, 'cart_count': sum(cart.values())})
    return redirect(url_for('cart'))

@app.route('/update_cart/<int:id>', methods=['POST'])
def update_cart(id):
    qty = int(request.form.get('qty', 1))
    cart = session.get('cart', {})
    if qty > 0:
        cart[str(id)] = qty
    else:
        cart.pop(str(id), None)
    session['cart'] = cart
    return redirect(url_for('cart'))

@app.route('/remove_from_cart/<int:id>')
def remove_from_cart(id):
    cart = session.get('cart', {})
    cart.pop(str(id), None)
    session['cart'] = cart
    return redirect(url_for('cart'))

@app.route('/checkout')
def checkout():
    cart = session.get('cart', {})
    cart_items = []
    total = 0
    
    if cart:
        db = get_db()
        for pid, qty in cart.items():
            p = db.execute('SELECT * FROM products WHERE id = ?', (pid,)).fetchone()
            if p:
                cart_items.append({
                    'id': pid,
                    'name': p['name'],
                    'price': p['price'],
                    'qty': qty,
                    'subtotal': p['price'] * qty
                })
                total += p['price'] * qty
        db.close()
    
    msg = "Hello! I want to order:\n"
    for item in cart_items:
        msg += f"- {item['name']} x{item['qty']} = ₦{item['subtotal']}\n"
    msg += f"\nTotal: ₦{total}"
    
    whatsapp_link = f"https://wa.me/{WHATSAPP_NUMBER}?text={msg.replace(' ', '%20').replace('\n', '%0A')}"
    
    return render_template('checkout.html', cart_items=cart_items, total=total, 
                         whatsapp_link=whatsapp_link, config=globals())

@app.route('/about')
def about():
    return render_template('about.html', config=globals())

# ==================== ADMIN ROUTES ====================

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        db = get_db()
        admin = db.execute('SELECT * FROM admins WHERE username = ? AND password = ?', 
                          (username, password)).fetchone()
        db.close()
        
        if admin:
            session['admin'] = True
            return redirect(url_for('admin_dashboard'))
        return 'Invalid credentials'
    
    return render_template('admin_login.html', config=globals())

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    db = get_db()
    total_products = db.execute('SELECT COUNT(*) as count FROM products').fetchone()['count']
    total_news = db.execute('SELECT COUNT(*) as count FROM news').fetchone()['count']
    db.close()
    
    return render_template('admin_dashboard.html', total_products=total_products, 
                          total_news=total_news, config=globals())

@app.route('/admin/products')
def admin_products():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    db = get_db()
    products = db.execute('SELECT * FROM products').fetchall()
    db.close()
    return render_template('admin_products.html', products=products, config=globals())

@app.route('/admin/add_product', methods=['POST'])
def add_product():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    image_file = request.form.get('image_file', '')
    if 'image_upload' in request.files:
        file = request.files['image_upload']
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            base, ext = os.path.splitext(filename)
            counter = 1
            while os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], filename)):
                filename = f"{base}_{counter}{ext}"
                counter += 1
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image_file = filename
    
    db = get_db()
    db.execute('''INSERT INTO products 
                  (name, price, compare_price, description, image_file, category, is_new) 
                  VALUES (?, ?, ?, ?, ?, ?, ?)''',
               (request.form['name'], request.form['price'], 
                request.form.get('compare_price', 0) or None,
                request.form['description'], image_file, 
                request.form['category'], 1 if request.form.get('is_new') else 0))
    db.commit()
    db.close()
    return redirect(url_for('admin_products'))

@app.route('/admin/edit_product/<int:id>', methods=['POST'])
def edit_product(id):
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    image_file = request.form.get('image_file', '')
    if 'image_upload' in request.files:
        file = request.files['image_upload']
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            base, ext = os.path.splitext(filename)
            counter = 1
            while os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], filename)):
                filename = f"{base}_{counter}{ext}"
                counter += 1
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image_file = filename
    
    db = get_db()
    db.execute('''UPDATE products SET 
                  name=?, price=?, compare_price=?, description=?, 
                  image_file=?, category=?, is_new=? WHERE id=?''',
               (request.form['name'], request.form['price'],
                request.form.get('compare_price', 0) or None,
                request.form['description'], image_file,
                request.form['category'], 1 if request.form.get('is_new') else 0, id))
    db.commit()
    db.close()
    return redirect(url_for('admin_products'))

@app.route('/admin/delete_product/<int:id>')
def delete_product(id):
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    db = get_db()
    # Optionally delete image file
    product = db.execute('SELECT image_file FROM products WHERE id = ?', (id,)).fetchone()
    if product and product['image_file']:
        img_path = os.path.join(app.config['UPLOAD_FOLDER'], product['image_file'])
        if os.path.exists(img_path):
            os.remove(img_path)
    
    db.execute('DELETE FROM products WHERE id = ?', (id,))
    db.commit()
    db.close()
    return redirect(url_for('admin_products'))

@app.route('/admin/news')
def admin_news():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    db = get_db()
    news = db.execute('SELECT * FROM news').fetchall()
    db.close()
    return render_template('admin_news.html', news=news, config=globals())

@app.route('/admin/add_news', methods=['POST'])
def add_news():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    db = get_db()
    db.execute('INSERT INTO news (title) VALUES (?)', (request.form['title'],))
    db.commit()
    db.close()
    return redirect(url_for('admin_news'))

@app.route('/admin/delete_news/<int:id>')
def delete_news(id):
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    db = get_db()
    db.execute('DELETE FROM news WHERE id = ?', (id,))
    db.commit()
    db.close()
    return redirect(url_for('admin_news'))

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('admin_login'))

# ==================== AI API ====================

@app.route('/api/ai', methods=['POST'])
def ai_chat():
    data = request.get_json()
    message = data.get('message', '')

    response = get_response(message)

    return jsonify({"response": response})
        
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
