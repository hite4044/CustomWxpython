import wx

from .animation_widget import AnimationWidget
from ..animation import MultiColorGradientAnimation, KeyFrameAnimation, MAKE_ANIMATION, KeyFrameCurves
from ..dpi import SCALE
from ..render import CustomGraphicsContext
from ..style import WidgetStyle, ToggleSwitchStyle, Style

TS_OFF = 0
TS_ON = 1


class ToggleSwitch(AnimationWidget):
    class OwnMultiColorAnimation(MultiColorGradientAnimation):
        start_fix = "off"

        def set_target(self, name: str, invent: bool = False):
            super().set_target(self.start_fix + (("_" + name) if name else ""), invent)

    WND_NAME = "cwxSwitch"
    style: ToggleSwitchStyle

    bg_anim: OwnMultiColorAnimation
    sym_anim: KeyFrameAnimation

    LABEL_PAD = 10

    def __init__(self, parent: wx.Window, label: str = "", style: int = TS_OFF,
                 widget_style: WidgetStyle | None = None):
        super().__init__(parent, widget_style=widget_style)
        self.is_on: bool = bool(style & TS_ON)

        self.init_animation()
        self.Bind(wx.EVT_MOUSE_EVENTS, self.on_mouse_events)
        self.Bind(wx.EVT_KEY_DOWN, self.on_key_down)

        self.update_bg_fix = lambda: setattr(self.bg_anim, "start_fix", "on" if self.is_on else "off")
        self.crt_bg = wx.Colour(self.style.bg.normal)
        self.crt_border = wx.Colour(self.style.border.normal)
        self.sym_pos = (30, 10) if self.is_on else (10, 30)
        self.text_extent = (1.0, 1.0, 1.0, 1.0)
        self.SetLabel(label)

    def init_animation(self):
        """初始按钮动画的函数"""
        during = 0.2
        self.bg_anim = self.OwnMultiColorAnimation(
            during,
            ("off", self.style.bg.normal), ("off_hover", self.style.bg.hover),
            ("off_pressed", self.style.bg.pressed), ("off_disable", self.style.bg.disabled),
            ("on", self.style.active_bg.normal), ("on_hover", self.style.active_bg.hover),
            ("on_pressed", self.style.active_bg.pressed), ("on_disable", self.style.active_bg.disabled)
        )
        if self.is_on:
            self.bg_anim.set_default_target("on")
        else:
            self.bg_anim.set_default_target("off")
        self.sym_anim = MAKE_ANIMATION(during, KeyFrameCurves.CUBE_EASE_OUT)

        self.reg_animation("bg", self.bg_anim)
        self.reg_animation("sym", self.sym_anim)

    def on_key_down(self, event: wx.KeyEvent):
        event.Skip()
        if event.GetKeyCode() == wx.WXK_SPACE:
            self.__chk()

    def on_mouse_events(self, event: wx.MouseEvent):
        event.Skip()
        self.update_bg_fix()
        if event.Entering():
            if event.LeftIsDown():
                self.bg_anim.set_target("pressed")
            else:
                self.bg_anim.set_target("hover")
        elif event.Leaving():
            self.bg_anim.set_target("")
        elif event.LeftDown():
            self.bg_anim.set_target("pressed")
        elif event.LeftUp():
            self.__chk()
            self.bg_anim.set_target("hover")
        else:
            return
        self.play_animation("bg")
        self.Refresh()

    def __chk(self):
        self.is_on = not self.is_on
        self.update_bg_fix()

        if self.sym_anim.is_playing and not self.sym_anim.is_invent:
            self.sym_anim.set_invent(True)
        else:
            self.sym_anim.set_invent(False)
            if self.sym_anim.percent_offset != 0:
                self.sym_anim.percent_offset = 1 - self.sym_anim.percent_offset
            self.sym_pos = (10, 30) if self.is_on else (30, 10)
        self.bg_anim.set_target("")
        self.play_animation("sym")
        self.play_animation("bg")
        self.Refresh()

    def Enable(self, enable=True):
        super().Enable(enable)
        self.update_bg_fix()
        self.crt_border = self.style.border.normal if enable else self.style.border.disabled
        self.bg_anim.set_target("disable" if not enable else "")
        self.play_animation("bg")

    @staticmethod
    def translate_style(style: Style) -> ToggleSwitchStyle:
        return style.toggle_switch_style

    def load_widget_style(self, style: ToggleSwitchStyle):
        super().load_widget_style(style)
        if not self.initializing_style:
            self.init_animation()

    def animation_callback(self):
        if self.bg_anim.is_playing:
            self.crt_bg = self.bg_anim.value
        elif self.sym_anim.is_playing:
            pass
        else:
            return
        self.Refresh()

    def draw_content(self, gc: CustomGraphicsContext):
        self.draw_switch(gc)  # 绘制背景
        with gc.State:
            gc.Translate((40 + self.LABEL_PAD) * SCALE, 0)
            self.draw_label_content(gc)  # 绘制内容

    def draw_switch(self, gc: CustomGraphicsContext):
        """绘制开关及其背景"""
        w, h = self.GetTupClientSize()
        with gc.State:
            gc.Translate(0, int(h / 2 - 10))
            # 绘制背景
            gc.SetBrush(gc.CreateBrush(wx.Brush(self.crt_bg)))
            if self.is_on:
                gc.SetPen(gc.CreatePen(wx.GraphicsPenInfo(self.crt_bg)))
            else:
                gc.SetPen(gc.CreatePen(wx.GraphicsPenInfo(self.crt_border)))
            gc.DrawInnerRoundedRect(0, 0, 40 * SCALE, 20 * SCALE, self.style.box_radius * SCALE,
                                        self.style.border_width * SCALE)

            # 绘制开关
            if self.is_on:
                gc.SetBrush(self.style.active_sym.create_brush(gc, (w, h)))
            else:
                gc.SetBrush(self.style.sym.create_brush(gc, (w, h)))
            cx = (self.sym_anim.value * (self.sym_pos[1] - self.sym_pos[0])) + self.sym_pos[0]
            cy = 10 * SCALE
            radius = self.style.sym_radius * SCALE
            gc.DrawEllipse(cx - radius, cy - radius - 0.5, radius * 2, radius * 2)

    def SetLabel(self, label: str):
        super().SetLabel(label)
        gc = CustomGraphicsContext(wx.GraphicsContext.Create(self))
        gc.SetFont(gc.CreateFont(self.GetFont(), self.style.fg))
        self.refresh_extent(gc)
        size = (int((40 + self.LABEL_PAD) * SCALE + self.text_extent[0]), int(max(30 * SCALE, self.text_extent[1])))
        self.RawSetMinSize(size)
        self.RawCacheBestSize(size)
        self.RawSetSize(size)

    def refresh_extent(self, gc: CustomGraphicsContext):
        self.text_extent = gc.GetFullTextExtent(self.GetLabel())

    def draw_label_content(self, gc: CustomGraphicsContext):
        """绘制标签内容"""
        w, h = self.GetTupClientSize()
        if not self.IsEnabled():
            text_color = self.style.fg.disabled
        else:
            text_color = self.style.fg.normal

        label = self.GetLabel()
        gc.SetFont(gc.CreateFont(self.GetFont(), text_color))
        self.refresh_extent(gc)
        with gc.State:
            gc.Translate(self.text_extent[2], self.text_extent[3])
            gc.DrawText(label, 0, h / 2 - (self.text_extent[1] / 2))
