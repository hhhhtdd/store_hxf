import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.simpledialog import askinteger
from db import get_conn


class MainWindow:

    def __init__(self, root):
        self.root = root
        self.root.title("理工文具店管理系统")
        self.root.geometry("1500x1000")
        self.cart = [] # 购物单
        self.root.configure(bg="#F5F5F7")  # Apple-style light gray background

        self.style = ttk.Style()
        self.style.theme_use('clam')

        # Apple-inspired color palette
        # Search area: #FFFFFF
        # Treeview: #FFFFFF, Selection: #0071E3 (Apple Blue)
        # Feedback: #F5F5F7

        self.style.configure("TFrame", background="#F5F5F7")
        self.style.configure("TLabelframe", background="#F5F5F7", bordercolor="#D2D2D7")
        self.style.configure("TLabelframe.Label", background="#F5F5F7", font=('Helvetica', 14, 'bold'), foreground="#1D1D1F")

        self.style.configure("IOS.TButton", padding=12, font=('Helvetica', 14, 'bold'), background="#FFFFFF", foreground="#0071E3", borderwidth=1, relief="flat")
        self.style.map("IOS.TButton",
            background=[('active', '#F5F5F7')],
            foreground=[('active', '#0071E3')]
        )

        self.style.configure("TLabel", font=('Helvetica', 14), background="#F5F5F7", foreground="#1D1D1F")

        self.style.configure("Treeview", font=('Helvetica', 13), rowheight=35, background="#FFFFFF", fieldbackground="#FFFFFF")
        self.style.configure("Treeview.Heading", font=('Helvetica', 14, 'bold'), background="#F5F5F7")
        self.style.map("Treeview", background=[('selected', '#0071E3')], foreground=[('selected', '#FFFFFF')])

        self.build_ui()
        self.load_data()
        self.update_cart_display()


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

        # ⭐ 传入权限，并保持引用 (不再需要刷新回调，因为主页不显示记录)
        from ui.admin_window import AdminWindow
        self.admin_win_instance = AdminWindow(win, role)
    # ================= UI =================
    def build_ui(self):

        # ===== 顶部工具栏 (薄荷绿背景/淡雅) =====
        top_bar = tk.Frame(self.root, bg="#E8F5E9", height=50)
        top_bar.pack(fill=tk.X)
        top_bar.pack_propagate(False)

        ttk.Button(top_bar, text="后台管理", command=self.open_admin, style="IOS.TButton").pack(side=tk.RIGHT, padx=20, pady=2)

        # 系统名称居中显示
        title_label = tk.Label(top_bar, text="理工文具店收银终端", font=('Helvetica', 18, 'bold'), bg="#E8F5E9", fg="#1D1D1F")
        title_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        # ===== 居中搜索框 (纯白区域) =====
        search_section = tk.Frame(self.root, bg="#FFFFFF", pady=10)
        search_section.pack(fill=tk.X)

        # 模拟圆角矩形搜索框 (加粗边框)
        search_outer = tk.Frame(search_section, bg="#D2D2D7", padx=2, pady=2) # Border
        search_outer.pack(expand=True)

        search_container = tk.Frame(search_outer, bg="#FFFFFF", padx=15, pady=2)
        search_container.pack()

        # 🔍 标志在最左边
        tk.Label(search_container, text="🔍", font=('Helvetica', 22), bg="#FFFFFF", fg="#86868B").pack(side=tk.LEFT)

        self.entry = tk.Entry(search_container, font=('Helvetica', 24), width=35, bd=0, highlightthickness=0, bg="#FFFFFF")
        self.entry.pack(side=tk.LEFT, ipady=10, padx=10)
        self.entry.focus_set()

        # 右侧提示文本 (不透明度 30% -> 灰色 #D2D2D7)
        tk.Label(search_container, text="名称 / 货号 / 类别", font=('Helvetica', 14), bg="#FFFFFF", fg="#D2D2D7").pack(side=tk.RIGHT, padx=10)

        # ===== 绑定快捷键 =====
        self.entry.bind("<Return>", lambda e: self.process_stock(ask_qty=False))
        self.entry.bind("<Shift-Return>", lambda e: self.process_stock(ask_qty=True))
        self.entry.bind("<KeyRelease>", self.filter_data)

        # ===== 商品表 (默认隐藏，仅在搜索时显示) =====
        columns = ("code", "name", "stock", "price")

        self.tree_frame = tk.Frame(self.root, bg="#F5F5F7")
        # self.tree_frame.pack(...) will be handled in filter_data

        self.tree = ttk.Treeview(self.tree_frame, columns=columns, show="headings", height=6)

        self.tree.heading("code", text="编码")
        self.tree.heading("name", text="名称")
        self.tree.heading("stock", text="库存")
        self.tree.heading("price", text="售价")

        for col in columns:
            self.tree.column(col, anchor=tk.CENTER, width=120)

        self.tree.pack(fill=tk.X, expand=False, padx=20, pady=5)
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)
        self.tree.bind("<Double-1>", self.on_tree_double_click)

        # ===== 购物单 (核心支付区) =====
        cart_section = tk.Frame(self.root, bg="#FFFFFF", pady=10)
        cart_section.pack(fill=tk.X)

        cart_container = tk.Frame(cart_section, bg="#FFFFFF")
        cart_container.pack(fill=tk.X, padx=20)

        # 购物车表格
        cart_cols = ("code", "name", "price", "qty", "subtotal")
        cart_headers = ("编码", "名称", "单价", "数量", "小计")
        self.cart_table = ttk.Treeview(cart_container, columns=cart_cols, show="headings", height=4)
        for col, head in zip(cart_cols, cart_headers):
            self.cart_table.heading(col, text=head)
            self.cart_table.column(col, anchor=tk.CENTER, width=120)
        self.cart_table.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 右侧结算面板
        checkout_panel = tk.Frame(cart_container, bg="#FFFFFF", padx=30)
        checkout_panel.pack(side=tk.RIGHT, fill=tk.Y)

        self.total_var = tk.StringVar(value="0.00")
        tk.Label(checkout_panel, text="应付总金额", font=('Helvetica', 16), bg="#FFFFFF", fg="#86868B").pack(pady=(10, 0))
        tk.Label(checkout_panel, textvariable=self.total_var, font=('Helvetica', 40, 'bold'), bg="#FFFFFF", fg="#1D1D1F").pack()
        tk.Label(checkout_panel, text="元", font=('Helvetica', 16), bg="#FFFFFF", fg="#1D1D1F").pack(pady=(0, 20))

        ttk.Button(checkout_panel, text="确认结账", command=self.finalize_checkout, style="IOS.TButton").pack(fill=tk.X, pady=5)
        ttk.Button(checkout_panel, text="清空购物单", command=self.clear_cart, style="IOS.TButton").pack(fill=tk.X, pady=5)

        # ===== 操作反馈 =====
        self.info_frame = ttk.LabelFrame(self.root, text="操作反馈")
        self.info_frame.pack(fill=tk.X, padx=20, pady=5)

        self.current_label = tk.StringVar()
        self.current_label.set("就绪")

        ttk.Label(self.info_frame, textvariable=self.current_label, font=('Helvetica', 12, 'bold'), foreground="#2c3e50").pack(anchor="w", padx=15, pady=5)

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

    def on_tree_double_click(self, event):
        selected = self.tree.focus()
        if not selected:
            return
        values = self.tree.item(selected, "values")
        if values:
            # values: (code, name, stock, price)
            self.add_to_cart_manual(values, ask_qty=False)
            self.entry.delete(0, tk.END)
            self.tree_frame.pack_forget()

    def filter_data(self, event=None):
        keyword = self.entry.get().strip()

        if not keyword:
            for i in self.tree.get_children():
                self.tree.delete(i)
            self.tree_frame.pack_forget()
            return

        conn = get_conn()
        c = conn.cursor()

        # 1. 尝试精确匹配商品编码 (扫码器模拟回车，但这里响应KeyRelease)
        c.execute("SELECT code, name, stock, price_out FROM goods WHERE code=?", (keyword,))
        exact_row = c.fetchone()

        if exact_row:
            # 如果精确匹配，直接加入购物单并清空输入框
            conn.close()
            self.add_to_cart_manual(exact_row, ask_qty=False)
            self.entry.delete(0, tk.END)
            self.tree_frame.pack_forget()
            return

        # 2. 如果没有精确匹配，则显示搜索结果
        for i in self.tree.get_children():
            self.tree.delete(i)

        self.tree_frame.pack(fill=tk.X, before=self.info_frame)

        c.execute("""
            SELECT code, name, stock, price_out
            FROM goods
            WHERE (code LIKE ? OR name LIKE ? OR type LIKE ?)
              AND (name IS NOT NULL AND name != 'None' AND name != '')
            LIMIT 20
        """, (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"))

        for row in c.fetchall():
            self.tree.insert("", tk.END, values=row)

        conn.close()

    def add_to_cart_manual(self, row):
        try:
            # row might be a tuple/list from DB or Treeview
            # Treeview strings might need conversion
            code = str(row[0])
            name = str(row[1])
            stock = int(row[2])
            price = float(row[3])
            qty = 1

            # 添加到购物单
            found = False
            for item in self.cart:
                if item['code'] == code:
                    item['qty'] += qty
                    item['subtotal'] = item['qty'] * item['price']
                    found = True
                    break

            if not found:
                self.cart.append({
                    'code': code,
                    'name': name,
                    'price': price,
                    'qty': qty,
                    'subtotal': price * qty,
                    'stock': stock
                })

            self.current_label.set(f"🛍️ 已添加: {name} x{qty}")
            self.update_cart_display()
        except Exception as e:
            messagebox.showerror("添加失败", f"数据格式错误: {e}")


    # ================= 核心业务 =================
    def process_stock(self, ask_qty=False):
        code = self.entry.get().strip()
        if not code:
            return

        conn = get_conn()
        c = conn.cursor()

        # 查询商品
        c.execute("SELECT code, name, stock, price_out FROM goods WHERE code=?", (code,))
        row = c.fetchone()

        if not row:
            # 尝试通过模糊匹配到的第一个结果
            c.execute("SELECT code, name, stock, price_out FROM goods WHERE (code LIKE ? OR name LIKE ? OR type LIKE ?) AND (name IS NOT NULL AND name != 'None' AND name != '') LIMIT 1", (f"%{code}%", f"%{code}%", f"%{code}%"))
            row = c.fetchone()
            if not row:
                messagebox.showerror("错误", f"商品不存在: {code}")
                self.current_label.set(f"❌ 商品不存在: {code}")
                conn.close()
                return

        conn.close()
        self.add_to_cart_manual(row, ask_qty=ask_qty)
        self.entry.delete(0, tk.END)
        self.entry.focus_set()

    def update_cart_display(self):
        for i in self.cart_table.get_children():
            self.cart_table.delete(i)

        total = 0.0
        for item in self.cart:
            total += item['subtotal']
            self.cart_table.insert("", tk.END, values=(item['code'], item['name'], f"{item['price']:.2f}", item['qty'], f"{item['subtotal']:.2f}"))

        self.total_var.set(f"{total:.2f}")

    def clear_cart(self):
        if not self.cart: return
        if messagebox.askyesno("确认", "确定清空当前购物单吗？"):
            self.cart = []
            self.update_cart_display()
            self.current_label.set("购物车已清空")

    def finalize_checkout(self):
        if not self.cart:
            messagebox.showwarning("提示", "购物单是空的")
            return

        total = self.total_var.get()
        if not messagebox.askyesno("结账确认", f"总计金额：{total} 元\n是否确认结账并打印记录？"):
            return

        conn = get_conn()
        c = conn.cursor()

        try:
            for item in self.cart:
                # 再次检查库存 (防止在购物期间库存变动)
                c.execute("SELECT stock FROM goods WHERE code=?", (item['code'],))
                current_stock = c.fetchone()[0]

                if current_stock < item['qty']:
                    raise Exception(f"商品 [{item['name']}] 库存不足，当前仅剩 {current_stock}")

                # 更新库存
                c.execute("UPDATE goods SET stock = stock - ? WHERE code=?", (item['qty'], item['code']))

                # 写入记录
                c.execute("""
                INSERT INTO record (code, name, type, qty)
                VALUES (?, ?, ?, ?)
                """, (item['code'], item['name'], 'out', item['qty']))

            conn.commit()
            messagebox.showinfo("成功", f"结账完成！实收 {total} 元")
            self.cart = []
            self.current_label.set(f"✅ 结账成功 | 实收: {total} 元")
            self.update_cart_display()
            self.load_data()
        except Exception as e:
            conn.rollback()
            messagebox.showerror("结账失败", str(e))
        finally:
            conn.close()