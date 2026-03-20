import tkinter as tk
from tkinter import ttk, messagebox
from db import get_conn

class AdminWindow:

    def __init__(self, root, role='admin'):
        self.root = root
        self.root.title("后台库存管理")
        self.root.geometry("1100x700")
        self.role = role

        self.style = ttk.Style()
        self.style.configure("TButton", padding=6)
        self.style.configure("Treeview.Heading", font=('Helvetica', 10, 'bold'))

        self.build_ui()
        self.load_data()

    # ================= UI =================
    def build_ui(self):

        # ===== 统计信息 =====
        stat_frame = ttk.LabelFrame(self.root, text="核心运营数据")
        stat_frame.pack(fill=tk.X, padx=20, pady=10)

        self.stat_var = tk.StringVar()
        self.stat_var.set("加载中...")

        ttk.Label(stat_frame, textvariable=self.stat_var, font=('Helvetica', 11, 'bold'), foreground="#d35400").pack(anchor="w", padx=15, pady=10)

        # ===== 顶部搜索 =====
        top = ttk.Frame(self.root)
        top.pack(fill=tk.X, padx=20, pady=5)

        ttk.Label(top, text="搜索 (编码/名称/类别)：").pack(side=tk.LEFT)

        self.search_entry = ttk.Entry(top, width=40)
        self.search_entry.pack(side=tk.LEFT, padx=10)
        self.search_entry.bind("<KeyRelease>", self.search)

        ttk.Button(top, text="查询", command=self.search).pack(side=tk.LEFT, padx=2)
        ttk.Button(top, text="显示全部", command=self.load_data).pack(side=tk.LEFT, padx=2)

        # ===== 表格 =====
        columns = ("code","name","type","stock","warn","price_in","price_out")

        self.tree = ttk.Treeview(self.root, columns=columns, show="headings")

        headers = ["编码","名称","类别","库存","预警线","进价","售价"]
        for col, text in zip(columns, headers):
            self.tree.heading(col, text=text)
            self.tree.column(col, width=120, anchor=tk.CENTER)

        self.tree.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        if self.role == 'admin':
            self.tree.bind("<Double-1>", self.on_double_click)

        # ===== 底部按钮 =====
        bottom = ttk.Frame(self.root)
        bottom.pack(fill=tk.X, padx=20, pady=15)


        if self.role == 'admin':
            ttk.Button(bottom, text="新增商品", command=self.add_goods).pack(side=tk.LEFT, padx=5)
            ttk.Button(bottom, text="删除商品", command=self.delete_goods).pack(side=tk.LEFT, padx=5)
        ttk.Button(bottom, text="刷新数据", command=self.load_data).pack(side=tk.LEFT, padx=5)

    # ================= 数据 =================
    def load_data(self):
        self.load_stats()
        for i in self.tree.get_children():
            self.tree.delete(i)

        conn = get_conn()
        c = conn.cursor()
        c.execute("SELECT * FROM goods")

        for row in c.fetchall():
            self.tree.insert("", tk.END, values=row)

        conn.close()

    def search(self, event=None):
        keyword = self.search_entry.get().strip()

        conn = get_conn()
        c = conn.cursor()

        c.execute("""
        SELECT * FROM goods
        WHERE code LIKE ? OR name LIKE ? OR type LIKE ?
        """, (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"))

        rows = c.fetchall()
        conn.close()

        for i in self.tree.get_children():
            self.tree.delete(i)

        for row in rows:
            self.tree.insert("", tk.END, values=row)

    # ================= 操作 =================
    def add_goods(self):
        win = tk.Toplevel(self.root)
        win.title("新增商品")
        win.geometry("300x400")

        fields = ["编码","名称","类别","库存","预警","进价","售价"]
        entries = {}

        for i, f in enumerate(fields):
            ttk.Label(win, text=f).grid(row=i, column=0, padx=20, pady=10, sticky="e")
            e = ttk.Entry(win)
            e.grid(row=i, column=1, padx=20, pady=10)
            entries[f] = e

        def save():
            try:
                data = (
                    entries["编码"].get(),
                    entries["名称"].get(),
                    entries["类别"].get(),
                    int(entries["库存"].get() or 0),
                    int(entries["预警"].get() or 0),
                    float(entries["进价"].get() or 0),
                    float(entries["售价"].get() or 0)
                )

                conn = get_conn()
                c = conn.cursor()
                c.execute("INSERT INTO goods VALUES (?,?,?,?,?,?,?)", data)
                conn.commit()
                conn.close()

                win.destroy()
                self.load_data()

            except Exception as e:
                messagebox.showerror("错误", str(e))

        ttk.Button(win, text="保存", command=save).grid(row=8, columnspan=2, pady=20)

    def delete_goods(self):

        selected = self.tree.focus()   # ⭐ 用 focus 替代 selection

        if not selected:
            messagebox.showwarning("提示", "请先选中一行")
            return

        values = self.tree.item(selected, "values")

        if not values:
            messagebox.showerror("错误", "无法获取数据")
            return

        code = values[0]

        if not messagebox.askyesno("确认", f"确定删除商品 [{code}]？"):
            return

        conn = get_conn()
        c = conn.cursor()
        c.execute("DELETE FROM goods WHERE code=?", (code,))
        conn.commit()
        conn.close()

        self.load_data()

    def on_double_click(self, event):
        item = self.tree.selection()
        if not item:
            return

        values = self.tree.item(item[0], "values")

        win = tk.Toplevel(self.root)
        win.title("编辑商品")
        win.geometry("300x400")

        fields = ["编码","名称","类别","库存","预警","进价","售价"]
        entries = {}

        for i, (f, val) in enumerate(zip(fields, values)):
            ttk.Label(win, text=f).grid(row=i, column=0, padx=20, pady=10, sticky="e")
            e = ttk.Entry(win)
            e.insert(0, val)
            e.grid(row=i, column=1, padx=20, pady=10)
            entries[f] = e

        def save():
            conn = get_conn()
            c = conn.cursor()

            c.execute("""
            UPDATE goods SET
            name=?, type=?, stock=?, warn_line=?, price_in=?, price_out=?
            WHERE code=?
            """, (
                entries["名称"].get(),
                entries["类别"].get(),
                int(entries["库存"].get()),
                int(entries["预警"].get()),
                float(entries["进价"].get()),
                float(entries["售价"].get()),
                entries["编码"].get()
            ))

            conn.commit()
            conn.close()

            win.destroy()
            self.load_data()

        ttk.Button(win, text="保存修改", command=save).grid(row=8, columnspan=2, pady=20)


    def load_stats(self):

        if self.role != "admin":
            self.stat_var.set("无权限查看")
            return

        conn = get_conn()
        c = conn.cursor()

        # 今日
        c.execute("""
        SELECT SUM(r.qty * (g.price_out - g.price_in)), SUM(qty * g.price_out)
        FROM record r
        JOIN goods g ON r.code = g.code
        WHERE r.type='out' AND date(time)=date('now')
        """)
        today = c.fetchone()

        # 近7天
        c.execute("""
        SELECT SUM(r.qty * (g.price_out - g.price_in)), SUM(qty * g.price_out)
        FROM record r
        JOIN goods g ON r.code = g.code
        WHERE r.type='out' AND date(time)>=date('now','-7 day')
        """)
        week = c.fetchone()

        conn.close()

        today_qty, today_sales = today if today else (0, 0)
        week_qty, week_sales = week if week else (0, 0)

        self.stat_var.set(
            f"今日利润:{today_qty or 0} | 今日销售额:{today_sales or 0}\n"
            f"7天利润:{week_qty or 0} | 7天销售额:{week_sales or 0}"
        )