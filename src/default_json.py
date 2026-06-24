import json

KEYS = ["Subjects"]
VALUES = [{"Default": "Default"}]


def check():
    try:
        with open("setting.json", "r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        open("setting.json", "w")
        data = {}
    # 如果缺少 Subjects 项，优先从 homework.json 修复（若存在），否则保持原有默认逻辑
    def has_subjects(d: dict) -> bool:
        return ("Subjects" in d) or ("subjects" in d)

    if not has_subjects(data):
        repaired = False
        try:
            with open("homework.json", "r", encoding="utf-8") as hf:
                hw = json.load(hf)
            # 将 homework.json 的键作为 Subjects 条目，使用字典映射格式 {"科目显示名": "代码"}
            # 目前仅有代码键，因此将键和值都设为相同的代码（例如 "C": "C"）
            if isinstance(hw, dict):
                subjects_map = {k: k for k in hw.keys()}
                if subjects_map:
                    data["Subjects"] = subjects_map
                    repaired = True
        except (FileNotFoundError, json.decoder.JSONDecodeError):
            repaired = False

        if not repaired:
            # 回退为原有的默认值
            data = {}
            for i in range(len(KEYS)):
                data[KEYS[i]] = VALUES[i]
    with open("setting.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    check()
