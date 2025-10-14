import typing

import wx

from .base_widget import Widget
from cwx.style import WidgetStyle
from cwx.render import CustomGraphicsContext


class StaticBitmap(Widget):
    """静态位图"""
    gc_bitmap: wx.GraphicsBitmap

    def __init__(self, parent: wx.Window, bitmap: wx.Bitmap = wx.NullBitmap, style: int = 0,
                 widget_style: WidgetStyle | None = None):
        super().__init__(parent, style, widget_style)
        self.bitmap = bitmap
        self.gc_bitmap = self.cvt_bitmap(bitmap)
        self.set_size()

    def set_size(self):
        if not self.bitmap.IsOk():
            return
        size = typing.cast(tuple[int, int], self.bitmap.GetSize().Get())
        self.RawSetSize(size)
        self.RawSetMinSize(size)

    @staticmethod
    def cvt_bitmap(bitmap: wx.Bitmap) -> wx.GraphicsBitmap | None:
        if bitmap.IsOk():
            return CustomGraphicsContext.Create().CreateBitmap(bitmap)
        return None

    def SetBitmap(self, bitmap: wx.Bitmap):
        self.bitmap = bitmap
        self.gc_bitmap = self.cvt_bitmap(bitmap)

    def draw_content(self, gc: CustomGraphicsContext):
        if self.gc_bitmap:
            gc.DrawBitmap(self.bitmap, 0, 0)
