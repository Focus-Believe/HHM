import psycopg2
import os
from werkzeug.security import generate_password_hash, check_password_hash

# =========================
# DB CONNECTION
# =========================
conn = psycopg2.connect(os.environ["DATABASE_URL"])
cur = conn.cursor()


# =========================
# USERS TABLE
# =========================
cur.execute("""
CREATE TABLE IF NOT EXISTS users(

    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE,
    password TEXT,
    last_seen TEXT DEFAULT ''
)
""")


# =========================
# MESSAGES TABLE (FULL FEATURED)
# =========================
cur.execute("""
CREATE TABLE IF NOT EXISTS messages(

    id SERIAL PRIMARY KEY,

    sender TEXT,
    receiver TEXT,
    msg TEXT,
    time TEXT,

    seen BOOLEAN DEFAULT FALSE,
    delivered BOOLEAN DEFAULT FALSE
)
""")


# =========================
# INDEXES (FAST CHAT)
# =========================
cur.execute("CREATE INDEX IF NOT EXISTS idx_sender ON messages(sender)")
cur.execute("CREATE INDEX IF NOT EXISTS idx_receiver ON messages(receiver)")
cur.execute("CREATE INDEX IF NOT EXISTS idx_users ON users(name)")

conn.commit()


# =========================
# REGISTER USER
# =========================
def register(name, password):

    try:
        hashed = generate_password_hash(password)

        cur.execute("""
            INSERT INTO users(name, password)
            VALUES(%s, %s)
        """, (name, hashed))

        conn.commit()
        return True

    except:
        conn.rollback()
        return False


# =========================
# LOGIN USER
# =========================
def login(name, password):

    cur.execute("""
        SELECT password
        FROM users
        WHERE name=%s
    """, (name,))

    row = cur.fetchone()

    if not row:
        return False

    return check_password_hash(row[0], password)


# =========================
# SAVE MESSAGE
# =========================
def save_message(sender, receiver, msg, time):

    cur.execute("""
        INSERT INTO messages(sender, receiver, msg, time)
        VALUES(%s, %s, %s, %s)
    """, (sender, receiver, msg, time))

    conn.commit()


# =========================
# MARK DELIVERED
# =========================
def mark_delivered(sender, receiver):

    cur.execute("""
        UPDATE messages
        SET delivered=TRUE
        WHERE sender=%s AND receiver=%s
    """, (sender, receiver))

    conn.commit()


# =========================
# MARK SEEN
# =========================
def mark_seen(sender, receiver):

    cur.execute("""
        UPDATE messages
        SET seen=TRUE
        WHERE sender=%s AND receiver=%s
    """, (sender, receiver))

    conn.commit()


# =========================
# GET CHAT HISTORY (2 USERS)
# =========================
def get_messages(user1, user2):

    cur.execute("""
        SELECT sender, receiver, msg, time, seen, delivered
        FROM messages
        WHERE
            (sender=%s AND receiver=%s)
        OR
            (sender=%s AND receiver=%s)
        ORDER BY id ASC
    """, (user1, user2, user2, user1))

    return cur.fetchall()


# =========================
# RECENT CHATS (LIKE WHATSAPP)
# =========================
def get_recent_chats(user):

    cur.execute("""
        SELECT DISTINCT ON (
            CASE
                WHEN sender=%s THEN receiver
                ELSE sender
            END
        )

        CASE
            WHEN sender=%s THEN receiver
            ELSE sender
        END AS chat_user,

        msg,
        time

        FROM messages

        WHERE sender=%s OR receiver=%s

        ORDER BY chat_user, id DESC
    """, (user, user, user, user))

    return cur.fetchall()


# =========================
# UNREAD COUNT
# =========================
def unread_count(user, other):

    cur.execute("""
        SELECT COUNT(*)
        FROM messages
        WHERE sender=%s
        AND receiver=%s
        AND seen=FALSE
    """, (other, user))

    return cur.fetchone()[0]


# =========================
# GET ALL USERS
# =========================
def get_users():

    cur.execute("""
        SELECT name FROM users
        ORDER BY name ASC
    """)

    return cur.fetchall()


# =========================
# UPDATE LAST SEEN
# =========================
def update_last_seen(name, time):

    cur.execute("""
        UPDATE users
        SET last_seen=%s
        WHERE name=%s
    """, (time, name))

    conn.commit()


# =========================
# GET LAST SEEN
# =========================
def get_last_seen(name):

    cur.execute("""
        SELECT last_seen
        FROM users
        WHERE name=%s
    """, (name,))

    row = cur.fetchone()

    return row[0] if row else ""
