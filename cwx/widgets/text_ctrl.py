import wx

from cwx.style import WidgetStyle
from cwx.widgets.base_widget import Widget



class TextCtrlBase(Widget):
    def __init__(self, parent: wx.Window, text: str, widget_style: WidgetStyle = None):
        super().__init__(parent, widget_style=widget_style)

        self.text = text

    def GetTextSize(self):
        gc = wx.GraphicsContext.Create()
        gc.SetFont(self.GetFont())
        return gc.GetFullTextExtent(self.text)

    def SetValue(self, text: str):
        self.text = text

    def GetValue(self) -> str:
        return self.text

    def SetIMEPosition(self, pos: tuple[int, int]):
        pass
