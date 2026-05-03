import json

SUBJECT_CODES = [
    "C",
    "M",
    "E",
    "P1",
    "H1",
    "G1",
    "PH1",
    "PH2",
    "CH1",
    "CH2",
    "B1",
    "OTH",
]

MAX = 2

def update_data(level,data):
    if level == 0:
        data["VER"] = 1
        for item in SUBJECT_CODES:
            for i in range(len(data[item])):
                data[item][i]["emphasize"] = "Standard"
        with open("homework.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    elif level == 1:
        data["VER"] = 2
        EMPHASIZE_LEVELS_OLD = ["Ignored", "Unimportant", "Standard", "Urgent"]
        EMPHASIZE_LEVELS = ["很低", "低", "标准", "高"]
        for item in SUBJECT_CODES:
            for i in range(len(data[item])):
                data[item][i]["emphasize"] = EMPHASIZE_LEVELS[EMPHASIZE_LEVELS_OLD.index(data[item][i]["emphasize"])]
        with open("homework.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    while True:
        try:
            with open("homework.json", "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.decoder.JSONDecodeError:
            print("homework.json 内容无效或为空，请检查文件内容。")
            break

        if data.get("VER", 0) < MAX:
            print("正在更新数据... VER:", data.get("VER"))
            update_data(data.get("VER", 0), data)
        else:
            print("数据已是最新版本，无需更新。")
            break