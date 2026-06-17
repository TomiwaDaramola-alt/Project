from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import psycopg2
import os
from werkzeug.utils import secure_filename
from functools import wraps

app = Flask(__name__)

# ==============================
# SECURITY
# ==============================
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-this")

# ==============================
# DATABASE CONNECTION (FIXED)
# ==============================
def get_db():
    database_url = os.environ.get("DATABASE_URL")

    if not database_url:
        raise Exception("DATABASE_URL is missing in environment variables")

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
# INIT DB (SAFE VERSION)
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

        print("DB initialized successfully")

    except Exception as e:
        print("DB init error:", e)

# IMPORTANT: only run after safe env check
if os.environ.get("DATABASE_URL"):
    init_db()
else:
    print("DATABASE_URL not set yet, skipping DB init")

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

    return render_template(
        "index.html",
        featured_products=featured_products,
        news=news
    )

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

    return render_template("shop.html", products=products, categories=categories)

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

    return render_template("product.html", product=product)

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

    return render_template("admin_login.html")

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

    return render_template(
        "admin_dashboard.html",
        total_products=total_products,
        total_news=total_news
    )

# ==============================
# RUN APP
# ==============================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)