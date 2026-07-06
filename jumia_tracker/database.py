import psycopg2
import psycopg2.extras
import os

# ============================================================
# CONNECTION SETUP
# Load DATABASE_URL from config.txt
# Never hardcode credentials in code
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Try environment variable first (Render production)
# Fall back to config.txt for local development
DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    # Not on Render — read from local config.txt
    config = {}
    config_path = os.path.join(BASE_DIR, "config.txt")
    with open(config_path, "r") as cf:
        for line in cf:
            if ": " in line:
                key, value = line.strip().split(": ", 1)
                config[key] = value
    DATABASE_URL = config["DATABASE_URL"]


def get_conn():
    # Creates and returns a new database connection
    # psycopg2.connect() → connects to PostgreSQL using the URL
    # cursor_factory → makes rows behave like dictionaries
    # Same role as sqlite3.Row in the old version
    conn = psycopg2.connect(DATABASE_URL)
    return conn


def init_db():
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id       SERIAL PRIMARY KEY,
            username TEXT   NOT NULL,
            email    TEXT   NOT NULL UNIQUE,
            password BYTEA  NOT NULL,
            phone    TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id           SERIAL PRIMARY KEY,
            user_id      INTEGER NOT NULL REFERENCES users(id),
            name         TEXT    NOT NULL,
            url          TEXT    NOT NULL,
            price        REAL    NOT NULL,
            last_checked TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS price_history (
            id         SERIAL PRIMARY KEY,
            product_id INTEGER NOT NULL REFERENCES products(id),
            price      REAL    NOT NULL,
            checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    cursor.close()
    conn.close()


def create_user(username, email, password, phone):
    conn = get_conn()
    # RealDictCursor → rows come back as real Python dictionaries
    # Same behaviour as sqlite3.Row — access by column name
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        cursor.execute('''
            INSERT INTO users (username, email, password, phone)
            VALUES (%s, %s, %s, %s)
        ''', (username, email, password, phone))
        # %s instead of ? → PostgreSQL uses %s as placeholder
        # Same security purpose — prevents SQL injection
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except psycopg2.errors.UniqueViolation:
        # PostgreSQL raises UniqueViolation instead of IntegrityError
        # Same concept — email already exists
        conn.rollback()
        cursor.close()
        conn.close()
        return False


def find_user_by_email(email):
    conn = get_conn()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute('''
        SELECT * FROM users WHERE email = %s
    ''', (email,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result


def get_products(user_id):
    conn = get_conn()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute('''
        SELECT * FROM products WHERE user_id = %s
    ''', (user_id,))
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results


def add_product(user_id, name, url, price):
    conn = get_conn()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute('''
        INSERT INTO products (user_id, name, url, price)
        VALUES (%s, %s, %s, %s)
        RETURNING id
    ''', (user_id, name, url, price))
    # RETURNING id → PostgreSQL returns the new row's id immediately
    # Replaces cursor.lastrowid from SQLite
    product_id = cursor.fetchone()['id']
    conn.commit()
    cursor.close()
    conn.close()
    return product_id


def update_product(product_id, name, price):
    conn = get_conn()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute('''
        UPDATE products
        SET name         = %s,
            price        = %s,
            last_checked = CURRENT_TIMESTAMP
        WHERE id = %s
    ''', (name, price, product_id))
    conn.commit()
    cursor.close()
    conn.close()


def add_price_history(product_id, price):
    conn = get_conn()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute('''
        INSERT INTO price_history (product_id, price)
        VALUES (%s, %s)
    ''', (product_id, price))
    conn.commit()
    cursor.close()
    conn.close()


def get_price_history(product_id):
    conn = get_conn()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute('''
        SELECT price, checked_at
        FROM price_history
        WHERE product_id = %s
        ORDER BY checked_at ASC
    ''', (product_id,))
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results


def delete_product(product_id, user_id):
    conn = get_conn()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute('''
        DELETE FROM price_history WHERE product_id = %s
    ''', (product_id,))
    cursor.execute('''
        DELETE FROM products WHERE id = %s AND user_id = %s
    ''', (product_id, user_id))
    conn.commit()
    cursor.close()
    conn.close()


def find_product_by_url(user_id, url):
    conn = get_conn()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute('''
        SELECT id FROM products
        WHERE user_id = %s AND url = %s
    ''', (user_id, url))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result


def get_all_products():
    conn = get_conn()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute('''
        SELECT products.*, users.username, users.email, users.phone
        FROM products
        JOIN users ON products.user_id = users.id
        WHERE products.name != 'Fetching product details...'
        AND products.name != 'Could not fetch product'
    ''')
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results


def get_last_price(product_id):
    conn = get_conn()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute('''
        SELECT price FROM price_history
        WHERE product_id = %s
        ORDER BY checked_at DESC
        LIMIT 1
    ''', (product_id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    if result:
        return result['price']
    return None


def get_price_change(product_id):
    conn = get_conn()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute('''
        SELECT price FROM price_history
        WHERE product_id = %s
        ORDER BY checked_at DESC
        LIMIT 2
    ''', (product_id,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    if len(rows) < 2:
        return None

    current  = rows[0]['price']
    previous = rows[1]['price']

    if current < previous:
        return {"direction": "down", "diff": previous - current}
    elif current > previous:
        return {"direction": "up", "diff": current - previous}
    else:
        return {"direction": "same", "diff": 0}
