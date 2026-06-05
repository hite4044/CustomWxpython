import json


class LanguageLoader:
    pass

class WidgetStrings:
    def __init__(self, path: str):
        with open(path, "r", encoding="utf-8") as f:
            self.strings = json.load(f)