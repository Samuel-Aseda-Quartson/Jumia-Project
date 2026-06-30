import sqlite3


def init_db():
    conn = sqlite3.connect('jumia_tracker.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT    NOT NULL,
            email    TEXT    NOT NULL UNIQUE,
            password TEXT    NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id      INTEGER NOT NULL,
            name         TEXT    NOT NULL,
            url          TEXT    NOT NULL,
            price        REAL    NOT NULL,
            last_checked TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    conn.commit()
    conn.close()


init_db()