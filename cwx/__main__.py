from time import perf_counter

from cwx.blur import blur_window
from cwx.font import ft

timer = perf_counter()
import wx
import pywinstyles
import cwx
import faulthandler
faulthandler.enable()


class Frame(wx.Frame):
    def __init__(self):
        super().__init__(None, -1, "Custom Wxpython", size=(700, 500))
        self.SetFont(ft(12))
        blur_window(self)
        self.SetBackgroundColour(wx.BLACK)
        # pywinstyles.apply_style(self, "acrylic")
        # self.SetBackgroundColour(wx.Colour(0, 0, 0))

        sizer = wx.BoxSizer(wx.VERTICAL)

        sizer.Add(cwx.StaticText(self, "hite404"))

        sizer.Add(cwx.Button(self, "点我啊!"), 0)

        sizer.AddSpacer(5)

        tc = cwx.TextCtrl(self, "fuck you 阿敏哦斯++++五十")
        tc.load_widget_style(tc.style.桃子)
        sizer.Add(tc, 0)

        sizer.AddSpacer(5)

        bar = cwx.ProgressBar(self, value=5)
        bar.load_widget_style(bar.style.赛博朋克)
        def func1():
            bar.SetValue(30)
            wx.CallLater(3000, func2)
        def func2():
            bar.SetValue(80)
            wx.CallLater(3000, func1)
        #wx.CallLater(1000, func1)
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
