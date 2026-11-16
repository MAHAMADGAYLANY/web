import json, os, random, sqlite3
from pathlib import Path
import duckdb, pandas as pd
from cryptography.fernet import Fernet
from flask import Flask, flash, redirect, render_template, request, session, url_for
try:
    from diffprivlib.mechanisms import Laplace
except ImportError: Laplace = None
ROOT, DB, KEY = Path(__file__).parent, Path(__file__).parent / "database.db", Path(__file__).parent / "secret.key"; app = Flask(__name__); app.secret_key = os.getenv("FLASK_SECRET_KEY", "secure-shop-demo-secret")
USERS = {"admin": ("admin123", "Admin"), "analyst": ("analyst123", "Analyst")}
PRODUCTS = [("Aurora Headphones", 79.99, "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=600"), ("Luna Smart Watch", 129, "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=600"), ("Terra Backpack", 54.5, "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=600"), ("Nova Camera", 299, "https://images.unsplash.com/photo-1516035069371-29a1b244cc32?w=600")]
def db():
    c = sqlite3.connect(DB); c.row_factory = sqlite3.Row; return c
def enc(value):
    if not KEY.exists(): KEY.write_bytes(Fernet.generate_key())
    return Fernet(KEY.read_bytes()).encrypt(value.encode()).decode()
def dec(value): return Fernet(KEY.read_bytes()).decrypt(value.encode()).decode()
def mask(value, email=False):
    if email:
        name, domain = value.split("@", 1); return name[:1] + "***@" + domain
    return "*" * max(0, len(value) - 3) + value[-3:]
def count(): return sum(session.get("cart", {}).values())
def setup():
    c = db(); c.executescript("CREATE TABLE IF NOT EXISTS products(id INTEGER PRIMARY KEY,name TEXT,price REAL,image TEXT); CREATE TABLE IF NOT EXISTS orders(id INTEGER PRIMARY KEY,name TEXT,email TEXT,phone TEXT,address TEXT,items TEXT,total REAL,created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
    if not c.execute("SELECT COUNT(*) FROM products").fetchone()[0]: c.executemany("INSERT INTO products(name,price,image) VALUES(?,?,?)", PRODUCTS)
    c.commit(); c.close()
def home():
    c = db(); rows = c.execute("SELECT * FROM products").fetchall(); c.close(); return render_template("index.html", products=rows, cart_count=count())
def products(): return home() if request.path == "/" else render_template("products.html", products=db().execute("SELECT * FROM products").fetchall(), cart_count=count())
def add_to_cart(product_id): session.setdefault("cart", {})[str(product_id)] = session.get("cart", {}).get(str(product_id), 0) + 1; session.modified = True; flash("Product added to your cart.", "success"); return redirect(request.referrer or url_for("products"))
def remove_from_cart(product_id): session.get("cart", {}).pop(str(product_id), None); session.modified = True; return redirect(url_for("cart"))
def cart():
    c = db(); items = [{"product": p, "quantity": q, "subtotal": p["price"] * q} for i, q in session.get("cart", {}).items() if (p := c.execute("SELECT * FROM products WHERE id=?", (i,)).fetchone())]; c.close(); return render_template("cart.html", cart=items, total=sum(x["subtotal"] for x in items), cart_count=count())
def checkout():
    if not session.get("cart"): flash("Your cart is empty.", "error"); return redirect(url_for("products"))
    if request.method == "GET": return render_template("checkout.html", confirmed=False, cart_count=count())
    fields = [request.form.get(x, "").strip() for x in ("name", "email", "phone", "address")]
    if not all(fields): flash("Please complete every delivery field.", "error"); return redirect(url_for("checkout"))
    c, items, total = db(), [], 0
    for i, q in session["cart"].items():
        if p := c.execute("SELECT * FROM products WHERE id=?", (i,)).fetchone(): items.append({"name": p["name"], "quantity": q, "price": p["price"]}); total += p["price"] * q
    c.execute("INSERT INTO orders(name,email,phone,address,items,total) VALUES(?,?,?,?,?,?)", (*map(enc, fields), json.dumps(items), total)); oid = c.execute("SELECT last_insert_rowid()").fetchone()[0]; c.commit(); c.close(); session["cart"] = {}
    return render_template("checkout.html", confirmed=True, order_id=oid, total=total, cart_count=0)
def login():
    if request.method == "POST" and (u := USERS.get(request.form.get("username"))) and u[0] == request.form.get("password"): session.update(username=request.form["username"], role=u[1]); return redirect(url_for("admin_dashboard"))
    if request.method == "POST": flash("Incorrect username or password.", "error")
    return render_template("login.html")
def logout(): session.clear(); return redirect(url_for("home"))
def admin_dashboard():
    if "username" not in session: return redirect(url_for("login"))
    c = db()
    if request.method == "POST" and session["role"] == "Admin": c.execute("INSERT INTO products(name,price,image) VALUES(?,?,?)", (request.form["name"], float(request.form["price"]), request.form["image"])); c.commit()
    orders = [dict(x) for x in c.execute("SELECT * FROM orders ORDER BY id DESC")]; products = c.execute("SELECT * FROM products").fetchall(); c.close()
    for o in orders:
        o.update(name=dec(o["name"]), email=dec(o["email"]), phone=dec(o["phone"]), address=dec(o["address"]))
        if session["role"] == "Analyst": o.update(email=mask(o["email"], True), phone=mask(o["phone"]), address=mask(o["address"]))
    frame = pd.DataFrame(orders); stats = duckdb.sql("SELECT COUNT(*) n, COALESCE(SUM(total),0) s FROM frame").fetchall()[0]; noisy = float(stats[1]) + (Laplace(epsilon=1, sensitivity=10).randomise(float(stats[1])) - float(stats[1]) if Laplace else random.expovariate(.1) - random.expovariate(.1))
    return render_template("admin.html", orders=orders, products=products, total_orders=stats[0], total_sales=float(frame["total"].sum()) if not frame.empty else 0, noisy_sales=max(0, round(noisy, 2)), role=session["role"], username=session["username"])
app.add_url_rule("/", "home", home); app.add_url_rule("/products", "products", products); app.add_url_rule("/cart", "cart", cart); app.add_url_rule("/cart/add/<int:product_id>", "add_to_cart", add_to_cart, methods=["POST"]); app.add_url_rule("/cart/remove/<int:product_id>", "remove_from_cart", remove_from_cart, methods=["POST"]); app.add_url_rule("/checkout", "checkout", checkout, methods=["GET", "POST"]); app.add_url_rule("/login", "login", login, methods=["GET", "POST"]); app.add_url_rule("/logout", "logout", logout); app.add_url_rule("/admin", "admin_dashboard", admin_dashboard, methods=["GET", "POST"])
if __name__ == "__main__": setup(); app.run(debug=True)
