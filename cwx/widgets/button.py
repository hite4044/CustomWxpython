"""
按钮
"""
import typing
from typing import cast as type_cast

import wx

from .animation_widget import AnimationWidget
from .. import WidgetStyle
from ..animation import KeyFrameAnimation, KeyFrame, KeyFrameCurves, MultiKeyFrameAnimation, ColorGradationAnimation
from ..dpi import SCALE
from ..render import CustomGraphicsContext
from ..style import Style, BtnStyle, TransformableColor, HyperlinkBtnStyle

cwxEVT_BUTTON = wx.NewEventType()
EVT_BUTTON = wx.PyEventBinder(cwxEVT_BUTTON, 1)


class ButtonEvent(wx.PyCommandEvent):
    def __init__(self):
        super().__init__(cwxEVT_BUTTON, wx.ID_ANY)


class ButtonBase(AnimationWidget):
    style: BtnStyle
    bg_anim: MultiKeyFrameAnimation

    def __init__(self, parent: wx.Window, widget_style: BtnStyle = None):
        """按钮基类"""
        super().__init__(parent, widget_style=widget_style, fps=60)
        self.init_animation()

        self.Bind(wx.EVT_MOUSE_EVENTS, self.on_mouse_events)

    def init_animation(self):
        """初始按钮动画的函数"""

        self.bg_anim = MultiKeyFrameAnimation \
            (0.2,
             {"float":
                  ColorGradationAnimation(0.1, self.style.bg.copy, self.style.float_bg.copy),
              "click":
                  KeyFrameAnimation(0.1, [
                      KeyFrame(KeyFrameCurves.SMOOTH, 0, +0.08),
                      KeyFrame(KeyFrameCurves.SMOOTH, 1, -0.08)
                  ]),
              "disable":
                  ColorGradationAnimation(0.1, self.style.bg.copy, self.style.bg.copy.add_luminance(-0.1))
              })

        self.reg_animation("bg", self.bg_anim)

    def animation_callback(self):
        if self.bg_anim.is_playing:
            data = self.bg_anim.value
        else:
            return

        self.style.bg.reset()
        if isinstance(data, float):
            self.style.bg.add_luminance(data)
        else:
            self.style.bg = TransformableColor(data)
        self.Refresh()

    def on_mouse_events(self, event: wx.MouseEvent):
        event.Skip()
        if event.Entering():
            self.bg_anim.set_sub_anim("float")
            self.bg_anim.set_invent(invent=False)
        elif event.Leaving():
            self.bg_anim.set_sub_anim("float")
            self.bg_anim.set_invent(invent=True)
        elif event.LeftDown():
            self.bg_anim.set_sub_anim("click")
            self.bg_anim.set_invent(invent=False)
            event = ButtonEvent()
            wx.PostEvent(self, event)
        elif event.LeftUp():
            self.bg_anim.set_sub_anim("click")
            self.bg_anim.set_invent(invent=True)
        else:
            return
        self.play_animation("bg")
        self.Refresh()

    def Enable(self, enable: bool = True):
        super().Enable(enable)
        self.bg_anim.set_sub_anim("disable")
        self.bg_anim.set_invent(invent=enable)
        self.play_animation("bg")
        self.Refresh()

    def update_size(self):
        width, height = self.get_content_size()
        size = (int(width + 40 * SCALE), int(height + 15 * SCALE))
        self.RawSetSize(size)
        self.RawSetMinSize(size)

    @staticmethod
    def translate_style(style: Style):
        return style.btn_style

    def load_widget_style(self, style: BtnStyle):
        super().load_widget_style(style)
        if not self.initializing_style:
            typing.cast(ColorGradationAnimation, self.bg_anim["disable"])\
                .set_color(style.bg.copy, style.bg.copy.add_luminance(-0.1))
            typing.cast(ColorGradationAnimation, self.bg_anim["float"])\
                .set_color(style.bg.copy, style.float_bg.copy)

    def draw_content(self, gc: CustomGraphicsContext):
        self.draw_btn_background(gc)  # 绘制背景
        self.draw_btn_content(gc)  # 绘制内容

    def draw_btn_background(self, gc: CustomGraphicsContext):
        w, h = self.GetTupClientSize()

        border_width = self.style.border_width * SCALE
        gc.TRANSPARENT_BRUSH
        gc.SetPen(gc.CreatePen(wx.GraphicsPenInfo(self.style.border_color, border_width, self.style.border_style)))
        gc.SetBrush(gc.CreateBrush(wx.Brush(self.style.bg)))
        gc.DrawRoundedRectangle(border_width / 2, border_width / 2,
                                w - border_width, h - border_width,
                                self.style.corner_radius * SCALE)

    def draw_btn_content(self, gc: CustomGraphicsContext):
        pass

    def get_content_size(self) -> tuple[float, float]:
        return 0, 0


class Button(ButtonBase):
    def __init__(self, parent: wx.Window, label: str, widget_style: BtnStyle = None):
        super().__init__(parent, widget_style=widget_style)
        self.SetLabel(label)

    def get_content_size(self) -> tuple[float, float]:
        """获取按钮里内容的大小"""
        gc = CustomGraphicsContext(wx.GraphicsContext.Create(self))
        gc.SetFont(gc.CreateFont(self.GetFont(), self.style.fg))
        return gc.GetFullTextExtent(self.GetLabel())[:2]

    def SetLabel(self, label: str):
        super().SetLabel(label)
        self.update_size()

    def draw_btn_content(self, gc: CustomGraphicsContext):
        w, h = self.GetTupClientSize()
        self.style.fg.reset()
        if not self.IsEnabled():
            self.style.fg.add_luminance(-0.2)
        text_color = self.style.fg.copy

        gc.SetFont(gc.CreateFont(self.GetFont(), text_color))
        label = self.GetLabel()
        t_w, t_h, t_x, t_y = type_cast(tuple[int, int, int, int], gc.GetFullTextExtent(label))
        gc.DrawText(label, int((w - t_w) / 2), int((h - t_h) / 2))


class HyperlinkButton(Button):
    def __init__(self, parent: wx.Window, label: str, widget_style: BtnStyle = None):
        super().__init__(parent, label, widget_style=widget_style)

    @staticmethod
    def translate_style(style: Style):
        return HyperlinkBtnStyle.load(style)
