from typing import TypeVar

from cwx.style.frame.dwm import DWM_SYSTEMBACKDROP_TYPE, ACCENT_STATE
from .color import *
from .frame.struct import *

WS_T = TypeVar('WS_T')


class Style:
    """整个应用程序的样式, 包含了各种组件的组件样式"""
    default_style: 'WidgetStyle'

    REGISTERED_STYLES: dict[str, type['WidgetStyle']] = {}

    @classmethod
    def register_style_cls(cls, style_cls: type['WidgetStyle']):
        """注册一个样式类, 应当在WidgetStyle子类定义时调用"""
        cls.REGISTERED_STYLES[style_cls.__name__] = style_cls

    styles: dict[str, 'WidgetStyle'] = {}

    def as_type(self, cls: type[WS_T]) -> WS_T | None:
        """指定要获取的样式类并尝试返回对应的样式类"""
        return self.styles.get(cls.__name__)

    def as_type_str(self, name: str):
        """指定要获取的样式类并尝试返回对应的样式类"""
        return self.styles.get(name)

    frame_style: 'TopLevelStyle'
    btn_style: 'BtnStyle'
    textctrl_style: 'TextCtrlStyle'
    static_line_style: 'StaticLineStyle'
    progress_bar_style: 'ProgressBarStyle'
    toggle_switch_style: 'ToggleSwitchStyle'

    def __init__(self, is_dark: bool = None, colors: Colors | None = None):
        self.is_dark = is_dark if is_dark is not None else self.sys_is_dark()
        if colors is None:
            colors = Colors.default(self.is_dark)
        self.colors = colors

        self.load()

    @property
    def frame_style(self):
        return self.as_type_str("TopLevelStyle")

    @property
    def btn_style(self):
        return self.as_type_str("BtnStyle")

    @property
    def textctrl_style(self):
        return self.as_type_str("TextCtrlStyle")

    @property
    def static_line_style(self):
        return self.as_type_str("StaticLineStyle")

    @property
    def progress_bar_style(self):
        return self.as_type_str("ProgressBarStyle")

    @property
    def toggle_switch_style(self):
        return self.as_type_str("ToggleSwitchStyle")

    def load(self):
        """初始化各种组件主题"""
        self.default_style = EmptyStyle.load(self)
        for style_cls in self.REGISTERED_STYLES.values():
            print(style_cls)
            self.styles[style_cls.__name__] = style_cls.load(self)

    @staticmethod
    def sys_is_dark():
        """获取系统当前是否为暗色模式"""
        return wx.SystemSettings.GetAppearance().IsDark()

    def set_as_light(self):
        """设置主题为亮色模式, 将会以变更过后的颜色重新加载组件主题, 建议直接使用Style(False)"""
        self.colors = Colors.default(False)
        self.is_dark = False

        self.load()
        # self.frame_style.caption_theme = FrameTheme.LIGHT
        return self

    def set_as_dark(self):
        """设置主题为暗色模式, 将会以变更过后的颜色重新加载组件主题, 建议直接使用Style(True)"""
        self.colors = Colors.default(True)
        self.is_dark = True

        self.load()
        # self.frame_style.caption_theme = FrameTheme.DARK
        return self

    def copy(self):
        """创建主题的副本"""
        from copy import deepcopy
        return deepcopy(self)


class DefaultStyleCls:
    """
    默认主题, 包含亮色+暗色
    """

    @property
    def LIGHT(self) -> Style:
        return Style().set_as_light()

    @property
    def DARK(self) -> Style:
        return Style().set_as_dark()

    @property
    def DEFAULT(self) -> Style:
        return self.DARK if wx.SystemSettings.GetAppearance().IsDark() else self.LIGHT


DefaultStyle = DefaultStyleCls()


class MaskState(Enum):
    NONE = 0  # 无
    HOVER = 1  # 鼠标悬浮在控件上面
    PRESSED = 2  # 鼠标按下
    DISABLED = 3  # 禁用


class MixedStateColor(wx.Colour):
    hover: wx.Colour
    pressed: wx.Colour
    disabled: wx.Colour

    def __init__(self, normal: wx.Colour,
                 hover: wx.Colour = None, pressed: wx.Colour = None, disabled: wx.Colour = None):
        if hover is None:
            hover = normal
        if pressed is None:
            pressed = normal
        if disabled is None:
            disabled = normal

        super().__init__(normal)
        self.hover = hover
        self.pressed = pressed
        self.disabled = disabled

    @property
    def normal(self):
        return self

    @normal.setter
    def normal(self, value: wx.Colour):
        self.SetRGBA(value.GetRGBA())

    @classmethod
    def from_colors(cls, state_color: Colors.StateColor):
        return cls(state_color.st_default, state_color.st_hover, state_color.st_pressed, state_color.st_disabled)


class Foreground(MixedStateColor):
    pass


class Background(MixedStateColor):
    pass


class Stroke(MixedStateColor):
    pass


class Border(MixedStateColor):
    pass


class WidgetStyle:
    """
    用于记录组件绘制的颜色、边框等信息, 注意样式信息应当不经过DPI转换
    Including information about widget's drawing, such as color, border
    """

    fg: Foreground
    bg: Background

    def __init__(self, fg: Foreground | wx.Colour = wx.WHITE, bg: Background | wx.Colour = wx.BLACK):
        if not isinstance(fg, Foreground):
            fg = Foreground(fg)
        if not isinstance(bg, Background):
            bg = Background(bg)
        self.fg = fg
        self.bg = bg

    @staticmethod
    def load(style: Style) -> 'WidgetStyle':
        """
        负责将主题转化为组件样式
        Translate gen style into widget style.
        """
        return WidgetStyle(
            Foreground.from_colors(style.colors.text),
            Background.from_colors(style.colors.control_fill),
        )


class EmptyStyle(WidgetStyle):
    pass
