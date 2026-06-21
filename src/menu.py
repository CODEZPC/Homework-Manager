from tkinter import *
from tkinter import messagebox

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
    
    def exit(self):
        self.menu_frame.place_forget()

def open_menu():
    global tk, COLOR
    tk = main.tk
    COLOR = main.COLOR
    menu = Menu()

if __name__ == "__main__":
    pass