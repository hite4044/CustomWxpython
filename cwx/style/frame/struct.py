from enum import auto, Enum


class CaptionTheme(Enum):
    AUTO = auto()
    LIGHT = auto()
    DARK = auto()


class BackdropType(Enum):
    AUTO = 0  # 无

    NONE = 1  # 纯色
    ACRYLIC = 3  # 亚克力
    MICA = 2  # 磨砂桌面背景
    MICA_ALT = 4  # 磨砂桌面背景 (更深)


class AccentState(Enum):
    DISABLE = 0  # 禁用

    COLORED = 1  # 纯色
    TRANSPARENT = 5  # 透明
    COLORED_TRANSPARENT = 2  # 带颜色透明
    BLUR = 3  # 模糊
    COLORED_BLUR = 4  # 带颜色模糊
