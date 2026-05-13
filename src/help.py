from tkinter import *

tk = Tk()
window_width = tk.winfo_screenwidth()
window_height = tk.winfo_screenheight()

CONFIG = {}

class Help:
    def __init__(self):
        tk.title("作业管理器·使用手册")
        tk.geometry(f"{int(window_width * 0.8)}x{int(window_height * 0.8)}+{int(window_width * 0.1)}+{int(window_height * 0.1)}")
        tk.resizable(False, False)

        tk.config(bg="#23272E")
        tk.option_add("*Background", "#23272E")
        tk.option_add("*Foreground", "#C8C8C8")
        tk.option_add("*Font", ("JetBrains Mono", 12))
        self.load_help()
    
    def load_help(self):
        self.content = Listbox(tk, highlightthickness=0, borderwidth=0)
        self.content.place(x=0, y=0, relheight=1, relwidth=0.15)
        self.content.insert(END, "1111")


if __name__ == "__main__":
    app = Help()
    tk.mainloop()