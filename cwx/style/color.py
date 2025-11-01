import ctypes
from ctypes import wintypes
from dataclasses import dataclass
from enum import Enum

import colour
import wx

from ..dpi import SCALE
from ..lib.delay_init import DelayInitWrapper

dwmapi = ctypes.WinDLL('dwmapi.dll')

HRESULT = wintypes.LONG

DwmGetColorizationColor = dwmapi.DwmGetColorizationColor
DwmGetColorizationColor.argtypes = [ctypes.POINTER(wintypes.DWORD), ctypes.POINTER(wintypes.BOOL)]
DwmGetColorizationColor.restype = HRESULT


def get_windows_theme_color():  # 蓝色
    cr_colorization = wintypes.DWORD()
    f_opaque_blend = wintypes.BOOL()

    result = DwmGetColorizationColor(ctypes.byref(cr_colorization), ctypes.byref(f_opaque_blend))

    if result == 0:  # S_OK 的值为 0
        r = (cr_colorization.value >> 16) % 256
        g = (cr_colorization.value >> 8) % 256
        b = (cr_colorization.value >> 0) % 256
        return r, g, b
    else:
        return 0, 111, 196  # 如果获取颜色失败, 返回默认颜色 (蓝色)


class EasyColor(colour.Color):
    """colour.Color的更易于使用的版本"""

    def __init__(self, color: tuple):
        super().__init__(rgb=(color[0] / 255, color[1] / 255, color[2] / 255))

    def add_luminance(self, value: float):
        self.set_luminance(max(min(self.get_luminance() + value, 1), 0))

    def add_saturation(self, value: float):
        self.set_saturation(max(min(self.get_saturation() + value, 1), 0))

    @property
    def rgb_tuple(self) -> tuple[int, int, int]:
        return int(self.get_red() * 255), int(self.get_green() * 255), int(self.get_blue() * 255)

    @property
    def int_rgb(self) -> int:
        color = self.rgb_tuple
        return (color[0] << 16) | (color[1] << 8) | color[2]


class TransformableColor(wx.Colour):
    """一个颜色类, 定义一个可以快捷调节的颜色"""
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

    def add_saturation(self, value: float):
        self.color.add_saturation(value)
        self.Set(*self.color.rgb_tuple, self.GetAlpha())
        return self

    def light1(self):
        return self.add_luminance(LUM_LEVEL)

    def light2(self):
        return self.add_luminance(LUM_LEVEL * 2)

    def light3(self):
        return self.add_luminance(LUM_LEVEL * 3)

    def dark1(self):
        return self.add_luminance(-LUM_LEVEL)

    def dark2(self):
        return self.add_luminance(-LUM_LEVEL * 2)

    def dark3(self):
        return self.add_luminance(-LUM_LEVEL * 3)

    @property
    def copy(self):
        return TransformableColor(wx.Colour(self.Get()))

    def with_alpha(self, alpha: int):
        rgb: int = self.GetRGB()
        rgba = rgb | alpha << 24
        self.SetRGBA(rgba)
        return self


class TC(TransformableColor):
    """可变换颜色(TransformableColor) 的简写"""
    pass


LUM_LEVEL = 0.04  # 亮度等级的计算


class ColorTransformer:
    @staticmethod
    def with_alpha(color: wx.Colour, alpha: int):
        return wx.Colour(color.Red(), color.Green(), color.Blue(), alpha)

    @staticmethod
    def add_luminance(wx_color: wx.Colour, luminance: float):
        """增加颜色"""
        color = colour.Color(rgb=(wx_color.GetRed() / 255, wx_color.GetGreen() / 255, wx_color.GetBlue() / 255))
        base = color.get_luminance()
        color.set_luminance(max(min(base + luminance, 1), 0))
        color_tup: tuple[int, int, int] = color.get_rgb()
        return wx.Colour(int(color_tup[0] * 255), int(color_tup[1] * 255), int(color_tup[2] * 255), wx_color.GetAlpha())

    @staticmethod
    def highlight(color: wx.Colour):
        return ColorTransformer.add_luminance(color, LUM_LEVEL)

    # light level

    @staticmethod
    def light1(color: wx.Colour):
        return ColorTransformer.add_luminance(color, LUM_LEVEL)

    @staticmethod
    def light2(color: wx.Colour):
        return ColorTransformer.add_luminance(color, LUM_LEVEL * 2)

    @staticmethod
    def light3(color: wx.Colour):
        return ColorTransformer.add_luminance(color, LUM_LEVEL * 3)

    @staticmethod
    def dark1(color: wx.Colour):
        return ColorTransformer.add_luminance(color, -LUM_LEVEL)

    @staticmethod
    def dark2(color: wx.Colour):
        return ColorTransformer.add_luminance(color, -LUM_LEVEL * 2)

    @staticmethod
    def dark3(color: wx.Colour):
        return ColorTransformer.add_luminance(color, -LUM_LEVEL * 3)


class CT(ColorTransformer):
    """颜色转换器(ColorTransformer)的简写"""
    pass


class DefaultColors:
    """
    系统默认颜色, 需要在wx.App初始化后使用, 使用已创建实例 TheDefaultColors
    System default color, need initial wx.App instance before use.
    """

    def __init__(self):
        self.PRIMARY = wx.Colour(get_windows_theme_color())


TheDefaultColors: DefaultColors = DelayInitWrapper(DefaultColors)


class Colors:
    """根据WinUI 3的颜色系统设置, WinUI 3的颜色系统真的非常好！"""

    class StateColor:
        KEY_MAP: dict[str, str] = {}
        use_default: bool = True

        @property
        def st_default(self) -> wx.Colour:
            return self.get_color("default")

        @property
        def st_hover(self) -> wx.Colour | None:
            return self.get_color("hover")

        @property
        def st_pressed(self) -> wx.Colour | None:
            return self.get_color("pressed")

        @property
        def st_disabled(self) -> wx.Colour | None:
            return self.get_color("disabled")

        def get_color(self, state: str) -> wx.Colour | None:
            if n := self.KEY_MAP.get(state):
                return getattr(self, n)
            if self.use_default and "default" in self.KEY_MAP:
                return getattr(self, self.KEY_MAP["default"])
            return None

    @dataclass
    class Text(StateColor):
        KEY_MAP = {"default": "primary", "hover": "secondary", "pressed": "tertiary", "disabled": "disabled"}
        primary: wx.Colour
        secondary: wx.Colour
        tertiary: wx.Colour
        disabled: wx.Colour

        @classmethod
        def load(cls, for_dark: bool):
            return cls(
                primary=wx.WHITE if for_dark else wx.Colour(26, 26, 26),
                secondary=wx.Colour(204, 204, 204) if for_dark else wx.Colour(92, 92, 92),
                tertiary=wx.Colour(150, 150, 150) if for_dark else wx.Colour(134, 134, 134),
                disabled=wx.Colour(113, 113, 113) if for_dark else wx.Colour(155, 155, 155)
            )

    @dataclass
    class ControlFill(StateColor):
        KEY_MAP = {"default": "default", "hover": "secondary", "pressed": "tertiary", "disabled": "disabled"}
        default: wx.Colour
        secondary: wx.Colour
        tertiary: wx.Colour
        disabled: wx.Colour

        @classmethod
        def load(cls, for_dark: bool):
            if for_dark:  # 暗色
                std = wx.WHITE
                return cls(
                    default=CT.with_alpha(std, 16),  # Rest
                    secondary=CT.with_alpha(std, 24),  # Hover
                    tertiary=CT.with_alpha(std, 10),  # Pressed
                    disabled=CT.with_alpha(std, 15)  # Disabled
                )
            else:  # 亮色
                std = wx.BLACK
                return cls(
                    default=wx.Colour(255, 255, 255, 0xB3),
                    secondary=wx.Colour(249, 249, 249, 0x50),
                    tertiary=wx.Colour(249, 249, 249, 0x4D),  # Pressed
                    disabled=CT.with_alpha(std, 15)
                )

    @dataclass
    class ControlStroke(StateColor):
        KEY_MAP = {"default": "default", "hover": "secondary"}
        default: wx.Colour
        secondary: wx.Colour

        @classmethod
        def load(cls, for_dark: bool):
            if for_dark:
                return cls(
                    default=wx.Colour(255, 255, 255, 16),
                    secondary=wx.Colour(255, 255, 255, 0x29),
                )
            else:
                return cls(
                    default=wx.Colour(0, 0, 0, 0x0F),
                    secondary=wx.Colour(0, 0, 0, 0x29),
                )

    @dataclass
    class AccentText(StateColor):
        KEY_MAP = {"default": "primary", "hover": "secondary", "pressed": "tertiary", "disabled": "disabled"}
        primary: wx.Colour
        secondary: wx.Colour
        tertiary: wx.Colour
        disabled: wx.Colour

        @classmethod
        def load(cls, for_dark: bool):
            return cls(
                primary=TheDefaultColors.PRIMARY,
                secondary=TheDefaultColors.PRIMARY,
                tertiary=TheDefaultColors.PRIMARY,
                disabled=wx.Colour(113, 113, 113) if for_dark else wx.Colour(155, 155, 155),
            )

    def __init__(self,
                 text: Text,
                 accent_text: AccentText,
                 control_fill: ControlFill,
                 control_stroke: ControlStroke,
                 primary: wx.Colour,
                 secondary: wx.Colour,
                 fg: wx.Colour,
                 bg: wx.Colour,
                 border: wx.Colour):
        self.text = text
        self.accent_text = accent_text
        self.control_fill = control_fill
        self.control_stroke = control_stroke

        self.primary = primary
        self.secondary = secondary
        self.fg = fg
        self.bg = bg
        self.border = border

    @property
    def input_fg(self):
        return self.fg

    @property
    def input_bg(self):
        return ColorTransformer.with_alpha(self.bg, 40)

    @staticmethod
    def default(for_dark: bool):
        return Colors(
            text=Colors.Text.load(for_dark),
            accent_text=Colors.AccentText.load(for_dark),
            control_fill=Colors.ControlFill.load(for_dark),
            control_stroke=Colors.ControlStroke.load(for_dark),
            primary=TheDefaultColors.PRIMARY,
            secondary=wx.Colour(85, 85, 85, 128),
            fg=wx.Colour(255, 255, 255),
            bg=wx.BLACK,
            border=wx.Colour(0, 0, 0, 15)
        )


class GradientDir(Enum):
    HORIZONTAL = 4
    VERTICAL = 8
    TOP_LEFT_CORNER = 12  # 从左上角开始 (到右下角) \ 渐变至左上角
    TOP_RIGHT_CORNER = 16  # 从右上角开始 (到左下角) \ 渐变至右上角

    # 用于圆形渐变
    BOTTOM_LEFT_CORNER = 20  # 渐变至左下角
    BOTTOM_RIGHT_CORNER = 24  # 渐变至右下角
    AS_MAX_SIDE = 24  # 标志使用最远的一条边


class GradientColor(TransformableColor):
    """
    渐变颜色, 快捷使用多种渐变设定
    """

    def __init__(self,
                 color: tuple[int, ...] | wx.Colour,
                 stop_color: tuple[int, ...] | wx.Colour = None,
                 gradient_type: wx.GradientType = wx.GRADIENT_NONE,
                 direction: GradientDir | int = GradientDir.HORIZONTAL,
                 stops: list[tuple[float, tuple[int, int, int] | wx.Colour]] = None):
        """
        :param color: 基础颜色
        :param stop_color: 渐变停止颜色
        :param gradient_type: 渐变类型, 线性或者圆形
        :param direction: 渐变方向
        :param stops: 渐变途径点
        """
        super().__init__(color)
        self.gradient_type = gradient_type
        self.direction: GradientDir | int = direction
        self.stop_is_none = stop_color is None

        self.gradient_stops = wx.GraphicsGradientStops(color, color if stop_color is None else stop_color)
        for percent, stop_color in (stops if stops else []):
            self.gradient_stops.Add(wx.Colour(stop_color), percent)

    @property
    def stop_color(self) -> wx.Colour:
        return self.gradient_stops.GetEndColour()

    @stop_color.setter
    def stop_color(self, color: wx.Colour):
        self.gradient_stops.SetEndColour(color)

    def update_start_color(self):
        self.gradient_stops.SetStartColour(self)

    def update_myself(self):
        self.update_start_color()
        if self.stop_is_none:
            self.stop_color = self

    def Set(self, *args, **kw):
        super().Set(*args, **kw)
        self.update_myself()

    def SetRGB(self, colRGB):
        super().SetRGB(colRGB)
        self.update_myself()

    def SetRGBA(self, colRGBA):
        super().SetRGBA(colRGBA)
        self.update_myself()


class GradientPen(GradientColor):
    ANGLE_CALC_RADIUS = 100

    def __init__(self,
                 color: tuple[int, int, int] | wx.Colour,
                 stop_color: tuple[int, int, int] | wx.Colour = None,
                 gradient_type: int = wx.GRADIENT_LINEAR,
                 direction: GradientDir | int = GradientDir.HORIZONTAL,
                 stops: list[tuple[float, tuple[int, int, int] | wx.Colour]] = None,
                 width: float = 1, pen_style: int = wx.PENSTYLE_SOLID,

                 # 用于圆形渐变
                 radius: float = 100,
                 gradient_from: tuple[float, float] | None = None,
                 gradient_to: tuple[float, float] | None = None,
                 ):
        """
        为GradientColor提供笔(Pen)的预定义配置
        Improve color gradient config for Pen.

        :param color: 主颜色
        :param stop_color: 渐变停止颜色
        :param gradient_type: 渐变类型
        :param direction: 渐变方向 || 停止点所在方位
        :param stops: 渐变途径颜色
        :param width: 笔的线宽
        :param pen_style: 笔的样式
        :param radius: 圆形渐变 - 半径
        :param gradient_from: 圆形渐变 - 渐变起始点, 以位置百分比定义 (0~1)
        :param gradient_to: 圆形渐变 - 渐变结束点, 以位置百分比定义 (0~1)
        """
        super().__init__(color, stop_color, gradient_type, direction, stops)

        self.width = width  # 笔的宽度
        self.pen_style = pen_style  # 笔的样式
        self.radius = radius  # 圆形渐变的半径

        # 圆形渐变的起始位置, (0.0~1.0, 0.0~1.0)
        self.gradient_from: tuple[float, float] = gradient_from if gradient_from else (0.5, 0.5)
        # 圆形渐变的结束位置
        self.gradient_to: tuple[float, float] | None = None if gradient_from is None else gradient_to

    def create_pen(self, gc: wx.GraphicsContext, size: tuple[float, float], dpi_active: bool = True):
        """
        以渐变颜色创建一个笔,
        Create a pen with gradient color.

        :param gc: `wx.GraphicsContext`
        :param size: 控件的大小
        :param dpi_active: 是否自动进行DPI转换
        """
        width = self.width * SCALE if dpi_active else self.width
        pen = wx.GraphicsPenInfo(self, width, self.pen_style).Width(width)
        if self.gradient_type == wx.GRADIENT_LINEAR:
            from_pt = (0, 0)
            if isinstance(self.direction, int) or isinstance(self.direction, float):
                # center = (size[0] / 2, size[1] / 2)
                raise NotImplementedError("Not Implemented direction as number")
            elif self.direction == GradientDir.HORIZONTAL:
                to_pt = (size[0], 0)
            elif self.direction == GradientDir.VERTICAL:
                to_pt = (0, size[1])
            elif self.direction == GradientDir.TOP_LEFT_CORNER:
                to_pt = size
            elif self.direction == GradientDir.TOP_RIGHT_CORNER:
                from_pt = (size[0], 0)
                to_pt = (0, size[1])
            else:
                raise NotImplementedError(f"Not Implemented direction {self.direction} for linear gradient")

            pen = pen.LinearGradient(*from_pt, *to_pt, self.gradient_stops)
        elif self.gradient_type == wx.GRADIENT_RADIAL:  # 圆形渐变
            gradient_center = (size[0] * self.gradient_from[0], size[1] * self.gradient_from[1])
            if self.gradient_to:
                stop_pt = (size[0] * self.gradient_to[0], size[1] * self.gradient_to[1])
            elif self.direction == GradientDir.HORIZONTAL:
                stop_pt = (0, size[1] / 2)
            elif self.direction == GradientDir.VERTICAL:
                stop_pt = (size[0] / 2, 0)
            elif self.direction == GradientDir.TOP_LEFT_CORNER:
                stop_pt = (0, 0)
            elif self.direction == GradientDir.TOP_RIGHT_CORNER:
                stop_pt = (size[0], 0)
            elif self.direction == GradientDir.BOTTOM_LEFT_CORNER:
                stop_pt = (0, size[0])
            elif self.direction == GradientDir.BOTTOM_RIGHT_CORNER:
                stop_pt = size
            else:
                raise NotImplementedError(f"Not Implemented direction {self.direction} for radial gradient")
            pen = pen.RadialGradient(*gradient_center, *stop_pt, self.radius, self.gradient_stops)
        return gc.CreatePen(pen)


class GradientBrush(GradientColor):
    def __init__(self,
                 color: tuple[int, int, int] | wx.Colour,  # 主颜色
                 stop_color: tuple[int, int, int] | wx.Colour = None,  # 渐变停止颜色
                 gradient_type: int = wx.GRADIENT_LINEAR,  # 渐变类型
                 direction: GradientDir | int = GradientDir.HORIZONTAL,  # 渐变方向
                 stops: dict[float, tuple[int, int, int] | wx.Colour] = None,  # 渐变途径点
                 radius: float = 100,
                 gradient_from: tuple[float, float] | None = None,
                 gradient_to: tuple[float, float] | None = None,
                 ):
        """
        为GradientColor提供刷(Brush)的预定义配置
        Improve color gradient config for Brush.

        :param color: 主颜色
        :param stop_color: 渐变停止颜色
        :param gradient_type: 渐变类型
        :param direction: 渐变方向 || 停止点所在方位
        :param stops: 渐变途径颜色
        :param radius: 圆形渐变 - 半径
        :param gradient_from: 圆形渐变 - 渐变起始点, 以位置百分比定义 (0~1)
        :param gradient_to: 圆形渐变 - 渐变结束点, 以位置百分比定义 (0~1)
        """
        super().__init__(color, stop_color, gradient_type, direction, stops)

        self.radius = radius
        self.gradient_from = gradient_from
        self.gradient_to = gradient_to

    def create_brush(self,
                     gc: wx.GraphicsContext,
                     size: tuple[float, float]):
        """
        以渐变颜色创建一个笔刷
        Create a brush with gradient color.

        :param gc: wx.GraphicsContext
        :param size: 控件的大小
        """
        if self.gradient_type == wx.GRADIENT_LINEAR:
            from_pt = (0, 0)
            if isinstance(self.direction, int) or isinstance(self.direction, float):
                # center = (size[0] / 2, size[1] / 2)
                raise NotImplementedError("Not Implemented direction as number")
            elif self.direction == GradientDir.HORIZONTAL:
                stop_pt = (size[0], 0)
            elif self.direction == GradientDir.VERTICAL:
                stop_pt = (0, size[1])
            elif self.direction == GradientDir.TOP_LEFT_CORNER:
                stop_pt = size
            elif self.direction == GradientDir.TOP_RIGHT_CORNER:
                from_pt = (size[0], 0)
                stop_pt = (0, size[1])
            else:
                raise NotImplementedError(f"Not Implemented direction {self.direction} for linear gradient")

            return gc.CreateLinearGradientBrush(*from_pt, *stop_pt, self.gradient_stops)
        elif self.gradient_type == wx.GRADIENT_RADIAL:
            gradient_center = (size[0] * self.gradient_from[0], size[1] * self.gradient_from[1])
            if self.gradient_to:
                stop_pt = (size[0] * self.gradient_to[0], size[1] * self.gradient_to[1])
            elif self.direction == GradientDir.HORIZONTAL:
                stop_pt = (0, size[1] / 2)
            elif self.direction == GradientDir.VERTICAL:
                stop_pt = (size[0] / 2, 0)
            elif self.direction == GradientDir.TOP_LEFT_CORNER:
                stop_pt = (0, 0)
            elif self.direction == GradientDir.TOP_RIGHT_CORNER:
                stop_pt = (size[0], 0)
            elif self.direction == GradientDir.BOTTOM_LEFT_CORNER:
                stop_pt = (0, size[0])
            elif self.direction == GradientDir.BOTTOM_RIGHT_CORNER:
                stop_pt = size
            else:
                raise NotImplementedError(f"Not Implemented direction {self.direction} for radial gradient")

            return gc.CreateRadialGradientBrush(*gradient_center, *stop_pt, self.radius, self.gradient_stops)
        return gc.CreateBrush(wx.Brush(self))


TRANSPARENT_COLOR = wx.Colour(0, 0, 0, 0)
