import tkinter as tk
from tkinter import ttk
from tkinter.simpledialog import askinteger
from db import get_conn


class MainWindow:

    def __init__(self, root):
        self.root = root
        self.root.title("理工文具店管理系统")
        self.root.geometry("1200x900")

        self.build_ui()
        self.load_data()
        self.load_records()


    def open_admin(self):
        import tkinter.simpledialog as sd
        from db import get_conn

        username = sd.askstring("登录", "用户名")
        password = sd.askstring("登录", "密码", show="*")

        if not username or not password:
            return

        conn = get_conn()
        c = conn.cursor()

        c.execute("SELECT role FROM user WHERE username=? AND password=?", (username, password))
        row = c.fetchone()
        conn.close()

        if not row:
            tk.messagebox.showerror("错误", "账号或密码错误")
            return

        role = row[0]

        win = tk.Toplevel(self.root)

        # ⭐ 传入权限
        from ui.admin_window import AdminWindow
        AdminWindow(win, role)
    # ================= UI =================
    def build_ui(self):

        # ===== 顶部工具栏 =====
        top_bar = ttk.Frame(self.root)
        top_bar.pack(fill=tk.X, padx=10, pady=5)

        ttk.Button(top_bar, text="后台管理", command=self.open_admin).pack(side=tk.RIGHT)
        # ===== 输入框 =====
        top_frame = ttk.Frame(self.root)
        top_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(top_frame, text="商品编码：").pack(side=tk.LEFT)

        self.entry = ttk.Entry(top_frame)
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.entry.focus_set()

        # ===== 绑定快捷键 =====
        self.entry.bind("<Return>", lambda e: self.process_stock("out"))
        self.entry.bind("<Shift-Return>", lambda e: self.process_stock("in"))

        # ===== 商品表 =====
        columns = ("code", "name", "stock", "price")

        self.tree = ttk.Treeview(self.root, columns=columns, show="headings")

        self.tree.heading("code", text="编码")
        self.tree.heading("name", text="名称")
        self.tree.heading("stock", text="库存")
        self.tree.heading("price", text="售价")

        for col in columns:
            self.tree.column(col, anchor=tk.CENTER, width=120)

        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # ===== 当前商品 =====
        info_frame = ttk.LabelFrame(self.root, text="当前商品")
        info_frame.pack(fill=tk.X, padx=10, pady=5)

        self.current_label = tk.StringVar()
        self.current_label.set("暂无")

        ttk.Label(info_frame, textvariable=self.current_label).pack(anchor="w", padx=5)

        # ===== 近期记录 =====
        record_frame = ttk.LabelFrame(self.root, text="近期记录")
        record_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        columns = ("时间", "编码", "名称", "类型", "数量")

        self.record_table = ttk.Treeview(record_frame, columns=columns, show="headings")

        for col in columns:
            self.record_table.heading(col, text=col)
            self.record_table.column(col, anchor=tk.CENTER, width=100)

        self.record_table.pack(fill=tk.BOTH, expand=True)

    # ================= 商品数据 =================
    def load_data(self):

        for i in self.tree.get_children():
            self.tree.delete(i)

        conn = get_conn()
        c = conn.cursor()

        c.execute("SELECT code, name, stock, price_out FROM goods")

        for row in c.fetchall():
            self.tree.insert("", tk.END, values=row)

        conn.close()

    # ================= 记录数据 =================
    def load_records(self):

        for i in self.record_table.get_children():
            self.record_table.delete(i)

        conn = get_conn()
        c = conn.cursor()

        c.execute("""
        SELECT time, code, name, type, qty
        FROM record
        ORDER BY id DESC
        LIMIT 20
        """)

        for row in c.fetchall():
            self.record_table.insert("", tk.END, values=row)

        conn.close()

    # ================= 核心业务 =================
    def process_stock(self, mode):

        code = self.entry.get().strip()
        if not code:
            return

        conn = get_conn()
        c = conn.cursor()

        # 查询商品
        c.execute("SELECT name, stock, price_out FROM goods WHERE code=?", (code,))
        row = c.fetchone()

        if not row:
            self.current_label.set(f"❌ 商品不存在: {code}")
            conn.close()
            return

        name, stock, price = row

        # 输入数量
        qty = askinteger("数量", "输入数量", minvalue=1)
        if not qty:
            conn.close()
            return

        # 库存检查
        if mode == "out" and stock < qty:
            self.current_label.set("❌ 库存不足")
            conn.close()
            return

        # 更新库存
        if mode == "in":
            c.execute("UPDATE goods SET stock = stock + ? WHERE code=?", (qty, code))
            new_stock = stock + qty
        else:
            c.execute("UPDATE goods SET stock = stock - ? WHERE code=?", (qty, code))
            new_stock = stock - qty

        # 写入记录
        c.execute("""
        INSERT INTO record (code, name, type, qty)
        VALUES (?, ?, ?, ?)
        """, (code, name, mode, qty))

        conn.commit()
        conn.close()

        # 更新UI
        action = "入库" if mode == "in" else "出库"

        self.current_label.set(
            f"{action}成功 | {name} | 数量:{qty} | 剩余:{new_stock}"
        )

        self.load_data()
        self.load_records()

        self.entry.delete(0, tk.END)
        self.entry.focus_set()