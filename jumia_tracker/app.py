from flask import Flask, render_template, request, redirect, url_for, flash, session
import bcrypt
# session  → dictionary Flask uses to remember user across requests
# bcrypt   → handles password hashing and verification

app = Flask(__name__)
app.secret_key = "dev-secret-key-change-in-production"

# TEMPORARY USER STORE
# Phase 6 replaces this with a real database table
# For now, a Python list that holds user dictionaries
# IMPORTANT: this resets every time Flask restarts
# That is expected behaviour for now
users = []
# users is a module-level variable
# data type: list of dictionaries
# each dictionary will look like:
# {
#     "id": 1,
#     "name": "Samuel",
#     "email": "samuel@example.com",
#     "password": b"$2b$12$hashedvalue..."  ← bytes, not string
# }


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/products")
def view_products():
    # ROUTE PROTECTION
    # Check session before doing anything else
    if "user_id" not in session:
        flash("Please log in to view your products.", "danger")
        return redirect(url_for("login"))

    products = [
        {
            "name": "Samsung 55 Inch TV",
            "price": 3500.00,
            "url": "https://www.jumia.com.gh/samsung-tv"
        },
        {
            "name": "iPhone 14 Pro",
            "price": 9200.00,
            "url": "https://www.jumia.com.gh/iphone-14"
        },
    ]
    return render_template("products.html", products=products)


@app.route("/add-product", methods=["GET", "POST"])
def add_product():
    # ROUTE PROTECTION
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

        flash("Product added successfully!", "success")
        return redirect(url_for("view_products"))


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "GET":
        return render_template("signup.html")

    if request.method == "POST":
        # EXTRACT
        # Get all three fields from the submitted form
        name     = request.form.get("name")
        email    = request.form.get("email")
        password = request.form.get("password")
        # data types: all strings (or None if missing)

        # VALIDATE
        # Check 1: all fields must be present
        if not name or not email or not password:
            flash("All fields are required.", "danger")
            return render_template("signup.html")

        # Check 2: email must not already exist
        # Loop through users list and check each email
        # In Phase 6: this becomes a database query
        for user in users:
            if user["email"] == email:
                flash("An account with that email already exists.", "danger")
                return render_template("signup.html")

        # HASH THE PASSWORD
        # Never store the raw password
        # bcrypt.hashpw requires bytes — encode() converts string to bytes
        password_bytes  = password.encode("utf-8")
        # password_bytes data type: bytes e.g. b"mypassword123"

        salt            = bcrypt.gensalt()
        # salt: random bytes added before hashing
        # prevents two users with same password having same hash
        # data type: bytes

        hashed_password = bcrypt.hashpw(password_bytes, salt)
        # hashed_password data type: bytes
        # e.g. b"$2b$12$Kx8Ge7XZqW9mNpL..."
        # this is what gets stored — never the original password

        # CREATE NEW USER DICTIONARY
        new_user = {
            "id":       len(users) + 1,
            # id: integer — simple counter for now
            # Phase 6: database generates this automatically

            "name":     name,
            "email":    email,
            "password": hashed_password
            # storing hashed bytes — never the original string
        }

        # SAVE TO TEMPORARY STORE
        # Phase 6: this becomes database.save(new_user)
        users.append(new_user)

        # SUCCESS
        flash("Account created successfully. Please log in.", "success")
        return redirect(url_for("login"))
        # Redirect to login — not products
        # Signup does not mean logged in
        # User must authenticate separately

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "GET":
        return render_template("login.html")

    if request.method == "POST":

        # EXTRACT
        # Get credentials from submitted form
        email    = request.form.get("email")
        password = request.form.get("password")
        # data types: strings (or None if missing)

        # VALIDATE
        # Check both fields are present
        if not email or not password:
            flash("All fields are required.", "danger")
            return render_template("login.html")

        # FIND USER
        # Search the users list for a matching email
        # In Phase 6: this becomes a database query
        # e.g. user = db.query("SELECT * FROM users WHERE email = ?", email)
        found_user = None
        # found_user data type: dictionary or None

        for user in users:
            if user["email"] == email:
                found_user = user
                break
                # break stops the loop immediately once match is found
                # no point checking remaining users

        # If no user found with that email
        if found_user is None:
            # Vague error — never reveal which field failed
            flash("Invalid credentials. Please try again.", "danger")
            return render_template("login.html")

        # VERIFY PASSWORD
        # bcrypt.checkpw hashes the submission and compares to stored hash
        # Returns True if match, False if not
        password_bytes = password.encode("utf-8")
        # encode() converts string to bytes — bcrypt requires bytes

        password_match = bcrypt.checkpw(password_bytes, found_user["password"])
        # password_match data type: boolean (True or False)

        if not password_match:
            # Same vague error — attacker cannot tell which field failed
            flash("Invalid credentials. Please try again.", "danger")
            return render_template("login.html")

        # CREATE SESSION
        # Password matched — user is authenticated
        # Store identifying information in the session
        # Flask signs this with app.secret_key and sends it as a cookie
        session["user_id"]   = found_user["id"]
        session["user_name"] = found_user["name"]
        # These values are now available on every future request
        # This is how Flask remembers who you are

        # SUCCESS
        flash(f"Welcome back, {found_user['name']}!", "success")
        # f-string → inserts found_user["name"] into the message
        # data type of full string: string

        # POST/Redirect/GET — redirect after successful POST
        return redirect(url_for("view_products"))

@app.route("/logout")
def logout():
    # session.clear() removes ALL data from the session
    # The cookie becomes empty — user_id is gone
    # Next request to a protected route → redirected to login
    session.clear()

    flash("You have been logged out.", "success")
    return redirect(url_for("login"))
    # Always redirect after logout — never render a page directly
    # POST/Redirect/GET principle applies here too


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")