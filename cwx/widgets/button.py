"""
按钮
"""
import typing
import webbrowser
from typing import cast as type_cast

import wx

from .animation_widget import AnimationWidget
from .base_widget import MaskState
from ..event import SimpleCommandEvent
from ..animation import MultiKeyFrameAnimation, ColorGradationAnimation
from ..dpi import SCALE
from ..render import CustomGraphicsContext
from ..style import Style, BtnStyle, TransformableColor, HyperlinkBtnStyle

cwxEVT_BUTTON = wx.NewEventType()
EVT_BUTTON = wx.PyEventBinder(cwxEVT_BUTTON, 1)


class ButtonEvent(SimpleCommandEvent):
    eventType: int = cwxEVT_BUTTON


class ButtonBase(AnimationWidget):
    style: BtnStyle
    bg_anim: MultiKeyFrameAnimation

    def __init__(self, parent: wx.Window, widget_style: BtnStyle = None):
        """按钮基类"""
        super().__init__(parent, widget_style=widget_style, fps=60)
        self.mask_state = MaskState.NONE
        self.crt_bg = wx.Colour(self.style.bg)
        self.init_animation()

        self.Bind(wx.EVT_MOUSE_EVENTS, self.on_mouse_events)

    def init_animation(self):
        """初始按钮动画的函数"""

        self.bg_anim = MultiKeyFrameAnimation \
            ({"float": ColorGradationAnimation(0.1, self.style.bg, self.style.bg.float),
              "click": ColorGradationAnimation(0.1, self.style.bg.float, self.style.bg.pressed),
              "disable": ColorGradationAnimation(0.1, self.style.bg, self.style.bg.disabled)
              })

        self.reg_animation("bg", self.bg_anim)

    def animation_callback(self):
        if self.bg_anim.is_playing:
            self.crt_bg = self.bg_anim.value
        else:
            return

        self.Refresh()

    def on_mouse_events(self, event: wx.MouseEvent):
        event.Skip()
        if event.Entering():
            if event.LeftIsDown():
                self.mask_state = MaskState.DOWN
                self.bg_anim.set_sub_anim("click")
                self.bg_anim.set_invent(invent=False)
            else:
                self.mask_state = MaskState.BELOW
                self.bg_anim.set_sub_anim("float")
                self.bg_anim.set_invent(invent=False)
        elif event.Leaving():
            self.mask_state = MaskState.NONE
            self.bg_anim.set_sub_anim("float")
            self.bg_anim.set_invent(invent=True)
        elif event.LeftDown():
            self.mask_state = MaskState.DOWN
            self.bg_anim.set_sub_anim("click")
            self.bg_anim.set_invent(invent=False)
            self.on_button()
            self.ProcessEvent(ButtonEvent(self))
        elif event.LeftUp():
            self.mask_state = MaskState.BELOW
            self.bg_anim.set_sub_anim("click")
            self.bg_anim.set_invent(invent=True)
        else:
            return
        self.play_animation("bg")
        self.Refresh()

    def on_button(self):
        """点击时触发, 该函数比EVT_BUTTON早触发, 为特殊按钮类的功能提供支持"""
        pass

    def Enable(self, enable: bool = True):
        super().Enable(enable)
        self.bg_anim.set_sub_anim("disable")
        self.bg_anim.set_invent(invent=enable)
        self.play_animation("bg")
        self.Refresh()

    def update_size(self):
        width, height = self.get_content_size()
        size = (int(width + 32 * SCALE), int(height + 16 * SCALE))
        self.RawSetSize(size)
        self.RawSetMinSize(size)

    @staticmethod
    def translate_style(style: Style):
        return style.btn_style

    def load_widget_style(self, style: BtnStyle):
        super().load_widget_style(style)
        if not self.initializing_style:
            typing.cast(ColorGradationAnimation, self.bg_anim["float"]).set_color(style.bg.normal, style.bg.float)
            typing.cast(ColorGradationAnimation, self.bg_anim["disable"]).set_color(style.bg.normal, style.bg.disabled)

    def draw_content(self, gc: CustomGraphicsContext):
        self.draw_btn_background(gc)  # 绘制背景
        self.draw_btn_content(gc)  # 绘制内容

    def draw_btn_background(self, gc: CustomGraphicsContext):
        w, h = self.GetTupClientSize()

        border_width = self.style.border_width * SCALE
        gc.SetPen(gc.CreatePen(wx.GraphicsPenInfo(self.style.border_color, border_width, self.style.border_style)))
        gc.SetBrush(gc.CreateBrush(wx.Brush(self.crt_bg)))
        gc.DrawRoundedRectangle(border_width / 2, border_width / 2,
                                w - border_width, h - border_width,
                                self.style.corner_radius * SCALE)

    def draw_btn_content(self, gc: CustomGraphicsContext):
        pass

    def get_content_size(self) -> tuple[float, float]:
        return 0, 0


class Button(ButtonBase):
    """一个普通按钮"""
    def __init__(self, parent: wx.Window, label: str, widget_style: BtnStyle = None):
        """
        Args:
            label: 按钮的标签
        """
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
        if not self.IsEnabled():
            text_color = self.style.fg.disabled
        else:
            text_color = {MaskState.NONE: self.style.fg.normal,
                          MaskState.BELOW: self.style.fg.normal,
                          MaskState.DOWN: self.style.fg.pressed}[self.mask_state]

        gc.SetFont(gc.CreateFont(self.GetFont(), text_color))
        label = self.GetLabel()
        t_w, t_h, t_x, t_y = type_cast(tuple[int, int, int, int], gc.GetFullTextExtent(label))
        gc.DrawText(label, int((w - t_w) / 2), int((h - t_h) / 2))


class HyperlinkButton(Button):
    """点击可以跳转至特定网址的按钮"""
    def __init__(self, parent: wx.Window, label: str, url: str = None, widget_style: HyperlinkBtnStyle = None):
        """
        Args:
            url: 网页的网址
            label: 按钮的标签
        """
        super().__init__(parent, label, widget_style=widget_style)
        self.url = url
        """链接至的网页的URL"""
        self.open_new = 0
        """
        - 0: 在默认的浏览器窗口 (默认).
        - 1: 一个新的浏览器窗口.
        - 2: 一个新的浏览器标签页.
        """
        self.auto_raise = True
        """如果可能, 自动弹出浏览器窗口 (默认) 或不弹出."""

    def on_button(self):
        if self.url is not None:
            webbrowser.open(self.url, self.open_new, self.auto_raise)

    @staticmethod
    def translate_style(style: Style):
        return HyperlinkBtnStyle.load(style)
