import tkinter as tk
from db import init_db
from ui.main_window import MainWindow

if __name__ == "__main__":
    init_db()

    root = tk.Tk()
    app = MainWindow(root)
    root.mainloop()