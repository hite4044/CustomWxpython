from dataclasses import dataclass


@dataclass
class MOTDEntry:
    text: str | None
    color: tuple[int, int, int] = None
    bold: bool = False
    italic: bool = False
    underlined: bool = False
    strikethrough: bool = False
    obfuscated: bool = False

    def copy(self):
        return MOTDEntry(self.text, self.color, self.bold, self.italic,
                         self.underlined, self.strikethrough, self.obfuscated)

    def property(self):
        return {
            "color": self.color,
            "bold": self.bold,
            "italic": self.italic,
            "underlined": self.underlined,
            "strikethrough": self.strikethrough,
            "obfuscated": self.obfuscated
        }


def load_color(color: str) -> tuple[int, int, int]:
    if color in named_color_map:
        return named_color_map[color]
    elif color.startswith("#"):
        return int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
    elif color in format_code_color_map:
        return named_color_map[format_code_color_map[color]]
    else:
        raise RuntimeError("炸你没商量！")


named_color_map = {
    "black": (0x00, 0x00, 0x00),
    "dark_blue": (0x00, 0x00, 0xAA),
    "dark_green": (0x00, 0xAA, 0x00),
    "dark_aqua": (0x00, 0xAA, 0xAA),
    "dark_red": (0xAA, 0x00, 0x00),
    "dark_purple": (0xAA, 0x00, 0xAA),
    "gold": (0xFF, 0xAA, 0x00),
    "gray": (0xAA, 0xAA, 0xAA),
    "dark_gray": (0x55, 0x55, 0x55),
    "blue": (0x55, 0x55, 0xFF),
    "green": (0x55, 0xFF, 0x55),
    "aqua": (0x55, 0xFF, 0xFF),
    "red": (0xFF, 0x55, 0x55),
    "light_purple": (0xFF, 0x55, 0xFF),
    "yellow": (0xFF, 0xFF, 0x55),
    "white": (0xFF, 0xFF, 0xFF)
}
format_code_color_map = {
    "0": "black",
    "1": "dark_blue",
    "2": "dark_green",
    "3": "dark_aqua",
    "4": "dark_red",
    "5": "dark_purple",
    "6": "gold",
    "7": "gray",
    "8": "dark_gray",
    "9": "blue",
    "a": "green",
    "b": "aqua",
    "c": "red",
    "d": "light_purple",
    "e": "yellow",
    "f": "white"
}


def load_format_string(format_string: str) -> list[MOTDEntry] | None:
    if "§" not in format_string:
        return None
    active_style = MOTDEntry("")
    next_is_code = False
    entries = []
    for char in format_string:
        if char == "§":
            next_is_code = True
            continue
        elif next_is_code:
            next_is_code = False
            entry = active_style.copy()
            if char in format_code_color_map:
                active_style.color = load_color(format_code_color_map[char])
            elif char == "l" and not active_style.bold:
                active_style.bold = True
            elif char == "o" and not active_style.italic:
                active_style.italic = True
            elif char == "n" and not active_style.underlined:
                active_style.underlined = True
            elif char == "m" and not active_style.strikethrough:
                active_style.strikethrough = True
            elif char == "k" and not active_style.obfuscated:
                active_style.obfuscated = True
            elif char == "r":
                if active_style.text:
                    entries.append(entry)
                active_style = MOTDEntry("")
                continue
            else:  # 属性没有经过更改
                continue
            if active_style.text:
                entries.append(entry)
            active_style.text = ""
        else:
            active_style.text += char
    return entries


MOTD_TYPE = str | dict | list


class MOTD:
    def __init__(self, data: MOTD_TYPE):
        self.entries: list[MOTDEntry] = []
        self.load_data(data)

    def load_data(self, data: MOTD_TYPE, parent_entry: MOTDEntry = None):
        if isinstance(data, str):
            fmt_result = load_format_string(data)
            if fmt_result:
                self.entries.extend(fmt_result)
            else:
                self.entries.append(MOTDEntry(data))
        elif isinstance(data, dict):
            parent_data = parent_entry.property() if parent_entry else {}
            entry = MOTDEntry(data["text"], **parent_data, **data)
            self.entries.append(entry)
            for child_data in data.get("extra", []):
                self.load_data(child_data, entry)
        elif isinstance(data, list):
            for child_data in data:
                self.load_data(child_data)

    def __iter__(self):
        for entry in self.entries:
            yield entry

def test_format_string():
    print(*load_format_string("§6Hi§r, §nI'm§r §m§oWashabi§r  §lLKM!§r"), sep="\n")


if __name__ == "__main__":
    test_format_string()
