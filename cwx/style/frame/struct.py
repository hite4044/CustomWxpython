from enum import auto, Enum


class FrameTheme(Enum):
    """窗体绘制的主题, 会影响BackdropType的呈现颜色"""
    AUTO = auto()  # 根据系统主题自动选择
    LIGHT = auto()   # 以亮色绘制
    DARK = auto()   # 以暗色绘制


class BackdropType(Enum):
    """窗口背景的类型, 会在窗口失焦时统一渐变为当前系统纯色"""
    DONT_SET = -1  # 不设置, 使用此值将不会进行任何操作
    AUTO = 0  # 无

    NONE = 1  # 纯色
    ACRYLIC = 3  # 亚克力
    MICA = 2  # 磨砂桌面背景
    MICA_ALT = 4  # 磨砂桌面背景 (更深)

    @property
    def enabled(self):
        return self not in (self.DONT_SET, self.AUTO, self.NONE)


class AccentState(Enum):
    """窗口背景的模糊状态, 会覆盖BackdropType, 窗口失焦时不会变为纯色"""
    DONT_SET = -1   # 不设置, 使用此值将不会进行任何操作
    DISABLE = 0  # 禁用

    COLORED = 1  # 纯色
    TRANSPARENT = 5  # 透明
    COLORED_TRANSPARENT = 2  # 带颜色透明
    BLUR = 3  # 模糊
    COLORED_BLUR = 4  # 带颜色模糊

    @property
    def enabled(self):
        return self not in (self.DONT_SET, self.DISABLE)
