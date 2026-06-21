import wx

from cwx.animation import EZKeyFrameAnimation, KeyFrameCurves
from cwx.dpi import SCALE
from cwx.render import CustomGraphicsContext
from cwx.style import WidgetStyle, Style
from cwx.style.color import TRANSPARENT_COLOR
from cwx.widgets.animation_widget import AnimationWrapper
from cwx.widgets.base_widget import Widget, MaskState


class SliderStyle(WidgetStyle):
    bar_fg: wx.Colour
    bar_bg: wx.Colour
    bar_height: float
    handle_size: float
    handle_fg: wx.Colour
    handle_bg: wx.Colour

    def __init__(self, bar_fg: wx.Colour, bar_bg: wx.Colour,
                 handle_size: float, handle_fg: wx.Colour, handle_bg: wx.Colour,
                 bar_height: float):
        super().__init__(bar_fg, bar_bg)
        self.bar_fg = bar_fg
        self.bar_bg = bar_bg
        self.handle_size = handle_size
        self.handle_fg = handle_fg
        self.handle_bg = handle_bg
        self.bar_height = bar_height

    @staticmethod
    def load(style: Style) -> 'SliderStyle':
        return SliderStyle(
            bar_fg=style.colors.accent_fill.default,
            bar_bg=style.colors.neutral_strong.default,
            handle_size=20,
            handle_fg=style.colors.accent_fill.default,
            handle_bg=style.colors.control_solid.default,
            bar_height=4
        )


Style.register_style_cls(SliderStyle)


class Slider(Widget, AnimationWrapper):
    style: SliderStyle
    handle_scale_anim: EZKeyFrameAnimation

    def __init__(self, parent: wx.Window):
        super().__init__(parent)
        AnimationWrapper.__init__(self)

        self.percent: float = 0.5
        self.handle_scale: float = 0.5
        self.normal_scale: float = 0.5
        self.float_scale: float = 0.7
        self.click_scale: float = 0.35
        self.mask_state = MaskState.NONE
        self.drag_start_percent = 0
        self.drag_start_x = 0

        self.handle_scale_anim = self.reg_animation(
            "handle_scale", EZKeyFrameAnimation(0.15, KeyFrameCurves.QUADRATIC_EASE, 0.5, 0.5))
        self.handle_value("handle_scale", "handle_scale")

        self.update_size()

        self.Bind(wx.EVT_MOUSE_EVENTS, self.on_mouse_events)

    def on_mouse_events(self, event: wx.MouseEvent):
        def update_handle_pos():
            x, y, w, h = self.get_bar_box()
            self.percent = max(0.0, min(1.0, self.drag_start_percent + (event.GetX() / SCALE - self.drag_start_x) / w))
            self.Refresh()

        event.Skip()
        last_mask_state = self.mask_state
        in_box = wx.Rect2D(*(map(lambda t: t * SCALE, self.get_handle_box()))).Contains(wx.Point2D(event.GetPosition()))
        if event.ButtonDown() and in_box:
            self.mask_state = MaskState.PRESSED
            self.drag_start_percent = self.percent
            self.drag_start_x = event.GetX() / SCALE
            self.CaptureMouse()
            update_handle_pos()
        elif (event.Moving() or event.Dragging()) and event.LeftIsDown():
            self.mask_state = MaskState.PRESSED
            update_handle_pos()
        elif event.ButtonUp():
            if in_box:
                self.mask_state = MaskState.HOVER
            else:
                self.mask_state = MaskState.NONE
            self.ReleaseMouse()
            update_handle_pos()
        elif event.Leaving():
            self.mask_state = MaskState.NONE
        elif in_box:
            self.mask_state = MaskState.HOVER
        else:
            self.mask_state = MaskState.NONE

        if self.mask_state != last_mask_state:
            if self.mask_state == MaskState.HOVER:
                self.handle_scale_anim.set_range(self.handle_scale_anim.value, self.float_scale)
            elif self.mask_state == MaskState.PRESSED:
                self.handle_scale_anim.set_range(self.handle_scale_anim.value, self.click_scale)
            elif self.mask_state == MaskState.NONE:
                self.handle_scale_anim.set_range(self.handle_scale_anim.value, self.normal_scale)
            self.play_animation("handle_scale")
            self.Refresh()

    def animation_callback(self):
        self.Refresh()

    def update_size(self):
        size = (100, int(max(self.style.bar_height, self.style.handle_size)))
        self.CacheBestSize(size)
        self.SetMinSize(size)

    def draw_content(self, gc: CustomGraphicsContext):
        with gc.State:
            gc.SetTransform(gc.CreateMatrix(a=SCALE, d=SCALE))
            self.draw_bar(gc)
            self.draw_handle(gc)

    def get_bar_box(self) -> tuple[float, float, float, float]:
        w, h = self.GetTupClientSize()
        w /= SCALE
        h /= SCALE
        return 0, (h - self.style.bar_height) / 2, w, self.style.bar_height

    @staticmethod
    def translate_style(style: Style):
        return style.as_type(SliderStyle)

    def draw_bar(self, gc: CustomGraphicsContext):
        """绘制背景条"""
        x, y, w, h = self.get_bar_box()
        r = self.style.handle_size / 2
        x_offset = max(r * 2, (w - self.style.handle_size) * self.percent + r)
        gc.SetPen(gc.CreatePen(wx.GraphicsPenInfo(TRANSPARENT_COLOR, width=0)))
        gc.SetBrush(wx.Brush(self.style.bar_bg))
        gc.DrawInnerRoundedRect(x + r, y, w - r * 2, self.style.bar_height, self.style.bar_height / 2, 0)
        gc.SetBrush(wx.Brush(self.style.bar_fg))
        gc.DrawInnerRoundedRect(x + r, y, x_offset - r * 2, self.style.bar_height, self.style.bar_height / 2, 0)

    def get_handle_box(self) -> tuple[float, float, float, float]:
        x, y, w, h = self.get_bar_box()
        r = self.style.handle_size / 2
        x_offset = (w - self.style.handle_size) * self.percent + r
        return x + x_offset - r, y, self.style.handle_size, self.style.handle_size

    def draw_handle(self, gc: CustomGraphicsContext):
        x, y, w, h = self.get_bar_box()
        with gc.State:
            r = self.style.handle_size / 2
            x_offset = (w - self.style.handle_size) * self.percent + r
            gc.Translate(x + x_offset, y + self.style.bar_height / 2)  # 定位滑杆中心
            gc.EmptyPen()
            # gc.DrawInnerRoundedRect()
            # 绘制大圆
            gc.SetBrush(gc.CreateBrush(wx.Brush(self.style.handle_bg)))
            gc.DrawCircle(0, 0, r)
            # 绘制小圆
            gc.SetBrush(gc.CreateBrush(wx.Brush(self.style.handle_fg)))
            gc.DrawCircle(0, 0, r * self.handle_scale)
