import typing

import wx

from cwx.style import TopLevelStyle, Style, FrameTheme, AccentState, WidgetStyle
from cwx.style.frame import set_window_composition, set_caption_color, set_frame_dark, BackdropType, \
    set_window_backdrop, DwmExtendFrameIntoClientArea
from cwx.widgets import Widget, TopWindowCanvas


class TopLevelWrapper(Widget):
    """请使用Frame或者Dialog, 这个创建的窗口关闭不了"""
    init_wnd = False
    enable_double_buffer = False

    init_with_blur = None  # 创建窗口时默认启用模糊, True: 启用, False: 禁用, None: 跟随全局设置

    def __init__(self, widget_style: TopLevelStyle | None = None, gen_style: Style | None = None):
        if gen_style:
            self.gen_style = gen_style

        self.WindowBlurEnabled = False
        Widget.__init__(self, self, widget_style=widget_style)

        # self.Refresh = lambda :None

    def EnableWindowComposition(self,
                                enable: bool = True,
                                color: tuple[int, int, int, int] | tuple[int, int, int] | wx.Colour | None = None,
                                accent_state: AccentState = AccentState.BLUR):
        """启用窗口透明, 仅在Win10+起效"""
        if not self.WindowBlurEnabled and enable:
            self.WindowBlurEnabled = True

        if isinstance(color, wx.Colour):
            f_color = (color.Red(), color.Green(), color.Blue(), color.Alpha())
        elif isinstance(color, tuple):
            f_color = color + ((50,) if len(color) == 3 else ())
        else:
            f_color = None
        set_window_composition(self.GetHandle(), enable, f_color, accent_state=accent_state.value)
        return enable

    def SetBackdropType(self, backdrop_type: BackdropType):
        """设置窗口背景类型"""
        enable = backdrop_type not in (BackdropType.AUTO, BackdropType.NONE)
        DwmExtendFrameIntoClientArea(self.GetHandle(), enable)
        set_window_backdrop(self.GetHandle(), backdrop_type.value)
        return enable

    def SetCaptionTheme(self, theme: FrameTheme):
        """如果系统允许了应用深色模式, 设置窗口标题栏为深色"""
        set_frame_dark(self.GetHandle(),
                       self.gen_style.is_dark if theme == FrameTheme.AUTO else (theme == FrameTheme.DARK))

    def SetCaptionColor(self, color: wx.Colour):
        """设置标题栏颜色"""
        set_caption_color(self.GetHandle(), typing.cast(tuple[int, int, int], color.Get()))

    @staticmethod
    def translate_style(style: Style) -> WidgetStyle:
        widget_style = style.frame_style
        if widget_style.accent_state.enabled or widget_style.backdrop_type.enabled:
            widget_style.bg = wx.BLACK
        return widget_style

    def load_widget_style(self, style: TopLevelStyle):
        super().load_widget_style(style)

        enable_comp = enable_backdrop = False
        self.SetCaptionTheme(style.caption_theme)
        if style.accent_state != AccentState.DONT_SET:
            enable_comp = style.accent_state != AccentState.DISABLE
            self.EnableWindowComposition(enable_comp, style.accent_color, style.accent_state)
        if style.backdrop_type != BackdropType.DONT_SET:
            enable_backdrop = self.SetBackdropType(style.backdrop_type)
        self.WindowBlurEnabled = enable_comp or enable_backdrop

        super().SetForegroundColour(style.fg)
        if style.accent_state in (AccentState.DONT_SET, AccentState.DISABLE):
            super().SetBackgroundColour(style.bg)
        else:
            super().SetBackgroundColour(wx.BLACK)
    #
    # def draw_content(self, gc: CustomGraphicsContext):
    #     gc.SetBrush(wx.Brush(self.style.bg))
    #     gc.DrawRectangle(0, 0, *self.GetClientSize())


class Frame(wx.Frame, TopLevelWrapper):
    WND_NAME = "cwxFrame"

    def __init__(self, parent: wx.Window, id: int = wx.ID_ANY, title: str = '',
                 pos=wx.DefaultPosition, size=wx.DefaultSize, style: int = wx.DEFAULT_FRAME_STYLE,

                 widget_style: TopLevelStyle | None = None, gen_style: Style | None = None):
        wx.Frame.__init__(self, parent, id, title, pos, size, style, name=self.WND_NAME)
        TopLevelWrapper.__init__(self, widget_style, gen_style)

        self.canvas = TopWindowCanvas(self)


class Dialog(wx.Dialog, TopLevelWrapper):
    WND_NAME = "cwxDialog"

    def __init__(self, parent: wx.Window, id: int = wx.ID_ANY, title: str = '',
                 pos=wx.DefaultPosition, size=wx.DefaultSize, style: int = wx.DEFAULT_DIALOG_STYLE,

                 widget_style: TopLevelStyle | None = None, gen_style: Style | None = None):
        wx.Dialog.__init__(self, parent, id, title, pos, size, style, name=self.WND_NAME)
        TopLevelWrapper.__init__(self, widget_style, gen_style)

        self.canvas = TopWindowCanvas(self)
