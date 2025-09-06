from typing import cast as type_cast

import wx

from .base_widget import Widget
from ..style import WidgetStyle


class StaticText(Widget):
    style: WidgetStyle
    text_color: wx.Colour

    def __init__(self, parent: wx.Window, label: str, widget_style: WidgetStyle = None):
        super().__init__(parent, widget_style=widget_style)
        self.SetLabel(label)

    def SetLabel(self, label: str):
        super().SetLabel(label)
        dc = wx.ClientDC(self)
        width, height = type_cast(tuple, dc.GetTextExtent(label))
        self.SetSize((width, height))
        self.SetMinSize((width, height))

    def load_widget_style(self, style: WidgetStyle):
        super().load_widget_style(style)
        self.text_color = style.fg

    def draw_content(self, gc: wx.GraphicsContext):
        gc.SetFont(gc.CreateFont(self.GetFont(), col=wx.Colour(255, 255, 255)))
        gc.DrawText(self.GetLabel(), 0, 0)
