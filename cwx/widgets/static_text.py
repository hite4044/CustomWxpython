import platform
from math import ceil
from typing import cast as type_cast

import cairo
import wx

from .base_widget import Widget
from cwx.lib.perf import Counter
from cwx.render import CustomGraphicsContext
from cwx.style import WidgetStyle

class StaticText(Widget):
    style: WidgetStyle

    def __init__(self, parent: wx.Window, label: str, widget_style: WidgetStyle = None):
        super().__init__(parent, widget_style=widget_style)
        self.SetLabel(label)

    def SetFont(self, font: wx.Font):
        super().SetFont(font)
        self.RecalculateSize()

    def SetLabel(self, label: str):
        super().SetLabel(label)
        self.RecalculateSize()

    def RecalculateSize(self):
        label = self.GetLabel()
        gc = CustomGraphicsContext(wx.GraphicsContext.Create(self))
        gc.SetFont(gc.CreateFont(self.GetFont(), wx.BLACK))
        width, height, _, _ = type_cast(tuple, gc.GetFullTextExtent(label))
        size = (ceil(width), ceil(height))
        self.RawSetSize(size)
        self.RawSetMinSize(size)

    def draw_content(self, gc: CustomGraphicsContext):
        gc.SetFont(gc.CreateFont(self.GetFont(), col=self.style.fg))
        timer = Counter(create_start=True)
        gc.DrawText(self.GetLabel(), 0, 0)
        print(timer.endT())
