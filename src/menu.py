from tkinter import *
from tkinter import messagebox
import json

import main
from lang import *


class Menu:
    def __init__(self):
        self.load_menu()

    def load_menu(self):
        self.menu_frame = Frame(tk, relief=FLAT)
        self.menu_frame.place(x=0, y=0, relheight=1, relwidth=1)

        self.menu_top_frame = Frame(self.menu_frame, relief=FLAT)
        self.menu_top_frame.place(x=0, y=0, relwidth=1)

        self.close_menu = Button(
            self.menu_top_frame,
            text=text("menu.exit"),
            fg=COLOR,
            font=("汉仪文黑-85W", 14),
            relief=FLAT,
            command=self.exit,
        )

        self.close_menu.pack(side="right")

        self.language_frame = Frame(self.menu_frame, relief=FLAT)
        self.language_frame.place(x=20, y=40)

        self.lang_cn = Button(
            self.language_frame,
            text="中文",
            fg=COLOR,
            font=("汉仪文黑-85W", 14),
            relief=FLAT,
            command=lambda: self.change("Language", "zh-CN", True),
        )
        self.lang_en = Button(
            self.language_frame,
            text="ENGLISH",
            fg=COLOR,
            font=("汉仪文黑-85W", 14),
            relief=FLAT,
            command=lambda: self.change("Language", "en-US", True),
        )
        self.lang_cn.pack(side="left")
        self.lang_en.pack(side="left")

    def change(self, key, value, restart=False):
        with open("setting.json", "r") as f:
            data = json.load(f)
        data[key] = value
        with open("setting.json", "w") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        if restart:
            messagebox.showinfo(
                "重启 | RESTART",
                "重启以应用更改\nRestart to Apply",
            )
            main.restart_service()

    def exit(self):
        self.menu_frame.place_forget()


def open_menu():
    global tk, COLOR
    tk = main.tk
    COLOR = main.COLOR
    menu = Menu()


if __name__ == "__main__":
    pass
