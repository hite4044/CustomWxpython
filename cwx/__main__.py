from time import perf_counter

from cwx import DefaultStyle, AccentState, BackdropType
from cwx.font import ft

timer = perf_counter()
import wx
import cwx
import faulthandler
faulthandler.enable()


class Frame(cwx.Frame):
    def __init__(self):
        super().__init__(None, -1, "Custom Wxpython", size=(700, 500))
        style= DefaultStyle.DEFAULT
        style.frame_style.backdrop_type = BackdropType.MICA_ALT
        self.load_style(style)
        # self.load_style(DefaultStyle.DARK)
        # self.EnableWindowBlur(False)
        # self.SetBackgroundColour(wx.WHITE)

        self.SetFont(ft(9))
        # self.SetBackgroundColour(wx.BLACK)
        # self.canvas = TopWindowCanvas(self)

        sizer = wx.BoxSizer(wx.VERTICAL)

        st = cwx.StaticText(self, "       Custom Wxpython   hite404")
        sizer.Add(st)

        sizer.Add(cwx.Button(self, "点我啊!"), 0)

        sizer.AddSpacer(5)

        tc = cwx.TextCtrl(self, "Minecraft")
        #tc.load_widget_style(tc.style.桃子)
        #tc.load_widget_style(tc.style)
        sizer.Add(tc, 0, wx.EXPAND)

        sizer.AddSpacer(5)

        bar = cwx.ProgressBar(self, value=5)
        bar.load_widget_style(bar.style.赛博朋克)
        def func1():
            bar.SetValue(30)
            wx.CallLater(3000, func2)
        def func2():
            bar.SetValue(80)
            wx.CallLater(3000, func1)
        # wx.CallLater(1000, func1)
        sizer.Add(bar, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 5)

        sizer.AddSpacer(5)

        sizer.Add(cwx.StaticLine(self), 0, wx.EXPAND)

        sizer.AddStretchSpacer()

        self.SetSizer(sizer)

app = wx.App()
frame = Frame()
print("GUI Init Time:", round((perf_counter() - timer) * 100, 2), "ms")
frame.Show()

app.MainLoop()
