"""
统一的界面主题：深色配色、控件样式与悬停反馈。

各界面模块（main / menu / help）共用此处的颜色与样式助手，
以保证主界面、对话框、菜单、帮助面板观感一致。
"""

from tkinter import FLAT

# ───────────────────────── 配色 ─────────────────────────
BG = "#23272E"        # 主背景
PANEL = "#2A303A"     # 面板 / 输入框底色
PANEL_HI = "#343C48"  # 悬停 / 激活底色
LINE = "#2E353F"      # 细分隔线
BORDER = "#3A424E"    # 边框

FG = "#D7DCE3"        # 主文字
FG_HOVER = "#FFFFFF"  # 悬停时文字（提亮）
MUTED = "#8A93A2"     # 次要文字（按钮常态）
DIM = "#5E6773"       # 更弱文字（已过 / 禁用）

ACCENT = "#4C8DFF"    # 强调蓝
SUCCESS = "#3DD68C"
WARN = "#FFC24B"
DANGER = "#FF6B6B"

# 时间胶囊（状态 >=3 需要提交时使用亮底深字）
CHIP_LIGHT_BG = "#E9ECF2"
CHIP_LIGHT_FG = "#1F242B"
CHIP_MID_BG = "#3C4759"
CHIP_MID_FG = "#EAF0FF"


def time_chip_style(status_int):
    """
    依据时间状态数值返回时间胶囊的 (背景色, 前景色)。

    与 homeworkfunc.collect_status / analyze_time 的优先级数值对应：
    >=3 需要提交（亮底）、2 较高、1 正常（淡面板底）、0 低、-1 已过（弱化）。
    """
    if status_int >= 3:
        return CHIP_LIGHT_BG, CHIP_LIGHT_FG
    if status_int == 2:
        return CHIP_MID_BG, CHIP_MID_FG
    if status_int == 1:
        return PANEL, "#CBD3DF"
    if status_int == 0:
        return PANEL, MUTED
    return BG, DIM


def style_button(btn, kind="normal", padx=12, pady=4, font=None, keep_geometry=False):
    """
    为按钮应用统一的扁平样式与鼠标悬停反馈。

    kind: normal（次要） / accent（主要） / danger（危险） / chip（胶囊）
    keep_geometry=True 时只设置颜色与悬停，不改动边框/内外边距等尺寸相关属性，
    以便保持控件原有的尺寸与占位区域。
    """
    base_bg, base_fg = BG, MUTED
    hover_bg, hover_fg = PANEL_HI, FG

    if kind == "accent":
        base_fg, hover_bg, hover_fg = ACCENT, ACCENT, "#FFFFFF"
    elif kind == "danger":
        base_fg, hover_bg, hover_fg = MUTED, DANGER, "#FFFFFF"
    elif kind == "chip":
        base_bg, base_fg = PANEL, FG
        hover_bg, hover_fg = PANEL_HI, "#FFFFFF"

    opts = dict(
        bg=base_bg,
        fg=base_fg,
        activebackground=hover_bg,
        activeforeground=hover_fg,
        cursor="hand2",
    )
    if not keep_geometry:
        opts.update(
            relief=FLAT,
            bd=0,
            highlightthickness=0,
            padx=padx,
            pady=pady,
        )
    if font is not None:
        opts["font"] = font
    try:
        btn.configure(**opts)
    except Exception:
        pass

    def _enter(_event=None):
        try:
            btn.configure(bg=hover_bg, fg=hover_fg)
        except Exception:
            pass

    def _leave(_event=None):
        try:
            btn.configure(bg=base_bg, fg=base_fg)
        except Exception:
            pass

    btn.bind("<Enter>", _enter, add="+")
    btn.bind("<Leave>", _leave, add="+")
    return btn


def hover_bg(widget, normal_bg, hover_bg_color):
    """仅改变背景色的悬停效果（用于文字颜色需要动态变化的控件）。"""
    widget.bind(
        "<Enter>", lambda _e: widget.configure(bg=hover_bg_color), add="+"
    )
    widget.bind("<Leave>", lambda _e: widget.configure(bg=normal_bg), add="+")
    return widget


def style_entry(entry, font=None):
    """为输入框应用统一的扁平样式与聚焦高亮。"""
    opts = dict(
        relief=FLAT,
        bd=0,
        bg=PANEL,
        fg=FG,
        insertbackground=ACCENT,
        selectbackground=ACCENT,
        selectforeground="#FFFFFF",
        highlightthickness=1,
        highlightbackground=BORDER,
        highlightcolor=ACCENT,
        disabledbackground=PANEL,
        disabledforeground=DIM,
    )
    if font is not None:
        opts["font"] = font
    try:
        entry.configure(**opts)
    except Exception:
        pass
    return entry


def style_option_menu(om, font=None):
    """为 OptionMenu 应用统一的扁平样式（含下拉列表）。"""
    opts = dict(
        relief=FLAT,
        bd=0,
        highlightthickness=0,
        bg=PANEL,
        fg=FG,
        activebackground=PANEL_HI,
        activeforeground=FG,
        cursor="hand2",
        padx=10,
        pady=3,
    )
    if font is not None:
        opts["font"] = font
    try:
        om.configure(**opts)
    except Exception:
        pass
    try:
        om["menu"].configure(
            bg=PANEL,
            fg=FG,
            activebackground=ACCENT,
            activeforeground="#FFFFFF",
            bd=0,
            font=font or ("HYWenHei-85W", 14),
        )
    except Exception:
        pass
    return om


def style_spinbox(spin, font=None):
    """为 Spinbox（数值输入框）应用统一的扁平样式（含箭头按钮底色）。"""
    opts = dict(
        relief=FLAT,
        bd=0,
        bg=PANEL,
        fg=FG,
        insertbackground=ACCENT,
        selectbackground=ACCENT,
        selectforeground="#FFFFFF",
        highlightthickness=1,
        highlightbackground=BORDER,
        highlightcolor=ACCENT,
        buttonbackground=PANEL,
        activebackground=PANEL_HI,
        disabledbackground=PANEL,
        disabledforeground=DIM,
        justify="center",
    )
    if font is not None:
        opts["font"] = font
    try:
        spin.configure(**opts)
    except Exception:
        pass
    return spin
