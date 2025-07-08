import ctypes
from copy import deepcopy
from ctypes import wintypes
from dataclasses import dataclass
from typing import TypeVar

import colour
import wx

dwmapi = ctypes.WinDLL('dwmapi.dll')


def get_windows_theme_color():
    HRESULT = wintypes.LONG

    DwmGetColorizationColor = dwmapi.DwmGetColorizationColor
    DwmGetColorizationColor.argtypes = [ctypes.POINTER(wintypes.DWORD), ctypes.POINTER(wintypes.BOOL)]
    DwmGetColorizationColor.restype = HRESULT

    cr_colorization = wintypes.DWORD()
    f_opaque_blend = wintypes.BOOL()

    result = DwmGetColorizationColor(ctypes.byref(cr_colorization), ctypes.byref(f_opaque_blend))

    if result == 0:  # S_OK 的值为 0
        r = (cr_colorization.value >> 16) % 256
        g = (cr_colorization.value >> 8) % 256
        b = (cr_colorization.value >> 0) % 256
        return r, g, b
    else:
        return 0, 111, 196  # 如果获取颜色失败，返回 None


class LuminanceColor:
    def __init__(self, color: tuple[int, int, int] | wx.Colour):
        if isinstance(color, wx.Colour):
            color = color.GetRed(), color.GetGreen(), color.GetBlue()
        self.color = colour.Color(rgb=(color[0] / 255, color[1] / 255, color[2] / 255))
        self.base = self.color.get_luminance()

    def add_luminance(self, value: float):
        self.color.set_luminance(max(min(self.base + value, 1), 0))
        color: tuple[int, int, int] = self.color.get_rgb()
        return wx.Colour((int(color[0] * 255), int(color[1] * 255), int(color[2] * 255)))


class EasyColor(colour.Color):
    def __init__(self, color: tuple):
        super().__init__(rgb=(color[0] / 255, color[1] / 255, color[2] / 255))

    def add_luminance(self, value: float):
        self.set_luminance(max(min(self.get_luminance() + value, 1), 0))

    @property
    def rgb_tuple(self) -> tuple[int, int, int]:
        return int(self.get_red() * 255), int(self.get_green() * 255), int(self.get_blue() * 255)

    @property
    def int_rgb(self) -> int:
        color = self.rgb_tuple
        return (color[0] << 16) | (color[1] << 8) | color[2]


class TransformableColor(wx.Colour):
    color: EasyColor

    def __init__(self, color: tuple[int, int, int] | tuple[int, int, int, int] | wx.Colour):
        super().__init__(color)
        if isinstance(color, wx.Colour):
            color = (color.GetRed(), color.GetGreen(), color.GetBlue(), color.GetAlpha())
        self.base_rgba = color
        self.color = EasyColor(color[:3])
        self.base_color = self.color.get_rgb()

    def reset(self):
        self.color.set_rgb(self.base_color)
        self.Set(*self.base_rgba)
        return self

    def add_luminance(self, value: float):
        self.color.add_luminance(value)
        self.Set(*self.color.rgb_tuple, self.GetAlpha())
        return self

    @property
    def copy(self):
        return TransformableColor(wx.Colour(self.Get()))

    def set_alpha(self, alpha: int):
        rgb: int = self.GetRGB()
        rgba = (rgb << 8) | alpha
        self.SetRGBA(rgba)


class TC(TransformableColor):
    """TransformableColor的简写"""
    pass


COLOR_LEVEL = 0.04


class ColorTransformer:
    @staticmethod
    def with_alpha(color: wx.Colour, alpha: int):
        return wx.Colour(color.Red(), color.Green(), color.Blue(), alpha)

    @staticmethod
    def add_luminance(color: wx.Colour, luminance: float):
        color = LuminanceColor(color)
        return color.add_luminance(luminance)

    @staticmethod
    def highlight(color: wx.Colour):
        return ColorTransformer.add_luminance(color, COLOR_LEVEL)

    # light level

    @staticmethod
    def light1(color: wx.Colour):
        return ColorTransformer.add_luminance(color, COLOR_LEVEL)

    @staticmethod
    def light2(color: wx.Colour):
        return ColorTransformer.add_luminance(color, COLOR_LEVEL * 2)

    @staticmethod
    def light3(color: wx.Colour):
        return ColorTransformer.add_luminance(color, COLOR_LEVEL * 3)

    @staticmethod
    def dark1(color: wx.Colour):
        return ColorTransformer.add_luminance(color, -COLOR_LEVEL)

    @staticmethod
    def dark2(color: wx.Colour):
        return ColorTransformer.add_luminance(color, -COLOR_LEVEL * 2)

    @staticmethod
    def dark3(color: wx.Colour):
        return ColorTransformer.add_luminance(color, -COLOR_LEVEL * 3)


class DefaultColors:
    def __init__(self):
        self.PRIMARY = wx.Colour(get_windows_theme_color())


class Colors:
    def __init__(self,
                 primary: wx.Colour,
                 secondary: wx.Colour,
                 fg: wx.Colour,
                 bg: wx.Colour,
                 border: wx.Colour,
                 input_fg: wx.Colour,
                 input_bg: wx.Colour):
        self.primary = primary
        self.secondary = secondary
        self.fg = fg
        self.bg = bg
        self.border = border
        self.input_fg = input_fg
        self.input_bg = input_bg

    @staticmethod
    def default():
        return Colors(
            primary=DefaultColors().PRIMARY,
            secondary=wx.Colour(85, 85, 85, 128),
            fg=wx.Colour(255, 255, 255),
            bg=wx.BLACK,
            border=wx.Colour(85, 85, 85),
            input_fg=wx.Colour(255, 255, 255),
            input_bg=wx.Colour(0, 0, 0, 40)
        )


class Style:
    def __init__(self):
        self.colors = Colors.default()

        self.default_style = EmptyStyle.load(self)
        self.btn_style = BtnStyle.load(self)
        self.textctrl_style = TextCtrlStyle.load(self)
        self.static_line_style = StaticLineStyle.load(self)
        self.progress_bar_style = ProgressBarStyle.load(self)


class WidgetStyle:
    def __init__(self, fg: wx.Colour = wx.WHITE, bg: wx.Colour = wx.BLACK):
        self.fg = fg
        self.bg = bg

    @staticmethod
    def load(style: Style) -> 'WidgetStyle':
        return WidgetStyle(
            style.colors.fg,
            style.colors.bg
        )


class EmptyStyle(WidgetStyle):
    pass


@dataclass
class BorderStyle:
    color: TransformableColor
    corner_radius: float
    width: float
    style: int


class BtnStyle(WidgetStyle):
    fg: TransformableColor
    bg: TransformableColor

    def __init__(self,
                 fg: TransformableColor,
                 bg: TransformableColor,
                 border_color: wx.Colour,
                 corner_radius: float,
                 border_width: float,
                 border_style: int,
                 ):
        """
        :param fg: 按钮文字颜色
        :param bg: 按钮背景
        :param border_color: 边框颜色
        :param corner_radius: 边框圆角半径
        :param border_width: 边框宽度
        :param border_style: 边框样式 (wx.GraphicsPenInfo的样式)
        """
        super().__init__(fg, bg)
        self.border_color = border_color
        self.corner_radius = corner_radius
        self.border_width = border_width
        self.border_style = border_style

    @staticmethod
    def load(style: Style) -> 'BtnStyle':
        colors = style.colors

        return BtnStyle(
            fg=TC(colors.fg),
            bg=TC(ColorTransformer.light1(colors.primary)),
            border_color=ColorTransformer.with_alpha(colors.primary, 128),
            corner_radius=6,
            border_width=2,
            border_style=wx.PENSTYLE_SOLID
        )


class TextCtrlStyle(WidgetStyle):
    def __init__(self,
                 input_fg: wx.Colour,
                 input_bg: wx.Colour,
                 border: wx.Colour,
                 active_border: wx.Colour,
                 cursor: wx.Colour,
                 select_fg: wx.Colour,
                 select_bg: wx.Colour,

                 corner_radius: float,
                 select_corder_radius: float,
                 border_width: float,
                 active_border_width: float,
                 border_style: int):
        super().__init__(input_fg, input_bg)
        self.border = border
        self.active_border = active_border
        self.cursor = cursor
        self.select_fg = select_fg
        self.select_bg = select_bg

        self.corner_radius = corner_radius
        self.select_corder_radius = select_corder_radius
        self.border_width = border_width
        self.active_border_width = active_border_width
        self.border_style = border_style

    @staticmethod
    def load(style: Style) -> 'TextCtrlStyle':
        colors = style.colors

        return TextCtrlStyle(
            input_fg=colors.input_fg,
            input_bg=colors.input_bg,
            border=colors.border,
            active_border=colors.primary,
            cursor=colors.input_fg,
            select_fg=colors.input_fg,
            select_bg=colors.primary,

            corner_radius=4,
            select_corder_radius=5,
            border_width=1,
            active_border_width=2,
            border_style=wx.PENSTYLE_SOLID
        )


class StaticLineStyle(WidgetStyle):
    @staticmethod
    def load(style: Style) -> 'StaticLineStyle':
        return StaticLineStyle(
            bg=style.colors.border,
        )

class ProgressBarStyle(WidgetStyle):
    def __init__(self,
                 bg: wx.Colour, bar: wx.Colour, bar_stop: wx.Colour,
                 border: wx.Colour, corner_radius: float):
        super().__init__(
            bg=bg,
        )
        self.corner_radius = corner_radius
        self.bar = bar
        self.bar_stop = bar_stop
        self.border = border


    @staticmethod
    def load(style: Style) -> 'ProgressBarStyle':
        return ProgressBarStyle(
            bg=ColorTransformer.with_alpha(style.colors.bg, 40),
            bar=ColorTransformer.dark1(style.colors.primary),
            bar_stop=ColorTransformer.light1(style.colors.primary),
            border=style.colors.border,
            corner_radius=5
        )


app = wx.App()
print(get_windows_theme_color())
