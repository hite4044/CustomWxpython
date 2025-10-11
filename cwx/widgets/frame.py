import typing

import wx

from cwx import Widget, CustomGraphicsContext, WidgetStyle, Style, StyleType
from cwx.lib.dwm import ACCENT_STATE
from cwx.lib.settings import GlobalSettings
from cwx.lib.window_style import blur_window, set_caption_color, set_frame_dark


class TopLevelWrapper(Widget):
    """请使用Frame或者Dialog, 这个创建的窗口关闭不了"""
    init_wnd = False
    enable_double_buffer = False

    init_with_blur = None  # 创建窗口时默认启用模糊

    def __init__(self, *args, gen_style: Style | None = None, **kwargs):
        if gen_style:
            self.gen_style = gen_style

        Widget.__init__(self, self)
        self.WindowBlurEnabled = False

        if (self.init_with_blur is True) or (self.init_with_blur is None and GlobalSettings.auto_blur_toplevel):
            self.EnableWindowBlur()

    def EnableWindowBlur(self,
                         enable: bool = True,
                         color: tuple[int, int, int, int] | tuple[int, int, int] | wx.Colour | None = None,
                         accent_state: int = ACCENT_STATE.ACCENT_ENABLE_ACRYLICBLURBEHIND):
        """启用窗口透明, 仅在Win10+起效"""
        self.WindowBlurEnabled = enable

        if isinstance(color, wx.Colour):
            f_color = (color.Red(), color.Green(), color.Blue(), color.Alpha())
        elif isinstance(color, tuple):
            f_color = color + ((50,) if len(color) == 3 else ())
        else:
            f_color = None
        blur_window(self.GetHandle(), enable, f_color, accent_state=accent_state)

    def SetCaptionDark(self, is_dark: bool = True):
        """如果系统允许了应用深色模式, 设置窗口标题栏为深色"""
        set_frame_dark(self.GetHandle(), is_dark)

    def SetCaptionColor(self, color: wx.Colour):
        """设置标题栏颜色"""
        set_caption_color(self.GetHandle(), typing.cast(tuple[int, int, int], color.Get()))

    def load_style(self, style: Style):
        self.SetCaptionDark(style.style_type == StyleType.DARK)
        super().load_style(style)

    def load_widget_style(self, style: WidgetStyle):
        super().load_widget_style(style)
        super().SetForegroundColour(style.fg)
        super().SetBackgroundColour(style.bg)

    def draw_content(self, gc: CustomGraphicsContext):
        gc.SetBrush(wx.Brush(self.style.bg))
        gc.DrawRectangle(0, 0, *self.GetClientSize())


class Frame(wx.Frame, TopLevelWrapper):
    def __init__(self, *args, gen_style: Style | None = None, **kwargs):
        wx.Frame.__init__(self, *args, **kwargs)
        TopLevelWrapper.__init__(self, *args, gen_style=gen_style, **kwargs)


class Dialog(wx.Dialog, TopLevelWrapper):
    def __init__(self, *args, gen_style: Style | None = None, **kwargs):
        wx.Dialog.__init__(self, *args, **kwargs)
        TopLevelWrapper.__init__(self, *args, gen_style=gen_style, **kwargs)
