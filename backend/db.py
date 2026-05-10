import psycopg2, os
from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

conn = psycopg2.connect(os.environ["DATABASE_URL"])
cur = conn.cursor()

# =========================
# TABLES
# =========================

cur.execute("""
CREATE TABLE IF NOT EXISTS users(
    name TEXT UNIQUE,
    password TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS messages(
    sender TEXT,
    receiver TEXT,
    msg TEXT,
    time TEXT
)
""")

conn.commit()

# =========================
# REGISTER
# =========================

def register(name, password):

    try:

        # password hash
        hashed = generate_password_hash(password)

        cur.execute(
            "INSERT INTO users VALUES(%s,%s)",
            (name, hashed)
        )

        conn.commit()

        return True

    except:

        conn.rollback()

        return False

# =========================
# LOGIN
# =========================

def login(name, password):

    cur.execute(
        "SELECT password FROM users WHERE name=%s",
        (name,)
    )

    row = cur.fetchone()

    # user not found
    if row is None:
        return False

    saved_hash = row[0]

    # verify password
    return check_password_hash(
        saved_hash,
        password
    )

# =========================
# SAVE MESSAGE
# =========================

def save(sender, receiver, msg, time):

    cur.execute(
        "INSERT INTO messages VALUES(%s,%s,%s,%s)",
        (sender, receiver, msg, time)
    )

    conn.commit()
