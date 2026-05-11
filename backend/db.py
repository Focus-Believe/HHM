import psycopg2, os
from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

# =========================
# CONNECT DATABASE
# =========================

conn = psycopg2.connect(
    os.environ["DATABASE_URL"]
)

cur = conn.cursor()

# =========================
# USERS TABLE
# =========================

cur.execute("""
CREATE TABLE IF NOT EXISTS users(

    id SERIAL PRIMARY KEY,

    name TEXT UNIQUE,

    password TEXT,

    last_seen TEXT DEFAULT '',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# =========================
# MESSAGES TABLE
# =========================

cur.execute("""
CREATE TABLE IF NOT EXISTS messages(

    id SERIAL PRIMARY KEY,

    sender TEXT,

    receiver TEXT,

    msg TEXT,

    time TEXT,

    seen BOOLEAN DEFAULT FALSE
)
""")

conn.commit()

# =========================
# INDEXES (FAST SEARCH)
# =========================

cur.execute("""
CREATE INDEX IF NOT EXISTS idx_sender
ON messages(sender)
""")

cur.execute("""
CREATE INDEX IF NOT EXISTS idx_receiver
ON messages(receiver)
""")

cur.execute("""
CREATE INDEX IF NOT EXISTS idx_users
ON users(name)
""")

conn.commit()

# =========================
# REGISTER
# =========================

def register(name, password):

    try:

        hashed = generate_password_hash(password)

        cur.execute(
            """
            INSERT INTO users(name, password)
            VALUES(%s,%s)
            """,
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
        """
        SELECT password
        FROM users
        WHERE name=%s
        """,
        (name,)
    )

    row = cur.fetchone()

    if row is None:
        return False

    saved_hash = row[0]

    return check_password_hash(
        saved_hash,
        password
    )

# =========================
# SAVE MESSAGE
# =========================

def save_message(
    sender,
    receiver,
    msg,
    time
):

    cur.execute(
        """
        INSERT INTO messages(
            sender,
            receiver,
            msg,
            time
        )
        VALUES(%s,%s,%s,%s)
        """,
        (
            sender,
            receiver,
            msg,
            time
        )
    )

    conn.commit()

# =========================
# GET CHAT HISTORY
# =========================

def get_messages(user1, user2):

    cur.execute(
        """
        SELECT
            sender,
            receiver,
            msg,
            time,
            seen

        FROM messages

        WHERE

        (
            sender=%s
            AND
            receiver=%s
        )

        OR

        (
            sender=%s
            AND
            receiver=%s
        )

        ORDER BY id ASC
        """,

        (
            user1,
            user2,
            user2,
            user1
        )
    )

    return cur.fetchall()

# =========================
# RECENT CHATS
# =========================

def get_recent_chats(user):

    cur.execute(
        """
        SELECT DISTINCT

        CASE
            WHEN sender=%s
            THEN receiver

            ELSE sender
        END AS chat_user

        FROM messages

        WHERE
        sender=%s
        OR
        receiver=%s

        ORDER BY chat_user
        """,

        (
            user,
            user,
            user
        )
    )

    return cur.fetchall()

# =========================
# MARK AS SEEN
# =========================

def mark_seen(sender, receiver):

    cur.execute(
        """
        UPDATE messages

        SET seen=TRUE

        WHERE
        sender=%s
        AND
        receiver=%s
        """,

        (
            sender,
            receiver
        )
    )

    conn.commit()

# =========================
# UNREAD COUNT
# =========================

def unread_count(sender, receiver):

    cur.execute(
        """
        SELECT COUNT(*)

        FROM messages

        WHERE
        sender=%s
        AND
        receiver=%s
        AND
        seen=FALSE
        """,

        (
            sender,
            receiver
        )
    )

    return cur.fetchone()[0]

# =========================
# DELETE CHAT
# =========================

def delete_chat(user1, user2):

    cur.execute(
        """
        DELETE FROM messages

        WHERE

        (
            sender=%s
            AND
            receiver=%s
        )

        OR

        (
            sender=%s
            AND
            receiver=%s
        )
        """,

        (
            user1,
            user2,
            user2,
            user1
        )
    )

    conn.commit()

# =========================
# GET ALL USERS
# =========================

def get_users():

    cur.execute(
        """
        SELECT name
        FROM users
        ORDER BY name
        """
    )

    return cur.fetchall()

# =========================
# UPDATE LAST SEEN
# =========================

def update_last_seen(user, time):

    cur.execute(
        """
        UPDATE users

        SET last_seen=%s

        WHERE name=%s
        """,

        (
            time,
            user
        )
    )

    conn.commit()

# =========================
# GET LAST SEEN
# =========================

def get_last_seen(user):

    cur.execute(
        """
        SELECT last_seen

        FROM users

        WHERE name=%s
        """,

        (user,)
    )

    row = cur.fetchone()

    if row:
        return row[0]

    return ""
