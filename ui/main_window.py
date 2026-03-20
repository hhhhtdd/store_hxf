import tkinter as tk
from tkinter import ttk
from tkinter.simpledialog import askinteger
from db import get_conn


class MainWindow:

    def __init__(self, root):
        self.root = root
        self.root.title("理工文具店管理系统")
        self.root.geometry("1200x900")

        self.style = ttk.Style()
        self.style.configure("TButton", padding=6, font=('Helvetica', 10))
        self.style.configure("Treeview.Heading", font=('Helvetica', 10, 'bold'))
        self.style.configure("TLabel", font=('Helvetica', 10))
        self.style.configure("TLabelframe.Label", font=('Helvetica', 10, 'bold'))

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
        top_bar.pack(fill=tk.X, padx=20, pady=(10, 5))

        ttk.Button(top_bar, text="后台管理", command=self.open_admin).pack(side=tk.RIGHT)

        # ===== 居中搜索框 =====
        search_container = ttk.Frame(self.root)
        search_container.pack(fill=tk.X, padx=100, pady=20)

        label_font = ('Helvetica', 12, 'bold')
        ttk.Label(search_container, text="商品搜索：", font=label_font).pack(side=tk.LEFT)

        self.entry = ttk.Entry(search_container, font=('Helvetica', 16))
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 0))
        self.entry.focus_set()

        # ===== 绑定快捷键 =====
        self.entry.bind("<Return>", lambda e: self.process_stock(ask_qty=False))
        self.entry.bind("<Shift-Return>", lambda e: self.process_stock(ask_qty=True))
        self.entry.bind("<KeyRelease>", self.filter_data)

        # ===== 商品表 =====
        columns = ("code", "name", "stock", "price")

        self.tree = ttk.Treeview(self.root, columns=columns, show="headings", height=15)

        self.tree.heading("code", text="编码")
        self.tree.heading("name", text="名称")
        self.tree.heading("stock", text="库存")
        self.tree.heading("price", text="售价")

        for col in columns:
            self.tree.column(col, anchor=tk.CENTER, width=120)

        self.tree.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)

        # ===== 当前商品 =====
        info_frame = ttk.LabelFrame(self.root, text="操作反馈")
        info_frame.pack(fill=tk.X, padx=20, pady=10)

        self.current_label = tk.StringVar()
        self.current_label.set("就绪")

        ttk.Label(info_frame, textvariable=self.current_label, font=('Helvetica', 12, 'bold'), foreground="#2c3e50").pack(anchor="w", padx=15, pady=10)

        # ===== 近期记录 =====
        record_frame = ttk.LabelFrame(self.root, text="最近 20 条交易记录")
        record_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(10, 20))

        columns = ("时间", "编码", "名称", "类型", "数量")

        self.record_table = ttk.Treeview(record_frame, columns=columns, show="headings", height=10)

        for col in columns:
            self.record_table.heading(col, text=col)
            self.record_table.column(col, anchor=tk.CENTER, width=100)

        self.record_table.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    # ================= 商品数据 =================
    def load_data(self):
        self.filter_data()

    def on_tree_select(self, event):
        selected = self.tree.focus()
        if not selected:
            return
        values = self.tree.item(selected, "values")
        if values:
            code = values[0]
            self.entry.delete(0, tk.END)
            self.entry.insert(0, code)

    def filter_data(self, event=None):
        keyword = self.entry.get().strip()

        for i in self.tree.get_children():
            self.tree.delete(i)

        if not keyword:
            return

        conn = get_conn()
        c = conn.cursor()

        c.execute("""
            SELECT code, name, stock, price_out
            FROM goods
            WHERE code LIKE ? OR name LIKE ? OR type LIKE ?
        """, (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"))

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
    def process_stock(self, ask_qty=False):

        code = self.entry.get().strip()
        if not code:
            return

        conn = get_conn()
        c = conn.cursor()

        # 查询商品
        c.execute("SELECT name, stock, price_out FROM goods WHERE code=?", (code,))
        row = c.fetchone()

        if not row:
            # 尝试通过模糊匹配到的第一个结果
            c.execute("SELECT code, name, stock, price_out FROM goods WHERE code LIKE ? OR name LIKE ? OR type LIKE ? LIMIT 1", (f"%{code}%", f"%{code}%", f"%{code}%"))
            row = c.fetchone()
            if not row:
                self.current_label.set(f"❌ 商品不存在: {code}")
                conn.close()
                return
            code, name, stock, price = row
        else:
            name, stock, price = row

        # 确定数量
        if ask_qty:
            qty = askinteger("数量", f"[{name}] 入库/出库 数量", minvalue=1)
            if not qty:
                conn.close()
                return
        else:
            qty = 1

        # 默认前台只有出库 (mode = out)
        mode = "out"

        # 库存检查
        if stock < qty:
            self.current_label.set("❌ 库存不足")
            conn.close()
            return

        # 更新库存
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
        action = "出库"

        self.current_label.set(
            f"{action}成功 | {name} | 数量:{qty} | 剩余:{new_stock}"
        )

        self.load_data()
        self.load_records()

        self.entry.delete(0, tk.END)
        self.entry.focus_set()