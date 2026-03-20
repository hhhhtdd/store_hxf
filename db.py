import sqlite3

DB_NAME = "goods.db"

def get_conn():
    return sqlite3.connect(DB_NAME)

def init_db():
    conn = get_conn()
    c = conn.cursor()
    
    c.execute("""
    CREATE TABLE IF NOT EXISTS goods (
        code TEXT PRIMARY KEY,
        name TEXT,
        type TEXT,
        stock INTEGER,
        warn_line INTEGER,
        price_in REAL,
        price_out REAL
    )
    """)

    c.execute("""
            CREATE TABLE IF NOT EXISTS record (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT,
                name TEXT,
                type TEXT,   -- in / out
                qty INTEGER,
                time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
    
    c.execute("""
    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        time TEXT,
        code TEXT,
        name TEXT,
        operation TEXT,
        num INTEGER,
        price_in REAL,
        price_out REAL
    )
    """)

    # ===== 用户表（权限）=====
    c.execute("""
    CREATE TABLE IF NOT EXISTS user (
        username TEXT PRIMARY KEY,
        password TEXT,
        role TEXT   -- admin / staff
    )
    """)

    # 默认账号（只执行一次）
    c.execute("SELECT * FROM user WHERE username='admin'")
    if not c.fetchone():
        c.execute("INSERT INTO user VALUES ('admin','12345','admin')")
        c.execute("INSERT INTO user VALUES ('staff','123456','staff')")

    conn.commit()
    conn.close()


def search_goods(keyword):
    conn = get_conn()
    c = conn.cursor()

    c.execute("""
        SELECT id, name, price, stock
        FROM goods
        WHERE name LIKE ?
    """, (f"%{keyword}%",))

    data = c.fetchall()
    conn.close()
    return data