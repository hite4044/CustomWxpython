from math import ceil
from typing import cast as type_cast

import wx

from cwx.render import CustomGraphicsContext
from cwx.style import WidgetStyle
from .base_widget import Widget


class StaticText(Widget):
    """一段不可选中的文字"""
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
        gc.SetFont(self.GetFont(), wx.BLACK)
        width, height, _, _ = type_cast(tuple, gc.GetFullTextExtent(label))
        size = (ceil(width), ceil(height))
        self.RawSetSize(size)
        self.RawSetMinSize(size)

    def draw_content(self, gc: CustomGraphicsContext):
        gc.SetFont(self.GetFont(), self.style.fg)
        # timer = Counter(create_start=True)
        gc.DrawText(self.GetLabel(), 0, 0)
        # print(timer.endT())
