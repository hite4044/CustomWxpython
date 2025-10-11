import win32con as con
import wx
from win32gui import GetWindowLong, SetWindowLong

from cwx import Widget
from cwx.blur import blur_window
from cwx.lib.dwm import ACCENT_STATE


class Frame(wx.Frame):
    def __init__(self, *args, **kwargs):
        wx.Frame.__init__(self, *args, **kwargs)
        wnd_style = GetWindowLong(self.GetHandle(), con.GWL_EXSTYLE)
        wnd_style |= con.WS_EX_LAYERED
        SetWindowLong(self.GetHandle(), con.GWL_EXSTYLE, wnd_style)

        self.SetDoubleBuffered(True)

        self.WindowBlurEnabled = False
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
        blur_window(self, enable, f_color, accent_state=accent_state)
