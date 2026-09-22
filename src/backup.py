import hashlib
import os
import shutil
import time

import paths

# 备份目录：_internal/backup（旧版根目录 backup/ 会在启动时自动迁移到该位置）
BACKUP_DIR = paths.BACKUP_DIR
KEEP_COUNT = 20  # 每种 tag 保留的最近备份份数


def _ensure_dir():
    try:
        os.makedirs(BACKUP_DIR, exist_ok=True)
        return True
    except Exception:
        return False


def _digest_file(path):
    """计算文件 md5，用于去重（内容未变化不重复备份）。"""
    try:
        with open(path, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()
    except Exception:
        return None


def _list_backups(tag):
    """返回 _internal/backup/ 下属于该 tag 的备份文件名（新 → 旧）。"""
    try:
        names = [
            n
            for n in os.listdir(BACKUP_DIR)
            if n.startswith(tag + "_") and n.endswith(".json")
        ]
        names.sort(reverse=True)
        return names
    except Exception:
        return []


def backup_file(path, tag="homework", keep=KEEP_COUNT):
    """
    将数据文件备份到 _internal/backup/ 目录，命名为 <tag>_<时间戳>.json。

    - 源文件缺失 / 不可读时返回 None；
    - 与最新一份备份内容一致（md5 相同）时跳过，不产生重复文件；
    - 超出 keep 份数的最旧备份会被清理。

    返回备份文件相对路径（成功时）或 None。
    """
    if not path or not os.path.exists(path):
        return None
    digest = _digest_file(path)
    if digest is None:
        return None
    if not _ensure_dir():
        return None

    # 去重：与最新备份一致则不重复备份
    latest = _list_backups(tag)
    if latest:
        newest_path = os.path.join(BACKUP_DIR, latest[0])
        if _digest_file(newest_path) == digest:
            return os.path.join(BACKUP_DIR, latest[0])

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    name = "%s_%s.json" % (tag, timestamp)
    target = os.path.join(BACKUP_DIR, name)
    seq = 1
    while os.path.exists(target):
        seq += 1
        name = "%s_%s_%d.json" % (tag, timestamp, seq)
        target = os.path.join(BACKUP_DIR, name)

    try:
        shutil.copy2(path, target)
    except Exception:
        return None

    # 清理超出保留份数的旧备份（从最旧开始）
    files = list(_list_backups(tag))
    while len(files) > max(1, keep):
        old = os.path.join(BACKUP_DIR, files.pop())
        try:
            os.remove(old)
        except Exception:
            pass
    return os.path.join(BACKUP_DIR, name)


def list_backups(tag="homework"):
    """列出 _internal/backup/ 下某 tag 的备份文件名（新 → 旧）。"""
    return _list_backups(tag)


def backup_all():
    """备份核心数据文件：homework.json 与 setting.json。"""
    backup_file("homework.json", tag="homework")
    backup_file(paths.CONFIG_FILE, tag="setting")


if __name__ == "__main__":
    backup_all()
    print("backup dir:", BACKUP_DIR)
    print("homework backups:", list_backups("homework"))
    print("setting backups:", list_backups("setting"))
