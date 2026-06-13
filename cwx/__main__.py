from time import perf_counter

from cwx import CustomGraphicsContext

timer = perf_counter()
import wx
import cwx
import faulthandler
from cwx.font import ft

faulthandler.enable()


class Frame(cwx.Frame):
    def __init__(self):
        super().__init__(None, -1, "Custom Wxpython", size=(700, 500))
        CustomGraphicsContext.force_transparent_text = True

        style = cwx.Style(is_dark=True)
        # style.frame_style.accent_state = cwx.AccentState.COLORED_BLUR
        # style.frame_style.accent_color = wx.Colour(255, 182, 52, 50)
        style.frame_style.backdrop_type = cwx.BackdropType.ACRYLIC
        # style.frame_style.bg = wx.Colour(44, 44, 44)
        # style.frame_style.bg = wx.Colour(243, 243, 243)

        self.load_style(style)

        self.SetFont(ft(10))

        sizer = wx.BoxSizer(wx.VERTICAL)

        st = cwx.StaticText(self,
                            label="The brushes below are part of WinUl 3 and you can reference them in your app. For example:")

        sizer.Add(st)

        btn = cwx.HyperlinkButton(self, "点我啊!")
        btn.url = "https://space.bilibili.com/277685481"
        sizer.Add(btn, 0)

        btn = cwx.Button(self, "Standard XAML Button")
        sizer.Add(btn, 0)

        sizer.AddSpacer(5)

        tc = cwx.TextCtrl(self, "Minecraft")
        # tc.load_widget_style(tc.style.桃子)
        # tc.load_widget_style(tc.style)
        sizer.Add(tc, 0, wx.EXPAND)

        sizer.AddSpacer(5)

        bar = cwx.ProgressBar(self, value=5)

        # bar.load_widget_style(bar.style.赛博朋克)
        def func1():
            bar.SetValue(30)
            wx.CallLater(3000, func2)

        def func2():
            bar.SetValue(80)
            wx.CallLater(3000, func1)

        # wx.CallLater(1000, func1)
        # wx.CallLater(2000, btn.Disable)
        # wx.CallLater(4000, btn.Enable)
        sizer.Add(bar, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 5)

        sizer.AddSpacer(5)

        sizer.Add(cwx.StaticLine(self), 0, wx.EXPAND)

        # sizer.AddStretchSpacer()

        # sizer.Add(cwx.CheckBox(self, "我是谁？", style=wx.CHK_CHECKED | wx.ALIGN_RIGHT), 1, wx.EXPAND)
        sizer.Add(cwx.ToggleSwitch(self, label="Toggle Switch"), 0)

        sizer.Add(cwx.CheckBox(self, "just check it!"), 0)
        sizer.Add(cwx.Slider(self), 0, wx.EXPAND)

        self.SetSizer(sizer)

        # light_style = self.gen_style.copy()
        # light_style.set_as_light()
        # wx.CallLater(5000, self.load_style, light_style)

        # dlg = cwx.MessageDialog(self, "This is a message dialog", "Message", wx.OK)
        # wx.CallLater(1000, dlg.ShowModal)


app = wx.App()
frame = Frame()
print("GUI Init Time:", round((perf_counter() - timer) * 100, 2), "ms")
frame.Show()

app.MainLoop()
