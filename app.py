from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import psycopg2
import os
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from config import *
from AIbrain import get_response
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-in-production")

# ==================== DATABASE ====================

def get_db():
    return psycopg2.connect(os.environ.get("DATABASE_URL"))

# ==================== ADMIN SECURITY ====================

def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get('admin'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return wrapper

# ==================== FILE UPLOAD ====================

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'images', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ==================== INIT ADMIN (RUN ONCE MANUALLY) ====================
# DO NOT run every deploy in production
def create_admin():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE,
            password TEXT
        )
    """)

    hashed = generate_password_hash("Darmhies@Secure2026#Shop")

    cur.execute("""
        INSERT INTO admins (username, password)
        VALUES (%s, %s)
        ON CONFLICT (username) DO NOTHING
    """, ("darmhies_admin", hashed))

    conn.commit()
    cur.close()
    conn.close()

create_admin()

# ==================== CUSTOMER ROUTES ====================

@app.route('/')
def index():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM products WHERE is_new = 1 LIMIT 6")
    featured_products = cur.fetchall()

    cur.execute("SELECT * FROM news ORDER BY id DESC")
    news = cur.fetchall()

    conn.close()

    return render_template('index.html',
                           featured_products=featured_products,
                           news=news,
                           config=globals())

@app.route('/shop')
def shop():
    conn = get_db()
    cur = conn.cursor()

    category = request.args.get('category', '')
    search = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)
    per_page = 12

    query = "SELECT * FROM products WHERE 1=1"
    params = []

    if category:
        query += " AND category = %s"
        params.append(category)

    if search:
        query += " AND name ILIKE %s"
        params.append(f"%{search}%")

    cur.execute(query, params)
    products = cur.fetchall()

    cur.execute("SELECT DISTINCT category FROM products")
    categories = cur.fetchall()

    conn.close()

    class Pagination:
        def __init__(self, items):
            self.items = items

    return render_template('shop.html',
                           products=Pagination(products),
                           categories=categories,
                           category=category,
                           search=search,
                           config=globals())

@app.route('/product/<int:id>')
def product_detail(id):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM products WHERE id = %s", (id,))
    product = cur.fetchone()

    conn.close()
    return render_template('product.html', product=product, config=globals())

# ==================== CART (SESSION BASED) ====================

@app.route('/cart')
def cart():
    cart = session.get('cart', {})
    cart_items = []
    total = 0

    if cart:
        conn = get_db()
        cur = conn.cursor()

        for pid, qty in cart.items():
            cur.execute("SELECT * FROM products WHERE id = %s", (pid,))
            p = cur.fetchone()

            if p:
                subtotal = p[2] * qty
                cart_items.append({
                    'id': pid,
                    'name': p[1],
                    'price': p[2],
                    'qty': qty,
                    'subtotal': subtotal
                })
                total += subtotal

        conn.close()

    return render_template('cart.html', cart_items=cart_items, total=total, config=globals())

@app.route('/add_to_cart/<int:id>', methods=['POST'])
def add_to_cart(id):
    cart = session.get('cart', {})
    cart[str(id)] = cart.get(str(id), 0) + 1
    session['cart'] = cart
    return jsonify({'success': True})

# ==================== CHECKOUT ====================

@app.route('/checkout')
def checkout():
    cart = session.get('cart', {})
    cart_items = []
    total = 0

    conn = get_db()
    cur = conn.cursor()

    for pid, qty in cart.items():
        cur.execute("SELECT * FROM products WHERE id = %s", (pid,))
        p = cur.fetchone()

        if p:
            subtotal = p[2] * qty
            cart_items.append({
                'name': p[1],
                'qty': qty,
                'subtotal': subtotal
            })
            total += subtotal

    conn.close()

    msg = "Hello! I want to order:\n"
    for item in cart_items:
        msg += f"- {item['name']} x{item['qty']} = ₦{item['subtotal']}\n"
    msg += f"\nTotal: ₦{total}"

    whatsapp_link = f"https://wa.me/{WHATSAPP_NUMBER}?text={msg.replace(' ', '%20')}"

    return render_template('checkout.html',
                           cart_items=cart_items,
                           total=total,
                           whatsapp_link=whatsapp_link,
                           config=globals())

# ==================== ADMIN LOGIN ====================

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db()
        cur = conn.cursor()

        cur.execute("SELECT * FROM admins WHERE username = %s", (username,))
        admin = cur.fetchone()

        conn.close()

        if admin and check_password_hash(admin[2], password):
            session['admin'] = True
            return redirect(url_for('admin_dashboard'))

        return "Invalid credentials"

    return render_template('admin_login.html', config=globals())

# ==================== ADMIN DASHBOARD ====================

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM products")
    total_products = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM news")
    total_news = cur.fetchone()[0]

    conn.close()

    return render_template('admin_dashboard.html',
                           total_products=total_products,
                           total_news=total_news,
                           config=globals())

# ==================== RUN APP ====================

if __name__ == '__main__':
    app.run(debug=True)