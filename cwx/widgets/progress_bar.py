from typing import cast as type_cast

import wx

from .animation_widget import AnimationWidget
from .. import KeyFrameWay
from ..animation import EZKeyFrameAnimation
from ..style import ProgressBarStyle, Style


class ProgressBar(AnimationWidget):
    style: ProgressBarStyle
    border_pen: wx.Pen
    bg_brush: wx.Brush
    value_anim: EZKeyFrameAnimation

    # noinspection PyShadowingBuiltins
    def __init__(self, parent: wx.Window, style=0, widget_style: ProgressBarStyle = None,
                 range: float = 100, value: float = 0):
        super().__init__(parent, style, widget_style, fps=60)
        self.value = value
        self.range = range
        self.value_anim = EZKeyFrameAnimation(10, KeyFrameWay.SMOOTH, value / range, value / range)
        self.reg_animation("value", self.value_anim)

        if style | wx.VERTICAL:
            self.direction = wx.VERTICAL
            self.CacheBestSize(wx.Size(200, 21))
        else:
            self.direction = wx.HORIZONTAL
            self.CacheBestSize(wx.Size(21, 200))
        self.SetSize(type_cast(tuple[int, int], self.GetBestSize().GetIM()))

    @staticmethod
    def translate_style(style: Style) -> ProgressBarStyle:
        return style.progress_bar_style

    def load_widget_style(self, style: ProgressBarStyle):
        super().load_widget_style(style)
        self.bg_brush = wx.Brush(style.bg)
        self.border_pen = wx.Pen(style.border)

    def draw_content(self, gc: wx.GraphicsContext):
        w, h = type_cast(tuple[int, int], self.GetClientSize())

        gc.SetBrush(gc.CreateBrush(self.bg_brush))
        gc.SetPen(gc.CreatePen(self.border_pen))
        gc.DrawRoundedRectangle(0, 0, w - 1, h - 1, self.style.corner_radius)

        gc.SetPen(gc.CreatePen(wx.Pen(wx.RED, 0, wx.PENSTYLE_TRANSPARENT)))
        target_x = (w - 2) * self.value_anim.value  # self.value / self.range
        print(target_x)
        bar_brush = gc.CreateLinearGradientBrush(0, 0, target_x, h, self.style.bar, self.style.bar_stop)
        gc.SetBrush(bar_brush)
        if target_x <= self.style.corner_radius * 2:
            gc.DrawRoundedRectangle(1, 1, self.style.corner_radius * 2, h - 2, self.style.corner_radius)
        else:
            gc.DrawRoundedRectangle(1, 1, target_x, h - 2, self.style.corner_radius)

    def update_animation(self):
        self.value_anim.set_range(self.value_anim.value, self.value / self.range)
        self.play_animation("value")

    def animation_callback(self):
        self.Refresh()

    # 外部函数

    def SetValue(self, value: float):
        self.value = value
        self.update_animation()
        self.Refresh()

    def GetValue(self):
        return self.value

    def SetPercent(self, value: float):
        assert 0 <= value <= 1
        self.value = value * self.range
        self.value_anim.set_range(self.value_anim.value, value)

    def GetPercent(self):
        return self.value / self.range

    # noinspection PyShadowingBuiltins
    def SetRange(self, range: float):
        self.range = range
        self.update_animation()
        self.Refresh()

    def GetRange(self) -> float:
        return self.range
