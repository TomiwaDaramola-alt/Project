from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import psycopg2
import os
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from config import *
from AIbrain import get_response

app = Flask(__name__)

# ==============================
# SECURITY CONFIG
# ==============================
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-this")

# ==============================
# DATABASE CONNECTION
# ==============================
def get_db():
    database_url = os.environ.get("DATABASE_URL")

    if not database_url:
        raise Exception("DATABASE_URL not set")

    return psycopg2.connect(database_url, sslmode="require", connect_timeout=10)

# ==============================
# ADMIN PROTECTION
# ==============================
def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("admin"):
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return wrapper

# ==============================
# UPLOAD CONFIG
# ==============================
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "images", "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# ==============================
# SAFE DB INIT (RUN ONCE ONLY)
# ==============================
def init_db():
    try:
        conn = get_db()
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id SERIAL PRIMARY KEY,
                name TEXT,
                price NUMERIC,
                compare_price NUMERIC,
                description TEXT,
                image_file TEXT,
                category TEXT,
                is_new INTEGER DEFAULT 0
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS news (
                id SERIAL PRIMARY KEY,
                title TEXT
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS admins (
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE,
                password TEXT
            )
        """)

        conn.commit()
        cur.close()
        conn.close()

    except Exception as e:
        print("DB init error:", e)

# DO NOT CRASH APP ON START
init_db()

# ==============================
# HOME
# ==============================
@app.route("/")
def index():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM products WHERE is_new = 1 LIMIT 6")
    featured_products = cur.fetchall()

    cur.execute("SELECT * FROM news ORDER BY id DESC")
    news = cur.fetchall()

    conn.close()

    return render_template("index.html", featured_products=featured_products, news=news, config=globals())

# ==============================
# SHOP
# ==============================
@app.route("/shop")
def shop():
    conn = get_db()
    cur = conn.cursor()

    category = request.args.get("category", "")
    search = request.args.get("search", "")

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

    return render_template("shop.html", products=products, categories=categories, config=globals())

# ==============================
# PRODUCT
# ==============================
@app.route("/product/<int:id>")
def product_detail(id):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM products WHERE id = %s", (id,))
    product = cur.fetchone()

    conn.close()

    return render_template("product.html", product=product, config=globals())

# ==============================
# CART
# ==============================
@app.route("/cart")
def cart():
    cart = session.get("cart", {})
    items = []
    total = 0

    if cart:
        conn = get_db()
        cur = conn.cursor()

        for pid, qty in cart.items():
            cur.execute("SELECT * FROM products WHERE id = %s", (pid,))
            p = cur.fetchone()

            if p:
                subtotal = float(p[2]) * qty
                items.append({
                    "id": pid,
                    "name": p[1],
                    "price": float(p[2]),
                    "qty": qty,
                    "subtotal": subtotal
                })
                total += subtotal

        conn.close()

    return render_template("cart.html", cart_items=items, total=total, config=globals())

# ==============================
# ADD TO CART
# ==============================
@app.route("/add_to_cart/<int:id>", methods=["POST"])
def add_to_cart(id):
    cart = session.get("cart", {})
    cart[str(id)] = cart.get(str(id), 0) + 1
    session["cart"] = cart
    return jsonify({"success": True})

# ==============================
# CHECKOUT
# ==============================
@app.route("/checkout")
def checkout():
    cart = session.get("cart", {})
    items = []
    total = 0

    conn = get_db()
    cur = conn.cursor()

    for pid, qty in cart.items():
        cur.execute("SELECT * FROM products WHERE id = %s", (pid,))
        p = cur.fetchone()

        if p:
            subtotal = float(p[2]) * qty
            items.append({"name": p[1], "qty": qty})
            total += subtotal

    conn.close()

    msg = "Hello, I want to order:\n"
    for i in items:
        msg += f"- {i['name']} x{i['qty']}\n"

    whatsapp_link = f"https://wa.me/{WHATSAPP_NUMBER}?text={msg}"

    return render_template("checkout.html", cart_items=items, total=total, whatsapp_link=whatsapp_link, config=globals())

# ==============================
# ADMIN LOGIN
# ==============================
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        cur = conn.cursor()

        cur.execute("SELECT * FROM admins WHERE username = %s", (username,))
        admin = cur.fetchone()

        conn.close()

        if admin and admin[2] == password:
            session["admin"] = True
            return redirect("/admin/dashboard")

        return "Invalid login"

    return render_template("admin_login.html", config=globals())

# ==============================
# ADMIN DASHBOARD
# ==============================
@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM products")
    total_products = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM news")
    total_news = cur.fetchone()[0]

    conn.close()

    return render_template("admin_dashboard.html",
                           total_products=total_products,
                           total_news=total_news,
                           config=globals())

# ==============================
# RUN
# ==============================
if __name__ == "__main__":
    app.run()