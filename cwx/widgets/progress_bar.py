import math
from typing import cast as type_cast

import wx

from .animation_widget import AnimationWidget
from ..animation import EZKeyFrameAnimation, KeyFrameCurves
from ..dpi import SCALE
from ..render import GCRender, ARC, CustomGraphicsContext
from ..style import ProgressBarStyle, Style


class ProgressBar(AnimationWidget):
    style: ProgressBarStyle
    border_pen: wx.GraphicsPenInfo
    bg_brush: wx.Brush
    value_anim: EZKeyFrameAnimation

    # noinspection PyShadowingBuiltins
    def __init__(self, parent: wx.Window, style=0, widget_style: ProgressBarStyle = None,
                 range: float = 100, value: float = 0):
        super().__init__(parent, style, widget_style, fps=60)
        self.value = value
        self.range = range
        self.value_anim = EZKeyFrameAnimation(0.3, KeyFrameCurves.QUADRATIC_EASE, value / range, value / range)
        self.reg_animation("value", self.value_anim)

        if style | wx.VERTICAL:
            self.direction = wx.VERTICAL
            self.CacheBestSize((200, 21))
        else:
            self.direction = wx.HORIZONTAL
            self.CacheBestSize((21, 200))
        self.SetSize(type_cast(tuple[int, int], self.GetBestSize().GetIM()))

    @staticmethod
    def translate_style(style: Style) -> ProgressBarStyle:
        return style.progress_bar_style

    def load_widget_style(self, style: ProgressBarStyle):
        super().load_widget_style(style)
        self.bg_brush = wx.Brush(style.bg)

    def draw_content(self, gc: CustomGraphicsContext):
        w, h = type_cast(tuple[int, int], self.GetClientSize())
        border_width = round(self.style.border.width * SCALE)
        TRANSPARENT_PEN = gc.CreatePen(wx.GraphicsPenInfo(wx.BLACK, border_width, wx.PENSTYLE_TRANSPARENT))

        # 背景
        gc.SetBrush(gc.CreateBrush(self.bg_brush))
        gc.SetPen(self.style.border.create_pen(gc, (w, h)))
        GCRender.RenderInnerRoundedRect(gc, border_width, self.style.corner_radius)

        # 进度条
        gc.SetPen(TRANSPARENT_PEN)
        target_x = (w - border_width * 2) * self.value_anim.value
        br = self.style.bar.create_brush(gc, (w if self.style.full_gradient else target_x, h))
        gc.SetBrush(br)
        if target_x <= self.style.corner_radius * 2:
            radius = self.style.corner_radius
            path = gc.CreatePath()
            fix_percent = max(0.0, math.cos((target_x + border_width) / radius))  # 由小渐快大
            path.AddArc(target_x - radius / 2, h - (radius + border_width),
                        radius, ARC(90 * (1 - fix_percent)), ARC(0), 0)
            path.AddArc(target_x - radius / 2, radius + border_width,
                        radius, ARC(0), ARC(270 + 90 * fix_percent), 0)
            path.AddArc(border_width + radius, radius + border_width,
                        radius, ARC(270 - 90 * fix_percent), ARC(180), 0)
            path.AddArc(border_width + radius, h - (radius + border_width),
                        radius, ARC(180), ARC(90 + 90 * fix_percent), 0)
            gc.DrawPath(path)
        else:
            gc.DrawRoundedRectangle(border_width, border_width,
                                    target_x, h - border_width * 2,
                                    self.style.corner_radius)

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
