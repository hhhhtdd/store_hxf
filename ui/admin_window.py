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
        ttk.Button(bottom, text="交易明细", command=self.show_records).pack(side=tk.LEFT, padx=5)
        ttk.Button(bottom, text="统计图表", command=self.show_charts).pack(side=tk.LEFT, padx=5)

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


    def show_records(self):
        win = tk.Toplevel(self.root)
        win.title("交易明细")
        win.geometry("800x500")

        columns = ("id", "code", "name", "type", "qty", "time")
        tree = ttk.Treeview(win, columns=columns, show="headings")
        headers = ["ID", "编码", "名称", "类型", "数量", "时间"]
        for col, text in zip(columns, headers):
            tree.heading(col, text=text)
            tree.column(col, width=100, anchor=tk.CENTER)
        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        def load_record_data():
            for i in tree.get_children():
                tree.delete(i)
            conn = get_conn()
            c = conn.cursor()
            c.execute("SELECT id, code, name, type, qty, time FROM record ORDER BY id DESC LIMIT 200")
            for row in c.fetchall():
                tree.insert("", tk.END, values=row)
            conn.close()

        def on_right_click(event):
            item = tree.identify_row(event.y)
            if item:
                tree.selection_set(item)
                menu = tk.Menu(win, tearoff=0)
                menu.add_command(label="撤回记录", command=lambda: withdraw_record(tree.item(item, "values")))
                menu.post(event.x_root, event.y_root)

        def withdraw_record(values):
            if not values: return
            rec_id, code, name, mode, qty, _ = values
            if not messagebox.askyesno("确认", f"确定撤回记录 [ID:{rec_id}]？\n这将回退库存和统计数据。"):
                return

            conn = get_conn()
            c = conn.cursor()
            try:
                # 回退库存
                if mode == 'out':
                    c.execute("UPDATE goods SET stock = stock + ? WHERE code=?", (qty, code))
                else:
                    c.execute("UPDATE goods SET stock = stock - ? WHERE code=?", (qty, code))

                # 删除记录
                c.execute("DELETE FROM record WHERE id=?", (rec_id,))
                conn.commit()
                messagebox.showinfo("成功", "记录已撤回")
                load_record_data()
                self.load_data() # 刷新主表和统计
            except Exception as e:
                conn.rollback()
                messagebox.showerror("错误", str(e))
            finally:
                conn.close()

        tree.bind("<Button-3>", on_right_click)
        load_record_data()

    def show_charts(self):
        import matplotlib.pyplot as plt
        from matplotlib import rcParams

        # 设置中文字体 (尝试几种常见的)
        rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial']
        rcParams['axes.unicode_minus'] = False

        conn = get_conn()
        c = conn.cursor()

        # 最近15天销量前十
        c.execute("""
            SELECT name, SUM(qty) as total_qty
            FROM record
            WHERE type='out' AND date(time) >= date('now', '-15 day')
            GROUP BY code
            ORDER BY total_qty DESC
            LIMIT 10
        """)
        qty_data = c.fetchall()

        # 最近15天销售额前十
        c.execute("""
            SELECT r.name, SUM(r.qty * g.price_out) as total_sales
            FROM record r
            JOIN goods g ON r.code = g.code
            WHERE r.type='out' AND date(r.time) >= date('now', '-15 day')
            GROUP BY r.code
            ORDER BY total_sales DESC
            LIMIT 10
        """)
        sales_data = c.fetchall()
        conn.close()

        if not qty_data and not sales_data:
            messagebox.showinfo("提示", "最近15天没有销售记录")
            return

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))

        if qty_data:
            labels = [f"{d[0]}" for d in qty_data]
            sizes = [d[1] for d in qty_data]
            ax1.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140)
            ax1.set_title("最近15天销量前十")
        else:
            ax1.text(0.5, 0.5, '暂无销量数据', ha='center', va='center')

        if sales_data:
            labels = [f"{d[0]}" for d in sales_data]
            sizes = [d[1] for d in sales_data]
            ax2.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140)
            ax2.set_title("最近15天销售额前十")
        else:
            ax2.text(0.5, 0.5, '暂无销售额数据', ha='center', va='center')

        plt.tight_layout()
        plt.show()

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
            f"今日利润:{today_qty or 0}元   |   今日销售额:{today_sales or 0}元\n"
            f"7天利润:{week_qty or 0}元   |   7天销售额:{week_sales or 0}元"
        )