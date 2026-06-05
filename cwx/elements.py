from enum import Enum
from typing import Any

import wx

from cwx.render import CustomGraphicsContext


class GenericColor(wx.Colour):
    def create_brush(self) -> wx.GraphicsBrush:
        pass

    def create_pen(self) -> wx.GraphicsPen:
        pass


class StateColor(GenericColor):
    normal: GenericColor
    hover: GenericColor
    pressed: GenericColor
    disabled: GenericColor


class Align(Enum):
    TOP_LEFT = 0
    CENTER = 1


class MaskState(Enum):
    NONE = 0  # 无
    HOVER = 1  # 鼠标悬浮在控件上面
    PRESSED = 2  # 鼠标按下
    DISABLED = 3  # 禁用


class BaseElement:
    __KEEP_REF = CustomGraphicsContext  # 保持引用

    def __init__(self, wnd: wx.Window):
        self.wnd: wx.Window = wnd
        self.align: Align = Align.TOP_LEFT
        self.x: float = 0
        self.y: float = 0

    def check_state(self, width: float, height: float) -> MaskState:
        if not self.wnd.IsEnabled():
            return MaskState.DISABLED
        if self.align == Align.TOP_LEFT:
            rect = wx.Rect2D(self.x, self.y, width, height)
        elif self.align == Align.CENTER:
            rect = wx.Rect2D(self.x - width / 2, self.y - height / 2, width, height)
        mouse_pt = self.wnd.ScreenToClient(wx.GetMousePosition())
        if rect.Contains(mouse_pt):
            if wx.GetMouseState().LeftIsDown():
                return MaskState.PRESSED
            else:
                return MaskState.HOVER
        else:
            return MaskState.NONE

    def draw(self, gc: 'CustomGraphicsContext'): ...

    @classmethod
    def from_json(cls: Any, wnd: wx.Window, obj: dict[str, Any]) -> Any:
        return cls(wnd, **obj)


class BaseWrapper:
    enable: bool = False


class ColorGradientWrapper(BaseElement, BaseWrapper):
    def __init__(self):
        object.__init__(self)

    def update(self):
        pass


class ColorGradientColor(BaseElement, BaseWrapper):
    def __init__(self):
        object.__init__(self)


class RectElement(ColorGradientWrapper):
    def __init__(self, wnd: wx.Window,
                 width: int, height: int, corner_radius: int,
                 fill: GenericColor, stroke: GenericColor):
        BaseElement.__init__(self, wnd)
        ColorGradientWrapper.__init__(self)
        self.width: int = width
        self.height: int = height
        self.corner_radius: float = corner_radius
        self.fill: GenericColor = fill
        self.stroke: GenericColor = stroke

    def draw(self, gc: 'CustomGraphicsContext'):
        gc.SetBrush(self.fill.create_brush())
        gc.SetPen(self.stroke.create_pen())
        if self.align == Align.TOP_LEFT:
            gc.DrawRoundedRectangle(self.x, self.y, self.width, self.height, self.corner_radius)



class LabelElement(BaseElement):
    def __init__(self, wnd: wx.Window, label: str, color: wx.Colour):
        super().__init__(wnd)
        self.font: wx.Font = wnd.GetFont()
        self.label: str = label
        self.color: wx.Colour = color

    def set_font(self, font: wx.Font):
        self.font = font

    def draw(self, gc: 'CustomGraphicsContext'):
        gc.SetFont(gc.CreateFont(self.font, self.color))
        gc.DrawText(self.label, 0, 0)
