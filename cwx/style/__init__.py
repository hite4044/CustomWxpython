from dataclasses import dataclass

from .color import *
from .frame.struct import *
from cwx.lib.settings import GlobalSettings
from cwx.style.frame.dwm import DWM_SYSTEMBACKDROP_TYPE, ACCENT_STATE


class Style:
    default_style: 'WidgetStyle'
    frame_style: 'FrameStyle'
    btn_style: 'BtnStyle'
    textctrl_style: 'TextCtrlStyle'
    static_line_style: 'StaticLineStyle'
    progress_bar_style: 'ProgressBarStyle'

    def __init__(self, colors: Colors | None = None):
        if colors is None:
            colors = Colors.default()
        self.colors = colors
        self.is_dark = Style.sys_is_dark()

        self.load()

    def load(self):
        self.default_style = EmptyStyle.load(self)
        self.frame_style = FrameStyle.load(self)
        self.btn_style = BtnStyle.load(self)
        self.textctrl_style = TextCtrlStyle.load(self)
        self.static_line_style = StaticLineStyle.load(self)
        self.progress_bar_style = ProgressBarStyle.load(self)

    @staticmethod
    def sys_is_dark():
        return wx.SystemSettings.GetAppearance().IsDark()

    def set_as_light(self):
        self.colors.bg = wx.Colour(240, 240, 240)
        self.colors.fg = wx.BLACK
        self.is_dark = False

        self.load()
        self.frame_style.caption_theme = FrameTheme.LIGHT
        return self

    def set_as_dark(self):
        self.colors.bg = wx.BLACK
        self.colors.fg = wx.WHITE
        self.is_dark = True

        self.load()
        self.frame_style.caption_theme = FrameTheme.DARK
        return self


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


class WidgetStyle:
    """
    用于记录组件绘制的颜色、边框等信息, 注意样式信息应当不进行DPI转换
    Including information about widget's drawing, such as color, border
    """

    def __init__(self, fg: wx.Colour = wx.WHITE, bg: wx.Colour = wx.BLACK):
        self.fg = fg
        self.bg = bg

    @staticmethod
    def load(style: Style) -> 'WidgetStyle':
        """
        负责将主题转化为组件样式
        Translate gen style into widget style.
        """
        return WidgetStyle(
            style.colors.fg,
            style.colors.bg
        )


class EmptyStyle(WidgetStyle):
    pass


class FrameStyle(WidgetStyle):
    """
    accent_state: 人
    """
    def __init__(self, fg: wx.Colour, bg: wx.Colour,
                 caption_theme: FrameTheme,
                 backdrop_type: BackdropType,
                 accent_type: AccentState,
                 accent_color: wx.Colour | None = None):
        super().__init__(fg, bg)
        self.caption_theme = caption_theme
        self.backdrop_type = backdrop_type

        self.accent_state = accent_type
        self.accent_color: wx.Colour | None = accent_color  # 颜色记得带透明度, CT.with_alpha
        """颜色记得带透明度, CT.with_alpha"""

    @classmethod
    def load(cls, style: Style) -> 'FrameStyle':
        colors = style.colors
        return cls(
            fg=colors.fg,
            bg=colors.bg,
            caption_theme=GlobalSettings.default_caption_theme,
            backdrop_type=GlobalSettings.default_backdrop_type,
            accent_type=GlobalSettings.default_frame_accent,
        )


@dataclass
class BorderStyle:
    color: TransformableColor
    corner_radius: float
    width: float
    style: int

    active_color: GradientColor


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
            border_color=TC(ColorTransformer.with_alpha(ColorTransformer.light1(colors.primary), 128)),
            corner_radius=6,
            border_width=2,
            border_style=wx.PENSTYLE_SOLID
        )


class TextCtrlStyle(WidgetStyle):
    def __init__(self,
                 input_fg: wx.Colour,
                 input_bg: wx.Colour,
                 border: wx.Colour,
                 active_tl_border: wx.Colour,
                 active_br_border: wx.Colour,
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
        self.active_tl_border = active_tl_border
        self.active_br_border = active_br_border
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
            active_tl_border=colors.primary,
            active_br_border=colors.primary,
            cursor=colors.input_fg,
            select_fg=colors.input_fg,
            select_bg=colors.primary,

            corner_radius=4,
            select_corder_radius=5,
            border_width=1,
            active_border_width=2,
            border_style=wx.PENSTYLE_SOLID
        )

    @property
    def 桃子(self) -> 'TextCtrlStyle':
        self.active_tl_border = wx.Colour(0xfc, 0xcb, 0x90)
        self.active_br_border = wx.Colour(0xd5, 0x7e, 0xeb)
        return self


class StaticLineStyle(WidgetStyle):
    @staticmethod
    def load(style: Style) -> 'StaticLineStyle':
        return StaticLineStyle(
            bg=style.colors.border,
        )


class ProgressBarStyle(WidgetStyle):
    def __init__(self,
                 bg: wx.Colour, bar: GradientBrush,
                 border: GradientPen, corner_radius: float,
                 full_gradient: bool):
        super().__init__(bg=bg)
        self.corner_radius = corner_radius
        self.bar = bar
        self.border = border
        self.full_gradient = full_gradient

    @staticmethod
    def load(style: Style) -> 'ProgressBarStyle':
        return ProgressBarStyle(
            bg=ColorTransformer.with_alpha(style.colors.bg, 40),
            bar=GradientBrush(CT.dark1(style.colors.primary), CT.light1(style.colors.primary)),
            border=GradientPen(style.colors.border, width=1),
            corner_radius=5,
            full_gradient=True
        )

    @property
    def 赛博朋克(self) -> 'ProgressBarStyle':
        self.bar.gradient_stops.SetStartColour(wx.Colour(0x00, 0xdb, 0xde))
        self.bar.gradient_stops.SetEndColour(wx.Colour(0xfc, 0x00, 0xff))
        return self


class CheckBoxStyle(WidgetStyle):
    def __init__(self,
                 fg: wx.Colour, box_active_bg: GradientBrush, box_hover_bg: GradientBrush,
                 box_sym_pen: GradientPen, box_border: GradientPen,
                 box_corner_radius: float, box_size: float):
        """
        Args:
            fg: label's color.
            box_active_bg: background color when the box is active.
            box_sym_pen: symbol's color (in the box).
            box_border: border color of the box.
        """
        super().__init__(fg)
        self.box_active_bg: GradientBrush = box_active_bg
        self.box_hover_bg: GradientBrush = box_hover_bg
        self.box_sym: GradientPen = box_sym_pen
        self.box_border: GradientPen = box_border
        self.box_corner_radius: float = box_corner_radius
        self.box_size: float = box_size

    @classmethod
    def load(cls, style: Style) -> 'CheckBoxStyle':
        return cls(
            style.colors.fg,
            GradientBrush(style.colors.primary),
            GradientBrush(wx.Colour(255, 255, 255, 10) if style.is_dark else wx.Colour(0, 0, 0, 10)),
            GradientPen(style.colors.fg, width=2),
            GradientPen(style.colors.border, width=1),
            3,
            20
        )
