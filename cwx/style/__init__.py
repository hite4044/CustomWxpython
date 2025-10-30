from cwx.lib.settings import GlobalSettings
from cwx.style.frame.dwm import DWM_SYSTEMBACKDROP_TYPE, ACCENT_STATE
from .color import *
from .frame.struct import *


class Style:
    default_style: 'WidgetStyle'
    frame_style: 'TopLevelStyle'
    btn_style: 'BtnStyle'
    textctrl_style: 'TextCtrlStyle'
    static_line_style: 'StaticLineStyle'
    progress_bar_style: 'ProgressBarStyle'

    def __init__(self, colors: Colors | None = None):
        self.is_dark = Style.sys_is_dark()
        if colors is None:
            colors = Colors.default(self.is_dark)
        self.colors = colors

        self.load()

    def load(self):
        self.default_style = EmptyStyle.load(self)
        self.frame_style = TopLevelStyle.load(self)
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


@dataclass
class Foreground(wx.Colour):
    float: wx.Colour
    pressed: wx.Colour
    disabled: wx.Colour

    def __init__(self, normal: wx.Colour,
                 float: wx.Colour = None, pressed: wx.Colour = None, disabled: wx.Colour = None):
        if float is None:
            float = normal
        if pressed is None:
            pressed = normal
        if disabled is None:
            disabled = normal

        super().__init__(normal)
        self.float = float
        self.pressed = pressed
        self.disabled = disabled

    @property
    def normal(self):
        return self

    @normal.setter
    def normal(self, value: wx.Colour):
        self.SetRGBA(value.GetRGBA())

    @classmethod
    def from_colors(cls, text: Colors.TextColors):
        return cls(text.primary, text.secondary, text.primary, text.secondary)


@dataclass
class Background(wx.Colour):
    float: wx.Colour
    pressed: wx.Colour
    disabled: wx.Colour

    def __init__(self, normal: wx.Colour,
                 float: wx.Colour = None, pressed: wx.Colour = None, disabled: wx.Colour = None):
        if float is None:
            float = normal
        if pressed is None:
            pressed = normal
        if disabled is None:
            disabled = normal

        super().__init__(normal)
        self.float = float
        self.pressed = pressed
        self.disabled = disabled

    @property
    def normal(self):
        return self

    @normal.setter
    def normal(self, value: wx.Colour):
        self.SetRGBA(value.GetRGBA())

    @classmethod
    def from_colors(cls, background: Colors.BackColors):
        return cls(background.default, background.secondary, background.tertiary, background.disabled)


class WidgetStyle:
    """
    用于记录组件绘制的颜色、边框等信息, 注意样式信息应当不进行DPI转换
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
            Background.from_colors(style.colors.back),
        )


class EmptyStyle(WidgetStyle):
    pass


class TopLevelStyle(WidgetStyle):
    bg: wx.Colour

    def __init__(self, bg: Background,
                 caption_theme: FrameTheme,
                 backdrop_type: BackdropType,
                 accent_type: AccentState,
                 accent_color: wx.Colour | None = None):
        super().__init__(bg=bg)
        self.raw_bg = bg
        self.is_default_bg = True
        self.caption_theme = caption_theme
        self.backdrop_type = backdrop_type

        self.accent_state = accent_type
        self.accent_color: wx.Colour | None = accent_color  # 颜色记得带透明度, CT.with_alpha
        "颜色记得带透明度, CT.with_alpha"

    @classmethod
    def load(cls, style: Style) -> 'TopLevelStyle':
        return cls(
            bg=Background(TRANSPARENT_COLOR),
            caption_theme=GlobalSettings.default_caption_theme,
            backdrop_type=GlobalSettings.default_backdrop_type,
            accent_type=GlobalSettings.default_frame_accent,
        )

    @property
    def bg(self):
        return self.raw_bg

    @bg.setter
    def bg(self, value: wx.Colour):
        self.raw_bg = value
        self.is_default_bg = False


@dataclass
class BorderStyle:
    color: TransformableColor
    corner_radius: float
    width: float
    style: int

    active_color: GradientColor


class BtnStyle(WidgetStyle):
    fg: Foreground
    bg: Background

    def __init__(self,
                 fg: Foreground,
                 bg: Background,
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

    @classmethod
    def load(cls, style: Style) -> 'BtnStyle':
        colors = style.colors
        return cls(
            fg=Foreground.from_colors(colors.text),
            bg=Background.from_colors(colors.back),
            border_color=TC(colors.back.default).with_alpha(30),
            corner_radius=6,
            border_width=1,
            border_style=wx.PENSTYLE_SOLID
        )


class HyperlinkBtnStyle(BtnStyle):
    @classmethod
    def load(cls, style: Style) -> 'BtnStyle':
        widget_style = super().load(style)
        widget_style.bg.normal = TRANSPARENT_COLOR
        widget_style.bg.disabled = TRANSPARENT_COLOR
        widget_style.border_color = TRANSPARENT_COLOR

        widget_style.fg.normal = style.colors.accent_text.primary
        widget_style.fg.float = style.colors.accent_text.secondary
        widget_style.fg.pressed = style.colors.accent_text.tertiary
        widget_style.fg.disabled = style.colors.text.disabled

        return widget_style


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


class ToggleSwitchStyle(WidgetStyle):
    def __init__(self,
                 box_bg: GradientBrush, box_hover_bg: GradientBrush, box_active_bg: GradientBrush,
                 box_border: GradientPen, box_sym: GradientBrush,
                 ):
        super().__init__()
        self.box_bg: GradientBrush = box_bg
        self.box_hover_bg: GradientBrush = box_hover_bg
        self.box_active_bg: GradientBrush = box_active_bg
        self.box_border: GradientPen = box_border
        self.box_sym: GradientBrush = box_sym

        self.box_radius: float = 10
