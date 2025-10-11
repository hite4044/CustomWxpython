from typing import cast as type_cast

import wx

from .base_widget import Widget
from ..render import CustomGraphicsContext
from ..style import WidgetStyle


class StaticText(Widget):
    style: WidgetStyle
    text_font: wx.GraphicsFont

    def __init__(self, parent: wx.Window, label: str, widget_style: WidgetStyle = None):
        super().__init__(parent, widget_style=widget_style)
        self.SetLabel(label)

    def SetLabel(self, label: str):
        super().SetLabel(label)
        dc = wx.ClientDC(self)
        width, height = type_cast(tuple, dc.GetTextExtent(label))
        self.SetSize((width, height))
        self.SetMinSize((width, height))

    def draw_content(self, gc: CustomGraphicsContext):
        gc.SetFont(gc.CreateFont(self.GetFont(), col=self.style.fg))
        gc.DrawText(self.GetLabel(), 0, 0)
