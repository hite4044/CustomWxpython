import wx

from cwx.render import CustomGraphicsContext
from cwx.style import WidgetStyle, Style
from cwx.style.color import TRANSPARENT_COLOR
from cwx.widgets.animation_widget import AnimationWrapper
from cwx.widgets.base_widget import Widget
from cwx.dpi import SCALE


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

    def __init__(self, parent: wx.Window):
        super().__init__(parent)

        self.percent: float = 0.5
        self.handle_scale: float = 0.5
        self.update_size()

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
        gc.SetPen(gc.CreatePen(wx.GraphicsPenInfo(TRANSPARENT_COLOR, width=0)))
        gc.SetBrush(wx.Brush(self.style.bar_bg))
        gc.DrawRoundedRectangle(x, y, w, self.style.bar_height, 2)
        gc.SetBrush(wx.Brush(self.style.bar_fg))
        gc.DrawRoundedRectangle(x, y, w * self.percent, self.style.bar_height, 2)

    def draw_handle(self, gc: CustomGraphicsContext):
        x, y, w, h = self.get_bar_box()
        with gc.State:
            x_offset = w * self.percent
            r = self.style.handle_size / 2
            gc.Translate(x + x_offset, y + self.style.bar_height / 2)  # 定位滑杆中心
            gc.EmptyPen()
            # 绘制大圆
            gc.SetBrush(gc.CreateBrush(wx.Brush(self.style.handle_bg)))
            gc.DrawCircle(0, 0, r)
            # 绘制小圆
            gc.SetBrush(gc.CreateBrush(wx.Brush(self.style.handle_fg)))
            gc.DrawCircle(0, 0, r * self.handle_scale)
