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
    try:
        for i in KEYS:
            data[i]
    except KeyError:
        data = {}
        for i in range(len(KEYS)):
            data[KEYS[i]] = VALUES[i]
    with open("setting.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    check()
