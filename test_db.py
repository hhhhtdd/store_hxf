import sqlite3
from db import init_db, get_conn

def test_insertion():
    init_db()
    conn = get_conn()
    c = conn.cursor()

    # 插入一个模拟商品
    c.execute("INSERT OR REPLACE INTO goods (code, name, type, stock, warn_line, price_in, price_out) VALUES (?, ?, ?, ?, ?, ?, ?)",
              ('TEST001', '测试商品', '文具', 100, 10, 1.0, 2.0))

    # 模拟出库
    c.execute("INSERT INTO record (code, name, type, qty) VALUES (?, ?, ?, ?)",
              ('TEST001', '测试商品', 'out', 5))

    conn.commit()

    # 查询
    c.execute("SELECT * FROM record WHERE code='TEST001'")
    row = c.fetchone()
    print("Inserted Row:", row)

    conn.close()

if __name__ == "__main__":
    test_insertion()
