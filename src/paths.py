# -*- coding: utf-8 -*-
"""
运行期文件路径（集中定义）+ 旧版本文件位置自动迁移。

新位置（相对程序运行目录）：
    _internal/config/setting.json    配置文件
    _internal/backup/                备份文件
    _internal/lock/homework.lock     单实例锁文件
    （homework.json 作业数据仍位于程序运行目录根部）

旧版本位于程序目录根部（setting.json / backup/ / lock/），
启动时由 migrate_legacy() 自动检测并移动到新位置（先于任何读写执行）。
"""

import os
import shutil

# 运行时私有目录（-D 打包时与 PyInstaller 的 _internal 目录一致，数据随包存放）
INTERNAL_DIR = os.path.join(".", "_internal")

CONFIG_DIR = os.path.join(INTERNAL_DIR, "config")
CONFIG_FILE = os.path.join(CONFIG_DIR, "setting.json")

BACKUP_DIR = os.path.join(INTERNAL_DIR, "backup")

LOCK_DIR = os.path.join(INTERNAL_DIR, "lock")
LOCK_FILE = os.path.join(LOCK_DIR, "homework.lock")

# 旧版本位置（用于自动迁移；迁移完成后这些路径不再使用）
LEGACY_CONFIG_FILE = os.path.join(".", "setting.json")
LEGACY_BACKUP_DIR = os.path.join(".", "backup")
LEGACY_LOCK_DIR = os.path.join(".", "lock")
LEGACY_LOCK_FILE = os.path.join(LEGACY_LOCK_DIR, "homework.lock")


def ensure_dirs():
    """确保新位置所需目录存在（config / backup / lock）。"""
    for d in (CONFIG_DIR, BACKUP_DIR, LOCK_DIR):
        try:
            os.makedirs(d, exist_ok=True)
        except Exception:
            pass


def _move_file(src, dst):
    """
    把单个文件从旧位置移动到新位置。

    - 源文件不存在 → 不处理；
    - 目标已存在（避免覆盖）→ 改名为 "<name>.legacy" 保留，防止数据丢失；
    - 成功返回 True。
    """
    if not os.path.exists(src) or os.path.isdir(src):
        return False
    try:
        os.makedirs(os.path.dirname(dst) or ".", exist_ok=True)
        if os.path.exists(dst):
            dst = dst + ".legacy"
        if os.path.exists(dst):
            return False
        shutil.move(src, dst)
        return True
    except Exception:
        return False


def _merge_dir(src_dir, dst_dir):
    """
    把旧目录内容合并到新目录（同名文件改名为 *.legacy 保留），
    随后尽力删除已空的旧目录。返回是否有内容被移动。
    """
    moved = False
    try:
        os.makedirs(dst_dir, exist_ok=True)
        for name in sorted(os.listdir(src_dir)):
            src = os.path.join(src_dir, name)
            dst = os.path.join(dst_dir, name)
            if os.path.isdir(src):
                if _merge_dir(src, dst):
                    moved = True
                continue
            if os.path.exists(dst):
                dst = dst + ".legacy"
            if os.path.exists(dst):
                continue  # 连 *.legacy 都已存在 → 保留原文件不动
            try:
                shutil.move(src, dst)
                moved = True
            except Exception:
                pass
        try:
            os.rmdir(src_dir)  # 仅在目录已清空时成功
        except OSError:
            pass
    except Exception:
        pass
    return moved


def migrate_legacy():
    """
    老版本文件位置自动迁移（需在读取任何配置 / 备份 / 锁之前调用）：

        setting.json → _internal/config/setting.json
        backup/      → _internal/backup/
        lock/        → _internal/lock/

    仅当旧文件存在时处理；被占用而无法移动的文件会被跳过（例如旧实例仍持有锁），
    下次启动时会再次尝试，属幂等操作。
    """
    _move_file(LEGACY_CONFIG_FILE, CONFIG_FILE)
    if os.path.isdir(LEGACY_BACKUP_DIR):
        _merge_dir(LEGACY_BACKUP_DIR, BACKUP_DIR)
    if os.path.isdir(LEGACY_LOCK_DIR):
        _merge_dir(LEGACY_LOCK_DIR, LOCK_DIR)
