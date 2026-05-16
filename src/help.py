from tkinter import *

VERSION = "1.5.2"

HELP = [
    {
        "概述": f"作业管理器·使用手册 V{VERSION}\n选择左侧选项以查看详细信息。\n\n也可在作业添加/修改面板中再次打开本手册。",
    },
    {
        "添加与修改": [
            "作业添加与修改\n\n作业添加/修改面板可通过如下方式打开：\n\n添加：单击顶部按钮【添加】以进入。\n修改：单击项目左侧【E】以进入。\n\n作业添加/修改面板包括以下部分：\n\n作业科目：可选择的科目列表，包含语文、数学、英语、政治、历史、地理、物理D1、物理D2、化学D1、化学D2、生物D1、其他。\n内容：详见 内容与显示。\n时间：详见 时间与自定义信息。\n优先级：详见 优先级与显示。\n\n在添加/修改面板中，输入完成后单击【保存】以保存作业信息并返回主界面，单击【取消】以放弃修改并返回主界面。",
            {
                "内容与显示": "作业内容与显示\n\n作业内容输入框允许单行文本输入，内容将直接显示在主界面作业列表中，短内容将以静态显示，若内容超过显示区域宽度，将变为滚动显示，但同时带来更多负载，详见 负载。",
            },
            {
                "时间与自定义信息": "作业时间与自定义信息\n\n时间与自定义信息共用输入框，一次仅能展示一项。\n输入框允许输入作业截止时间，格式为 YYYY-MM-DD HH:MM，输入完成后会自动转换为相对时间显示在主界面作业列表中，输入0将自动解析为暂时不收。\n同时，允许输入任意文本内容，内容将直接显示在主界面作业列表中，适合用于输入一些额外的说明或备注信息。\n\n当输入内容无法解析为有效时间时，将默认视为自定义信息进行显示。\n\n显示样例如下（默认情况下，超时时间是5分钟）：\n当前时间在设置时间的超时时间之后 -> 时间已过\n当前时间在设置时间之后，在设置时间的超时时间之前 -> 现在收\n当前时间在设置时间之前，但剩余时间小于超时时间 -> 即将收\n当前时间在设置时间之前，且时间在今天 -> HH:MM收\n当前时间在设置时间之前，且时间在明天 -> 明天HH:MM收\n当前时间在设置时间之前，且时间在后天 -> 后天HH:MM收\n当前时间在设置时间之前，且时间在本周内 -> 周XHH:MM收\n当前时间在设置时间之前，且时间在下周内 -> 下周XHH:MM收\n当前时间在设置时间之前，且时间在下周外 -> YYYY/MM/DD收\n",
            },
            {
                "优先级与显示": "作业优先级与时间显示样式\n\n优先级及其对应的显示方式如下：\n极低：作业置灰，时间/自定义内容置灰\n低：作业正常显示，时间/自定义内容置灰\n标准：作业正常显示，时间/自定义内容正常显示\n高：作业正常显示，时间/自定义内容变为白底黑字显示\n\n当作业存在提交时间时，若为“现在收”/“时间已过”，则优先级设置无效化，变为默认显示模式（即优先级为“自动”）\n若为自定义信息，则默认为标准\n\n自动优先级的解析如下：\n时间已过 -> 极低\n现在收 -> 高\n即将收/HH:MM收/明天HH:MM收 -> 标准\n后天HH:MM收/周XHH:MM收/下周XHH:MM收/YYYY/MM/DD收 -> 低\n",
            },
            {
                "作业显示顺序": "……",
            }
        ]
    },
    {
        "删除与清空": "……",
    },
    {
        "存储与数据版本": "……",
    },
    {
        "Tick 行为": "……",
    },
    {
        "Classisland 对接": "……",
    },
    {
        "鼠标与防屏保": "……",
    },
    {
        "负载": "……",
    },
]


class Help:
    def __init__(self):
        global tk, window_width, window_height
        tk = Tk()
        window_width = tk.winfo_screenwidth()
        window_height = tk.winfo_screenheight()
        tk.title("作业管理器·使用手册")
        tk.geometry(
            f"{int(window_width * 0.8)}x{int(window_height * 0.8)}+{int(window_width * 0.1)}+{int(window_height * 0.1)}"
        )
        tk.resizable(False, False)
        tk.attributes("-topmost", True)

        tk.config(bg="#23272E")
        tk.option_add("*Background", "#23272E")
        tk.option_add("*Foreground", "#C8C8C8")
        tk.option_add("*Font", ("HYWenHei-85W", 12))
        self.load_help()

    def load_help(self):
        self.content = Listbox(
            tk,
            highlightthickness=0,
            borderwidth=1,
            relief=RIDGE,
            selectbackground="#23272E",
            selectforeground="#7AA4FF",
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
            wraplength=window_width * 0.8 * 0.81,
        )
        self.detail.place(
            x=int(window_width * 0.8 * 0.18), y=0, relheight=1, relwidth=0.82
        )

        # build a tree representation from CONFIG
        self._parse_config()
        # track which paths are expanded (set of path tuples)
        self.expanded_paths = set()
        # parallel list storing the full path (tuple) for each visible row
        self.display_paths = []
        # prevent handling programmatic selection events
        self._suspend_events = False

        self.content.bind("<<ListboxSelect>>", self.show_detail)
        self.content.bind("<Enter>", lambda e: self.content.config(fg="#C8C8C8"))
        self.content.bind("<Leave>", lambda e: self.content.config(fg="#4D4D4D"))

        # initial render: only top-level entries
        self.rebuild_list()

        # 默认选中并显示 CONFIG 第一项（如果存在）
        if self.roots:
            self.expanded_paths.add((self.roots[0],))
            self._suspend_events = True
            self.rebuild_list()
            if self.display_paths:
                self.content.selection_set(0)
                self.content.activate(0)
                self.content.see(0)
                name = self.display_paths[0][-1]
                desc = self.nodes.get(name, {}).get("desc", "")
                self.detail.config(text=desc)
            self._suspend_events = False

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

        for item in HELP:
            for k, v in item.items():
                self.roots.append(k)
                process_item(k, v, parent=None)

    def rebuild_list(self):
        self.content.delete(0, END)
        self.display_paths = []

        def insert_node(name, path):
            depth = len(path) - 1
            indent = "  " * depth
            self.content.insert(END, f"{indent}{name}")
            self.display_paths.append(tuple(path))
            # if this node's path tuple is in expanded_paths, render its children
            if tuple(path) in self.expanded_paths:
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
        # Toggle expansion for nodes with children; keep other expanded paths intact
        target_path = list(path)
        if self.nodes.get(name, {}).get("children"):
            t = tuple(path)
            if t in self.expanded_paths:
                # collapse: remove this path and any descendant expansions
                self.expanded_paths = {p for p in self.expanded_paths if not (len(p) >= len(t) and p[: len(t)] == t)}
            else:
                # expand: add this path
                self.expanded_paths.add(t)

        self._suspend_events = True
        self.rebuild_list()

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
