from tkinter import *

tk = Tk()
window_width = tk.winfo_screenwidth()
window_height = tk.winfo_screenheight()

CONFIG = [
    {"概述": "作业管理器·使用手册\n选择左侧选项以查看详细信息"},
    {
        "添加与修改": [
            "添加：单击顶部【添加】以进入\n修改：单击项目左侧【E】以进入",
            {"内容与长度": "……"},
        ]
    },
    {"删除与清空": "……"},
    {"存储与数据版本": "……"},
    {"Tick 行为": "……"},
    {"Classisland 对接": "……"},
    {"鼠标与防屏保": "……"},
    {"负载": "……"},
]


class Help:
    def __init__(self):
        tk.title("作业管理器·使用手册")
        tk.geometry(
            f"{int(window_width * 0.8)}x{int(window_height * 0.8)}+{int(window_width * 0.1)}+{int(window_height * 0.1)}"
        )
        tk.resizable(False, False)

        tk.config(bg="#23272E")
        tk.option_add("*Background", "#23272E")
        tk.option_add("*Foreground", "#C8C8C8")
        tk.option_add("*Font", ("JetBrains Mono", 12))
        self.load_help()

    def load_help(self):
        self.content = Listbox(
            tk,
            highlightthickness=0,
            borderwidth=1,
            relief=RIDGE,
            selectbackground="#7289DA",
            selectmode=SINGLE,
        )
        self.content.place(x=0, y=0, relheight=1, relwidth=0.18)
        self.detail = Label(
            tk,
            highlightthickness=0,
            borderwidth=1,
            relief=RIDGE,
            anchor="nw",
            justify=LEFT,
            wraplength=window_width * 0.8 * 0.82,
        )
        self.detail.place(
            x=int(window_width * 0.8 * 0.18), y=0, relheight=1, relwidth=0.82
        )

        # build a tree representation from CONFIG
        self._parse_config()
        # track which path is expanded (list of names from root)
        self.expanded_path = []
        # parallel list storing the full path (tuple) for each visible row
        self.display_paths = []
        # prevent handling programmatic selection events
        self._suspend_events = False

        self.content.bind("<<ListboxSelect>>", self.show_detail)

        # initial render: only top-level entries
        self.rebuild_list(self.expanded_path)

    def _parse_config(self):
        self.nodes = {}
        self.roots = []

        def process_item(name, val, parent):
            if isinstance(val, str):
                self.nodes[name] = {"desc": val, "children": [], "parent": parent}
            elif isinstance(val, list):
                base = ""
                items = val
                if items and isinstance(items[0], str):
                    base = items[0]
                    iterator = items[1:]
                else:
                    iterator = items
                children = []
                for elem in iterator:
                    if isinstance(elem, dict):
                        for k, v in elem.items():
                            process_item(k, v, parent=name)
                            children.append(k)
                self.nodes[name] = {
                    "desc": base,
                    "children": children,
                    "parent": parent,
                }
            elif isinstance(val, dict):
                children = []
                for k, v in val.items():
                    process_item(k, v, parent=name)
                    children.append(k)
                self.nodes[name] = {"desc": "", "children": children, "parent": parent}
            else:
                self.nodes[name] = {"desc": "", "children": [], "parent": parent}

        for item in CONFIG:
            for k, v in item.items():
                self.roots.append(k)
                process_item(k, v, parent=None)

    def rebuild_list(self, expanded_path):
        self.content.delete(0, END)
        self.display_paths = []

        def insert_node(name, path):
            depth = len(path) - 1
            indent = "  " * depth
            self.content.insert(END, f"{indent}{name}")
            self.display_paths.append(tuple(path))
            # if this node is marked as expanded in the expanded_path, render its children
            if len(expanded_path) > depth and expanded_path[depth] == name:
                for child in self.nodes.get(name, {}).get("children", []):
                    insert_node(child, path + [child])

        for root in self.roots:
            insert_node(root, [root])

    def show_detail(self, event):
        if getattr(self, "_suspend_events", False):
            return

        sel = self.content.curselection()
        if not sel:
            return
        idx = sel[0]
        path = self.display_paths[idx]
        name = path[-1]

        # show description for the selected node
        desc = self.nodes.get(name, {}).get("desc", "")
        self.detail.config(text=desc)

        # decide new expanded path: if selected node has children, expand it;
        # otherwise keep its ancestors expanded
        if self.nodes.get(name, {}).get("children"):
            new_expanded = list(path)
        else:
            new_expanded = list(path[:-1])

        # update and rebuild view
        self.expanded_path = new_expanded
        target_path = list(path)
        self._suspend_events = True
        self.rebuild_list(self.expanded_path)

        # try to restore selection to the originally selected path (or its nearest ancestor)
        try:
            new_idx = self.display_paths.index(tuple(target_path))
        except ValueError:
            new_idx = None
            for l in range(len(target_path) - 1, -1, -1):
                t = tuple(target_path[: l + 1])
                if t in self.display_paths:
                    new_idx = self.display_paths.index(t)
                    break
            if new_idx is None:
                new_idx = 0

        self.content.selection_clear(0, END)
        self.content.selection_set(new_idx)
        self.content.activate(new_idx)
        self.content.see(new_idx)
        self._suspend_events = False


if __name__ == "__main__":
    app = Help()
    tk.mainloop()
