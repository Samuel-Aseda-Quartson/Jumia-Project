from flask import Flask, render_template, request, redirect, url_for, flash, session
import bcrypt
import database
import scraper
import os
import threading

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
# os.environ.get() → reads SECRET_KEY from environment on Render
# second argument → fallback value for local development
# On Render, always set a real SECRET_KEY environment variable


@app.route("/")
def home():
    products      = None
    price_changes = {}

    if "user_id" in session:
        products = database.get_products(session["user_id"])

        # Build a dictionary of price changes keyed by product id
        # Template uses this to show green/red price indicators
        # e.g. price_changes[3] = {"direction": "down", "diff": 91.0}
        for product in products:
            change = database.get_price_change(product['id'])
            price_changes[product['id']] = change

    return render_template("home.html", products=products, price_changes=price_changes)

@app.route("/products")
def view_products():
    if "user_id" not in session:
        flash("Please log in to view your products.", "danger")
        return redirect(url_for("login"))
    products = database.get_products(session["user_id"])
    return render_template("products.html", products=products)


@app.route("/add-product", methods=["GET", "POST"])
def add_product():
    if "user_id" not in session:
        flash("Please log in to add products.", "danger")
        return redirect(url_for("login"))

    if request.method == "GET":
        return render_template("add_product.html")

    if request.method == "POST":
        jumia_url = request.form.get("jumia_url")

        if not jumia_url:
            flash("Please enter a Jumia URL.", "danger")
            return render_template("add_product.html")

        if "jumia.com" not in jumia_url:
            flash("Please enter a valid Jumia URL.", "danger")
            return render_template("add_product.html")

        # Check if this user already tracks this exact URL
        # Prevents duplicate entries for the same product
        existing = database.find_product_by_url(session["user_id"], jumia_url)
        if existing:
            flash("You are already tracking this product.", "danger")
            return render_template("add_product.html")


        # Save placeholder immediately — user does not wait
        product_id = database.add_product(
            user_id=session["user_id"],
            name="Fetching product details...",
            url=jumia_url,
            price=0.00
        )

        # Background thread scrapes the real data
        def scrape_and_update(pid, url):
            scraped = scraper.scrape(url)
            if scraped:
                database.update_product(pid, scraped["name"], scraped["price"])
                database.add_price_history(pid, scraped["price"])
            else:
                database.update_product(pid, "Could not fetch product", 0.00)

        thread = threading.Thread(
            target=scrape_and_update,
            args=(product_id, jumia_url),
            daemon=True
        )
        thread.start()

        flash("Product added. Fetching details in background — refresh in a few seconds.", "success")
        return redirect(url_for("home"))


@app.route("/delete-product/<int:product_id>", methods=["POST"])
def delete_product(product_id):
    if "user_id" not in session:
        flash("Please log in.", "danger")
        return redirect(url_for("login"))

    database.delete_product(product_id, session["user_id"])
    flash("Product removed.", "success")
    return redirect(url_for("home"))


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "GET":
        return render_template("signup.html")

    if request.method == "POST":
        name     = request.form.get("name")
        email    = request.form.get("email")
        password = request.form.get("password")

        if not name or not email or not password:
            flash("All fields are required.", "danger")
            return render_template("signup.html")

      # Get phone number from the form
        phone = request.form.get("phone")

        if not name or not email or not password or not phone:
            flash("All fields are required.", "danger")
            return render_template("signup.html")

        existing_user = database.find_user_by_email(email)
        if existing_user:
            flash("An account with that email already exists.", "danger")
            return render_template("signup.html")

        password_bytes  = password.encode("utf-8")
        salt            = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password_bytes, salt)

        # Pass phone number into create_user
        success = database.create_user(name, email, hashed_password, phone)

        if not success:
            flash("An account with that email already exists.", "danger")
            return render_template("signup.html")

        flash("Account created successfully. Please log in.", "success")
        return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    if request.method == "POST":
        email    = request.form.get("email")
        password = request.form.get("password")

        if not email or not password:
            flash("All fields are required.", "danger")
            return render_template("login.html")

        found_user = database.find_user_by_email(email)

        if found_user is None:
            flash("Invalid credentials. Please try again.", "danger")
            return render_template("login.html")

        password_bytes = password.encode("utf-8")
        
        # Convert the database password from memoryview to standard bytes
        hashed_password = bytes(found_user["password"])
        
        # Now pass the clean bytes object to bcrypt
        password_match = bcrypt.checkpw(password_bytes, hashed_password)

        if not password_match:
            flash("Invalid credentials. Please try again.", "danger")
            return render_template("login.html")

        session["user_id"]   = found_user["id"]
        session["user_name"] = found_user["username"]

        flash(f"Welcome back, {found_user['username']}!", "success")
        return redirect(url_for("home"))

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")