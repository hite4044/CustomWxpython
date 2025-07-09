from time import perf_counter

from cwx.font import ft

timer = perf_counter()
import wx
import pywinstyles
import cwx


class Frame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, -1, "Custom Wxpython", size=(300, 200))
        self.SetFont(ft(12))
        pywinstyles.apply_style(self, "acrylic")
        self.SetBackgroundColour(wx.Colour(0, 0, 0))
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(cwx.StaticText(self, "666"), 1)
        sizer.Add(cwx.Button(self, "点我啊!"), 0)
        tc = cwx.TextCtrl(self, "fuck you 阿敏哦斯++++五十")
        # tc.SetFont(ft(20))
        sizer.Add(tc, 0)
        sizer.AddSpacer(5)
        bar = cwx.ProgressBar(self, value=50)
        # bar = wx.Gauge(self)
        #bar.SetValue(50)
        def func1():
            bar.SetValue(0)
            wx.CallLater(20000, func2)
        def func2():
            bar.SetValue(100)
            wx.CallLater(5000, func1)

        #wx.CallLater(1000, bar.SetValue, 100)
        #wx.CallLater(5000, bar.SetValue, 0)
        #t = bar.gen_style.progress_bar_style
        #t.bar = wx.Colour((0, 0, 255))  # 蓝
        #t.bar_stop = wx.Colour((255, 0, 255))  # 紫
        #bar.load_widget_style(t)
        sizer.Add(bar, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 5)
        sizer.AddSpacer(5)
        sizer.Add(cwx.StaticLine(self), 0, wx.EXPAND)
        sizer.AddStretchSpacer()
        self.SetSizer(sizer)


app = wx.App()
print("Time:", perf_counter() - timer)
frame = Frame()
frame.Show()

app.MainLoop()
