"""
按钮
"""
import webbrowser
from typing import cast as type_cast

import wx

from .animation_widget import AnimationWidget
from .base_widget import MaskState
from ..dpi import SCALE
from ..event import SimpleCommandEvent
from ..lib.adv_anim import StateGradientAnimation
from ..render import CustomGraphicsContext
from ..style import Style, BtnStyle, HyperlinkBtnStyle

cwxEVT_BUTTON = wx.NewEventType()
EVT_BUTTON = wx.PyEventBinder(cwxEVT_BUTTON, 1)


class ButtonEvent(SimpleCommandEvent):
    eventType: int = cwxEVT_BUTTON


# class AutoBaseColorWrapper
class ButtonBase(AnimationWidget):
    style: BtnStyle
    bg_anim: StateGradientAnimation
    border_anim: StateGradientAnimation

    def __init__(self, parent: wx.Window, widget_style: BtnStyle = None):
        """按钮基类"""
        super().__init__(parent, widget_style=widget_style, fps=60)
        self.mask_state = MaskState.NONE
        self.crt_bg = wx.Colour(self.style.bg)
        self.crt_border = wx.Colour(self.style.border)
        self.init_animation()

        self.Bind(wx.EVT_MOUSE_EVENTS, self.on_mouse_events)

    def init_animation(self):
        """初始按钮动画的函数"""

        self.bg_anim = StateGradientAnimation(0.1, self.style.bg)
        self.border_anim = StateGradientAnimation(0.1, self.style.border)
        self.reg_animation("bg", self.bg_anim)
        self.reg_animation("border", self.border_anim)

    def animation_callback(self):
        if self.bg_anim.is_playing:
            self.crt_bg = self.bg_anim.value
        if self.border_anim.is_playing:
            self.crt_border = self.border_anim.value

        self.Refresh()

    def on_mouse_events(self, event: wx.MouseEvent):
        event.Skip()
        if event.Entering():
            if event.LeftIsDown():
                self.mask_state = MaskState.PRESSED
                self.bg_anim.set_target(self.mask_state)
            else:
                self.mask_state = MaskState.HOVER
                self.bg_anim.set_target(self.mask_state)
        elif event.Leaving():
            self.mask_state = MaskState.NONE
            self.bg_anim.set_target(self.mask_state)
        elif event.LeftDown():
            self.mask_state = MaskState.PRESSED
            self.bg_anim.set_target(self.mask_state)
            self.on_button()
            self.ProcessEvent(ButtonEvent(self))
        elif event.LeftUp():
            self.mask_state = MaskState.HOVER
            self.bg_anim.set_target(self.mask_state)
        else:
            return
        self.play_animation("bg")
        self.Refresh()

    def on_button(self):
        """点击时触发, 该函数比EVT_BUTTON早触发, 为特殊按钮类的功能提供支持"""
        pass

    def Enable(self, enable: bool = True):
        super().Enable(enable)
        self.bg_anim.set_target(MaskState.DISABLED, enable)
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
            self.bg_anim['normal'] = style.bg.normal
            self.bg_anim['float'] = style.bg.hover
            self.bg_anim['pressed'] = style.bg.pressed
            self.bg_anim['disable'] = style.bg.disabled

    def draw_content(self, gc: CustomGraphicsContext):
        self.draw_btn_background(gc)  # 绘制背景
        self.draw_btn_content(gc)  # 绘制内容

    def draw_btn_background(self, gc: CustomGraphicsContext):
        w, h = self.GetTupClientSize()

        border_width = self.style.border_width * SCALE
        gc.SetPen(gc.CreatePen(wx.GraphicsPenInfo(self.crt_border, border_width, self.style.border_style)))
        gc.SetBrush(gc.CreateBrush(wx.Brush(self.crt_bg)))
        gc.DrawInnerRoundedRect(0, 0,
                                w, h,
                                self.style.corner_radius * SCALE, border_width)

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
                          MaskState.HOVER: self.style.fg.normal,
                          MaskState.PRESSED: self.style.fg.pressed}[self.mask_state]

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
