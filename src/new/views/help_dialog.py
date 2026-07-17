"""
帮助手册视图 - 树形导航的帮助文档浏览面板。
"""

import tkinter as tk
from tkinter import Frame, Label, Button, Listbox, SINGLE, LEFT, END
from typing import Any, Dict, List, Optional, Set, Tuple

import config


# ──────────────── 帮助内容数据 ────────────────

VERSION_STR = config.VERSION  # 将在运行时由 app.py 注入更新

HELP_DATA: List[Dict] = []  # 将在运行时填充


def build_help_data(version: str) -> List[Dict]:
    """构建帮助文档数据结构。"""
    v = version
    return [
        {
            "概述": f"作业管理器·使用手册 V{v}\n选择左侧选项以查看详细信息。"
        },
        {
            "添加与修改": [
                f"作业添加与修改\n\n作业添加/修改面板可通过如下方式打开：\n\n"
                f"添加：单击顶部按钮【添加】以进入。\n"
                f"修改：单击项目左侧【E】以进入。\n\n"
                f"作业添加/修改面板包括以下部分：\n\n"
                f"作业科目：单选按钮组，可以选择该作业的科目\n"
                f"内容：详见 内容与显示。\n"
                f"时间：详见 时间与自定义信息。\n"
                f"优先级：详见 优先级与显示。\n\n"
                f"在添加/修改面板中，输入完成后单击【保存】以保存作业信息并返回主界面，"
                f"单击【取消】以放弃修改并返回主界面。",
                {
                    "内容与显示": (
                        "作业内容与显示\n\n"
                        "作业内容输入框允许单行文本输入，内容将直接显示在主界面作业列表中，"
                        "短内容将以静态显示，若内容超过显示区域宽度，"
                        "将变为滚动显示，但同时带来更多负载，详见 负载。"
                    ),
                },
                {
                    "时间与自定义信息": (
                        "作业时间与自定义信息\n\n"
                        "时间与自定义信息共用输入框，一次仅能展示一项。\n"
                        "输入框允许输入作业截止时间，格式为 YYYY/MM/DD HH:MM，"
                        "输入完成后会自动转换为相对时间显示在主界面作业列表中，"
                        "输入0将自动解析为暂时不收，也可点击下方按钮快速设置。\n"
                        "同时，允许输入任意文本内容，内容将直接显示在主界面作业列表中，"
                        "适合用于输入一些额外的说明或备注信息。\n\n"
                        "当输入内容无法解析为有效时间时，将默认视为自定义信息进行显示。\n\n"
                        "显示样例如下（默认情况下，超时时间是5分钟）：\n"
                        "当前时间在设置时间的超时时间之后 -> 时间已过\n"
                        "当前时间在设置时间之后，在设置时间的超时时间之前 -> 现在收\n"
                        "当前时间在设置时间之前，但剩余时间小于超时时间 -> 即将收\n"
                        "当前时间在设置时间之前，且时间在今天 -> HH:MM收\n"
                        "当前时间在设置时间之前，且时间在明天 -> 明天HH:MM收\n"
                        "当前时间在设置时间之前，且时间在后天 -> 后天HH:MM收\n"
                        "当前时间在设置时间之前，且时间在本周内 -> 周XHH:MM收\n"
                        "当前时间在设置时间之前，且时间在下周内 -> 下周XHH:MM收\n"
                        "当前时间在设置时间之前，且时间在下周外 -> YYYY/MM/DD收"
                    ),
                },
                {
                    "优先级与显示": (
                        "作业优先级与时间显示样式\n\n"
                        "优先级及其对应的显示方式如下：\n"
                        "极低：作业置灰，时间/自定义内容置灰\n"
                        "低：作业正常显示，时间/自定义内容置灰\n"
                        "标准：作业正常显示，时间/自定义内容正常显示\n"
                        "高：作业正常显示，时间/自定义内容变为白底黑字显示\n\n"
                        "当作业存在提交时间时，若为\"现在收\"/\"时间已过\"，"
                        "则优先级设置无效化，变为默认显示模式（即优先级为\"自动\"）\n"
                        "若为自定义信息，则默认为标准\n\n"
                        "自动优先级的解析如下：\n"
                        "时间已过 -> 极低\n现在收 -> 高\n"
                        "即将收/HH:MM收/明天HH:MM收 -> 标准\n"
                        "后天HH:MM收/周XHH:MM收/下周XHH:MM收/YYYY/MM/DD收 -> 低"
                    ),
                },
                {
                    "作业显示顺序": (
                        "作业显示顺序\n\n"
                        "作业列表的排序规则由 sort_key 函数决定，按以下优先级排列：\n\n"
                        "1. 优先级数值降序排列——即优先级高的作业排在前面\n"
                        "2. 若优先级相同，则按截止时间升序排列——即截止时间近的排在前面\n"
                        "3. 若时间和优先级均相同，按文本字符串顺序排列\n\n"
                        "优先级数值对应关系：\n"
                        "- 时间已过 → -1（置底显示）\n- 不收 / 自定义文本 → 0 或按手动设定的优先级\n"
                        "- 低优先级 → 0\n- 标准优先级 → 1\n- 即将收 → 1\n"
                        "- 高优先级 → 3\n- 现在收 → 3 或 4（置顶显示）\n\n"
                        "注意：每次刷新列表时都会重新排序，但相同键的作业会保持原始相对顺序（稳定排序）。"
                    ),
                },
            ]
        },
        {
            "删除与清理": [
                "删除与清理\n\n程序提供两种删除作业的方式：\n\n"
                "侧边按钮删除：将鼠标移动到某作业上时，左侧会出现「×」与「E」两个按钮，"
                "单击「×」即可删除对应作业，删除前会弹出确认对话框。\n\n"
                "批量清理：单击顶部【清理】按钮，程序会自动扫描所有「时间已过」"
                "（即当前时间超过截止时间 5 分钟以上）的作业并将其批量移除。"
                "清理完成后会弹出提示框报告清理数量。\n\n"
                "注意：删除操作不可撤销，请谨慎操作。",
            ],
        },
        {
            "科目管理": [
                "科目管理\n\n单击顶部【菜单】按钮可打开科目管理面板，"
                "在此面板中可以对作业科目进行增删改查等管理操作。\n\n"
                "科目管理面板包含一个科目列表（显示科目名称与代码）和五个操作按钮，"
                "所有修改需要重启程序后才能生效。",
                {
                    "添加科目": (
                        "添加科目\n\n单击【添加】按钮，依次输入科目显示名称（如「物理 D3」）"
                        "和科目键名（如「PH3」，仅允许英文字母和数字，会自动转为大写）。\n\n"
                        "显示名称将出现在主界面的科目选择器和作业列表中，"
                        "键名用于 homework.json 中的数据存储。\n\n"
                        "名称和键名均不可与现有科目重复。"
                    ),
                },
                {
                    "重命名科目": (
                        "重命名科目\n\n在列表中选中一个科目后，单击【重命名】按钮，"
                        "可分别修改其显示名称和键名（键名可留空以保持不变）。\n\n"
                        "若键名发生变更，程序会自动将 homework.json 中对应的旧键数据迁移至新键，数据不会丢失。"
                    ),
                },
                {
                    "删除科目": (
                        "删除科目\n\n在列表中选中一个科目后，单击【删除】按钮即可删除该科目。\n\n"
                        "若该科目下存在作业，删除前会提示该科目下有多少作业将被同时删除，确认后才会执行。\n\n"
                        "注意：程序要求至少保留一个科目，因此无法删除最后一个科目。"
                    ),
                },
                {
                    "调整顺序": (
                        "调整顺序\n\n在列表中选中一个科目后，可通过【上移】和【下移】按钮"
                        "调整该科目在列表中的位置，此顺序决定了主界面作业列表中科目的显示顺序。"
                    ),
                },
                {
                    "配置文件": (
                        "配置文件\n\n科目定义存储在程序目录下的 setting.json 文件中，格式如下：\n\n"
                        "{\n    \"Subjects\": {\n        \"语文 \": \"C\",\n"
                        "        \"数学 \": \"M\",\n        \"英语 \": \"E\",\n        ...\n    }\n}\n\n"
                        "Subjects 字典的键为科目显示名称，值为科目代码。\n\n"
                        "初始配置由程序自动生成。若 homework.json 已存在有效数据，"
                        "首次启动时会从中提取科目键作为默认配置。\n\n"
                        "若科目管理面板中标记了「需要重启」，"
                        "关闭菜单时会询问是否立即重启以应用更改。"
                    ),
                },
            ]
        },
        {
            "界面布局与操作": [
                "界面布局与操作\n\n程序启动后以全屏方式运行，背景色为深色主题（#23272E）。\n\n"
                "主界面可分为以下几个区域：\n\n"
                "1. 顶部按钮栏：包含【退出】【刷新】【添加】【清理】【菜单】五个按钮，"
                "鼠标移入屏幕顶部时显示，停止移动 3 秒后自动隐藏。\n\n"
                "2. 作业列表区（左侧）：以 Canvas 渲染所有作业条目，"
                "每行显示「科目:作业内容」，内容过长时会自动横向滚动。\n\n"
                "3. 时间显示区（右侧）：在每行作业右侧显示对应的截止时间或自定义信息，"
                "不同时间状态有不同的背景色样式。\n\n"
                "4. 底部信息栏（左下角）：显示程序版本、当前时间、作业数量、负载、"
                "鼠标坐标、Tick 计数、更新状态等信息。\n\n"
                "5. 侧边操作按钮：鼠标悬停在某作业上时，"
                "左侧会出现「×」（删除）和「E」（编辑）按钮。",
                {
                    "顶部按钮栏": (
                        "顶部按钮栏\n\n鼠标移动到屏幕顶部时显示，包含以下按钮：\n\n"
                        "- 退出：关闭程序并调用 ClassIsland 的 Homeworkmode-off 通知\n"
                        "- 刷新：重新加载 homework.json 数据并刷新显示\n"
                        "- 添加：打开作业添加面板\n"
                        "- 清理：批量移除所有已过期的作业\n"
                        "- 菜单：打开科目管理面板\n\n"
                        "所有操作按钮在点击后会短暂禁用（约 0.5 秒），以防止重复点击导致的数据异常。"
                    ),
                },
                {
                    "底部信息栏": (
                        "底部信息栏\n\n位于屏幕左下角，从左到右依次显示：\n\n"
                        "1. 基本信息：显示 \"Homework Manager\" 及当前版本号。"
                        "若窗口不在前台，则高亮显示「Background」提示。\n\n"
                        "2. 当前时间：格式为 YYYY-MM-DD HH:MM:SS，每秒更新。\n\n"
                        "3. 作业数量：显示当前作业数/最大作业数限制。"
                        "超过限制时以黄色/红色闪烁警告。\n\n"
                        "4. 负载：界面的渲染负载估算值，详见 负载。\n\n"
                        "5. 鼠标坐标：当前鼠标在窗口内的位置 (X, Y)。"
                        "若 mouse 库不可用则显示 N/A。\n\n"
                        "6. Tick：当前的 Tick 计数值。\n\n"
                        "7. 更新状态：自动更新的状态信息，单击可触发更新操作（检查/下载/重启）。"
                    ),
                },
                {
                    "按钮冷却机制": (
                        "按钮冷却机制\n\n为防止用户重复点击导致数据异常，"
                        "程序为关键按钮实现了冷却（cooldown）机制：\n\n"
                        "- 按钮被点击后立即进入 DISABLED 状态\n"
                        "- 冷却时长为 0.5 秒（每 0.1 秒递减 1，共 5 个周期）\n"
                        "- 冷却结束后按钮恢复 NORMAL 状态，可再次点击\n\n"
                        "受保护的按钮包括：【添加】【刷新】【清理】。"
                    ),
                },
                {
                    "进程锁机制": (
                        "进程锁机制\n\n程序启动时通过文件锁（位于 lock/homework.lock）"
                        "防止同一程序被多次启动。\n\n"
                        "实现原理：使用 msvcrt.locking 对锁文件加排他锁。"
                        "若获取失败（如锁文件已被其他实例占用），"
                        "则弹出提示框告知用户「程序已在运行」，并退出当前实例。\n\n"
                        "程序正常退出时，锁文件会自动释放。"
                    ),
                },
            ]
        },
        {
            "存储与数据版本": [
                "存储与数据版本\n\n程序的数据和配置分别存储在 homework.json 和 setting.json "
                "两个文件中，均采用 UTF-8 编码的 JSON 格式。",
                {
                    "数据文件结构": (
                        "数据文件（homework.json）结构\n\n"
                        "{\n    \"VER\": 2,\n    \"C\": [\n"
                        "        {\n            \"content\": \"作业内容\",\n"
                        "            \"time\": 1762560000,\n"
                        "            \"emphasize\": \"自动\"\n        }\n    ],\n"
                        "    \"M\": [],\n    ...\n}\n\n"
                        "注意：time 字段可以是整数时间戳，也可以是任意文本字符串，"
                        "后者会直接作为自定义信息显示。"
                    ),
                },
                {
                    "配置文件结构": (
                        "配置文件（setting.json）结构\n\n"
                        "{\n    \"Subjects\": {\n        \"语文 \": \"C\",\n"
                        "        \"数学 \": \"M\",\n        ...\n    }\n}\n\n"
                        "Subjects 字典的键为科目显示名称，值为科目代码。"
                        "可通过菜单面板中的科目管理功能进行修改。"
                        "若文件不存在或缺少 Subjects 项，程序会在启动时自动生成。"
                    ),
                },
                {
                    "数据迁移": (
                        "数据迁移\n\n当 homework.json 中的 VER 字段小于当前程序所需的版本号时，"
                        "程序会在启动时自动执行数据格式升级：\n\n"
                        "- 版本 0→1：为所有作业添加 emphasize（优先级）字段，默认值为 \"Standard\"\n"
                        "- 版本 1→2：将旧优先级名称（Ignored/Unimportant/Standard/Urgent）"
                        "转换为新名称（很低/低/标准/高）\n\n"
                        "数据迁移为自动过程，无需用户手动干预。"
                    ),
                },
            ]
        },
        {
            "Tick 行为": [
                "Tick 行为\n\n程序内部维护一个递增的 Tick 计数器，每秒增加 1（通过 tk.after 定时器实现）。\n\n"
                "Tick 的主要作用：\n\n"
                "1. 自动隐藏 UI 按钮：当 Tick > 2（即鼠标停止移动超过 3 秒）时，"
                "顶部功能按钮栏和侧边编辑/删除按钮将自动隐藏，减少视觉干扰。\n\n"
                "2. 防止锁屏/进入休眠：当 Tick > 300（即 5 分钟无操作）时，"
                "程序会自动移动鼠标并点击（使用 mouse 库），"
                "模拟用户活动以防止系统进入锁屏或休眠状态。执行后 Tick 重置为 3，继续循环。\n\n"
                "3. 鼠标移动事件会将 Tick 重置为 0，使按钮重新显示。\n\n"
                "底部信息栏会实时显示当前 Tick 值。"
            ],
        },
        {
            "Classisland 对接": [
                "ClassIsland 对接\n\n本程序支持与 ClassIsland（一款课表/信息看板工具）进行集成，"
                "通过 URI 协议实现自动化交互。\n\n"
                "启用条件：程序通过 PyInstaller 打包为 exe 运行时自动启用 ClassIsland 对接功能；"
                "以 Python 脚本方式运行时默认禁用。\n\n"
                "调用的 URI 格式：classisland://app/api/automation/{mode}/{uri}\n\n"
                "触发场景：\n"
                "- 程序启动时：调用 Homeworkmode-on，通知 ClassIsland 作业模式已开启\n"
                "- 程序退出时：调用 Homeworkmode-off，通知 ClassIsland 作业模式已关闭\n"
                "- 时间显示更新时：若检测到有作业状态变为「现在收」且强调级别为 4，"
                "则调用 Homeworkmode-upload，通知 ClassIsland 有作业需要提交\n\n"
                "此功能通过调用系统 shell 启动 URI 实现，不会阻塞主程序运行。"
            ],
        },
        {
            "鼠标与防屏保": [
                "鼠标与防屏保\n\n程序集成 mouse 库用于模拟鼠标操作，"
                "以防止系统自动锁屏或进入休眠状态。\n\n"
                "工作机制：\n"
                "- 每 5 分钟（300 个 Tick）无操作时，"
                "自动将鼠标移动到坐标 (400, 1200) 并执行一次点击\n"
                "- 此操作对用户透明，完成后鼠标位置不会被还原\n"
                "- 若 mouse 库导入失败（如权限不足或环境限制），"
                "程序会降级处理，跳过防屏保功能，不会崩溃\n\n"
                "底部信息栏中「鼠标」一栏会显示当前鼠标坐标。"
                "若 mouse 库不可用，则显示「====N/A====」并以黄色高亮提示。\n\n"
                "注意：鼠标移动由系统全局坐标控制，可能影响其他正在进行的操作。"
            ],
        },
        {
            "负载": [
                "负载\n\n程序底部信息栏中「负载」一栏显示当前界面的渲染负载估算值，"
                "用于帮助判断程序性能状况。\n\n"
                "负载计算由以下因素加权组合得出：\n"
                "- 作业总数量（每个作业计 1 分）\n"
                "- 正在滚动显示的作业数量（每个滚动项计 6 分）\n"
                "- 每秒滚动像素量（每秒移动像素 ÷ 500）\n"
                "- 所有作业文本的总像素宽度（总像素 ÷ 2000）\n"
                "- 当前进程的 CPU 使用率（÷ 2）\n"
                "- 当前进程的内存占用 MB 数（÷ 10）\n\n"
                "负载等级：\n- ≤ 100：正常（灰色显示）\n"
                "- 100 ~ 200：偏高（黄色闪烁警告）\n- > 200：过高（红色闪烁警告）\n\n"
                "负载过高时建议减少作业数量或缩短作业内容长度以提升性能。"
            ],
        },
        {
            "自动更新": [
                "自动更新\n\n程序启动时会自动检查更新，无需手动操作。"
                "底部信息栏中的更新状态区域可单击以进行交互。",
                {
                    "更新流程": (
                        "更新流程\n\n1. 程序在后台线程中向更新服务器发送 HTTP 请求\n"
                        "2. 获取远程版本信息（VERSION_NUM），与本地版本号比较\n"
                        "3. 若远程版本更新或更新类型为「Force」（强制更新），则提示用户有新版本\n"
                        "4. 用户单击底部信息栏中的更新消息即可开始下载更新\n"
                        "5. 下载过程中实时显示进度百分比、下载速度和文件大小\n"
                        "6. 下载完成后，再次单击消息区域即可触发重启更新\n\n"
                        "底部信息栏状态说明：\n"
                        "- 无消息：未进行更新检查\n- 尝试连接至服务器……：正在连接更新服务器\n"
                        "- 无需更新：已是最新版本\n"
                        "- 发现更新：有新版本可用（显示版本号和更新类型）\n"
                        "- 下载更新中……：正在下载（显示进度）\n"
                        "- 重启以更新：下载完成，单击即可重启\n"
                        "- 离线或未能连接到服务器：更新检查失败"
                    ),
                },
                {
                    "重启机制": (
                        "重启机制\n\n程序支持多种场景下的自动重启：\n\n"
                        "1. 更新后重启：新版本下载完成后，程序会：\n"
                        "   - 在 update 目录下保存新的 main.exe\n"
                        "   - 生成 update.bat 批处理文件\n"
                        "   - 批处理等待 2 秒后，用新文件覆盖当前 exe，删除 update 目录，启动新版本\n"
                        "   - 当前进程立即退出\n\n"
                        "2. 科目修改后重启：在科目管理面板中修改科目后，"
                        "退出菜单时可选择立即重启以应用更改。\n\n"
                        "3. 手动重启：通过 restart_service() 可触发与更新后相同的重启流程，"
                        "重新执行当前 exe。\n\n"
                        "重启批处理脚本会自动清理自身（删除 update.bat），不留残留文件。"
                    ),
                },
            ],
        },
    ]


# ──────────────── HelpDialog ────────────────

class HelpDialog:
    """帮助手册面板，支持树形导航。"""

    def __init__(self, parent: tk.Tk, version: str,
                 screen_width: int, screen_height: int):
        self._tk = parent
        self._screen_w = screen_width
        self._screen_h = screen_height
        self._help_data = build_help_data(version)

        self._frame = Frame(parent, bg=config.COLOR_BG_MAIN, relief=tk.FLAT)
        self._frame.place(x=0, y=0, relheight=1, relwidth=1)

        self._build_ui()

    def _build_ui(self) -> None:
        # 顶部关闭栏
        top_bar = Frame(self._frame, bg=config.COLOR_BG_MAIN, relief=tk.FLAT)
        top_bar.place(x=0, y=0, relwidth=1)

        Button(
            top_bar,
            text="退出手册",
            fg=config.COLOR_FG_DIM,
            font=config.FONT_BUTTON,
            relief=tk.FLAT,
            command=self.exit,
        ).pack(side="right")

        # 左侧列表
        self._listbox = Listbox(
            self._frame,
            highlightthickness=0,
            borderwidth=0,
            relief=tk.FLAT,
            selectbackground=config.COLOR_BG_MAIN,
            selectforeground="#7AA4FF",
            selectmode=SINGLE,
            bg=config.COLOR_BG_DARK,
            fg=config.COLOR_FG_PRIMARY,
            font=config.FONT_HELP,
        )
        self._listbox.place(x=0, y=40, relheight=1, relwidth=0.18, height=-40)

        # 右侧详情
        detail_wraplength = int(self._screen_w * 0.81)
        self._detail = Label(
            self._frame,
            highlightthickness=0,
            borderwidth=0,
            relief=tk.FLAT,
            anchor="nw",
            justify=LEFT,
            wraplength=detail_wraplength,
            bg=config.COLOR_BG_MAIN,
            fg=config.COLOR_FG_PRIMARY,
            font=config.FONT_HELP,
        )
        self._detail.place(
            x=int(self._screen_w * 0.18), y=40,
            relheight=1, relwidth=0.82, height=-40,
        )

        # 解析帮助数据结构
        self._nodes: Dict[str, Dict] = {}
        self._roots: List[str] = []
        self._parse_data()

        # 状态
        self._expanded_paths: Set[Tuple[str, ...]] = set()
        self._display_paths: List[Tuple[str, ...]] = []
        self._suspend_events = False

        self._listbox.bind("<<ListboxSelect>>", self._on_select)
        self._listbox.bind("<Enter>", lambda e: self._listbox.config(
            fg=config.COLOR_FG_PRIMARY))
        self._listbox.bind("<Leave>", lambda e: self._listbox.config(fg="#4D4D4D"))

        self._rebuild_list()

        # 默认展开第一项
        if self._roots:
            self._expanded_paths.add((self._roots[0],))
            self._suspend_events = True
            self._rebuild_list()
            if self._display_paths:
                self._listbox.selection_set(0)
                self._listbox.activate(0)
                self._listbox.see(0)
                name = self._display_paths[0][-1]
                desc = self._nodes.get(name, {}).get("desc", "")
                self._detail.config(text=desc)
            self._suspend_events = False

    def _parse_data(self) -> None:
        """解析 HELP_DATA 为节点树。"""
        self._nodes = {}
        self._roots = []

        def process_item(name: str, val: Any, parent: Optional[str]) -> None:
            if isinstance(val, str):
                self._nodes[name] = {"desc": val, "children": [], "parent": parent}
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
                self._nodes[name] = {
                    "desc": base,
                    "children": children,
                    "parent": parent,
                }
            elif isinstance(val, dict):
                children = []
                for k, v in val.items():
                    process_item(k, v, parent=name)
                    children.append(k)
                self._nodes[name] = {"desc": "", "children": children, "parent": parent}
            else:
                self._nodes[name] = {"desc": "", "children": [], "parent": parent}

        for item in self._help_data:
            for k, v in item.items():
                self._roots.append(k)
                process_item(k, v, parent=None)

    def _rebuild_list(self) -> None:
        """根据展开状态重建列表显示。"""
        self._listbox.delete(0, END)
        self._display_paths = []

        def insert_node(name: str, path: List[str]) -> None:
            depth = len(path) - 1
            indent = "  " * depth
            self._listbox.insert(END, f"{indent}{name}")
            self._display_paths.append(tuple(path))
            if tuple(path) in self._expanded_paths:
                for child in self._nodes.get(name, {}).get("children", []):
                    insert_node(child, path + [child])

        for root in self._roots:
            insert_node(root, [root])

    def _on_select(self, event: tk.Event) -> None:
        """列表选中事件处理。"""
        if self._suspend_events:
            return

        sel = self._listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        if idx >= len(self._display_paths):
            return

        path = self._display_paths[idx]
        name = path[-1]

        desc = self._nodes.get(name, {}).get("desc", "")
        self._detail.config(text=desc)

        target_path = list(path)
        if self._nodes.get(name, {}).get("children"):
            t = tuple(path)
            if t in self._expanded_paths:
                # 折叠
                self._expanded_paths = {
                    p for p in self._expanded_paths
                    if not (len(p) >= len(t) and p[:len(t)] == t)
                }
            else:
                self._expanded_paths.add(t)

        self._suspend_events = True
        self._rebuild_list()

        try:
            new_idx = self._display_paths.index(tuple(target_path))
        except ValueError:
            new_idx = None
            for l in range(len(target_path) - 1, -1, -1):
                t = tuple(target_path[:l + 1])
                if t in self._display_paths:
                    new_idx = self._display_paths.index(t)
                    break
            if new_idx is None:
                new_idx = 0

        self._listbox.selection_clear(0, END)
        self._listbox.selection_set(new_idx)
        self._listbox.activate(new_idx)
        self._listbox.see(new_idx)
        self._suspend_events = False

    def exit(self) -> None:
        """隐藏帮助面板。"""
        self._frame.place_forget()
