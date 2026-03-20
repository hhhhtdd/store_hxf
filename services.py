from db import get_conn
from datetime import datetime

def add_log(code, name, op, num=0, price_in=0, price_out=0):
    conn = get_conn()
    c = conn.cursor()

    c.execute("""
    INSERT INTO logs (time, code, name, operation, num, price_in, price_out)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        code, name, op, num, price_in, price_out
    ))

    conn.commit()
    conn.close()


def get_goods(keyword):
    conn = get_conn()
    c = conn.cursor()

    c.execute("""
    SELECT * FROM goods
    WHERE code=? OR name LIKE ?
    """, (keyword, f"%{keyword}%"))

    result = c.fetchall()
    conn.close()
    return result


def update_stock(code, delta):
    conn = get_conn()
    c = conn.cursor()

    c.execute("SELECT stock,name FROM goods WHERE code=?", (code,))
    row = c.fetchone()
    if not row:
        return None, "商品不存在"

    stock, name = row
    new_stock = stock + delta

    if new_stock < 0:
        return None, "库存不足"

    c.execute("UPDATE goods SET stock=? WHERE code=?", (new_stock, code))
    conn.commit()
    conn.close()

    return new_stock, name


def get_all_goods():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM goods")
    data = c.fetchall()
    conn.close()
    return data