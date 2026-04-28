import psycopg2, os

conn = psycopg2.connect(os.environ["DATABASE_URL"])
cur = conn.cursor()

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


def register(name, password):
    try:
        cur.execute("INSERT INTO users VALUES(%s,%s)", (name,password))
        conn.commit()
        return True
    except:
        conn.rollback()
        return False


def login(name, password):
    cur.execute("SELECT * FROM users WHERE name=%s AND password=%s",(name,password))
    return cur.fetchone() is not None


def save(sender, receiver, msg, time):
    cur.execute(
        "INSERT INTO messages VALUES(%s,%s,%s,%s)",
        (sender,receiver,msg,time)
    )
    conn.commit()
