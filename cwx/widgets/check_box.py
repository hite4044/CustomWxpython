import wx

from .animation_widget import AnimationWrapper
from .base_widget import MaskState, Widget
from ..animation import KeyFrameCurves, MAKE_ANIMATION, ColorGradientAnimation
from ..animation.adv_anim import StateGradientAnimation
from ..animation.state_color_wrap import StateAnimManager
from ..dpi import SCALE
from ..event import SimpleCommandEvent
from ..lib.animation_elements import DrawLinesAE
from ..lib.flag_parser import parse_flag
from ..render import CustomGraphicsContext
from ..style import WidgetStyle, Style, Background, Foreground
from ..style.color import GradientBrush, GradientPen

cwxEVT_CHECKBOX = wx.NewEventType()
EVT_CHECKBOX = wx.PyEventBinder(cwxEVT_CHECKBOX, 1)


class CheckBoxEvent(SimpleCommandEvent):
    eventType = cwxEVT_CHECKBOX

    def __init__(self, window: wx.Window, checked: bool, state: int):
        super().__init__(window)
        self.checked = checked
        self.state = state

    def IsChecked(self):
        return self.checked

    def Get3State(self):
        return self.state


class CheckBoxStyle(WidgetStyle):
    def __init__(self,
                 fg: wx.Colour,
                 sym_fg: GradientPen, box_bg: Background, active_bg: Background, border: Background,
                 box_corner_radius: float, box_size: float):
        """
        Args:
            fg: label's color.
        """
        super().__init__(fg)
        self.sym_pen: GradientPen = sym_fg
        self.box_bg: Background = box_bg
        self.active_bg: Background = active_bg
        self.border: Background = border
        self.box_corner_radius: float = box_corner_radius
        self.box_size: float = box_size

    @classmethod
    def load(cls, style: Style) -> 'CheckBoxStyle':
        return cls(
            Foreground.from_colors(style.colors.text),
            GradientPen(GradientBrush(wx.BLACK if style.is_dark else wx.WHITE), width=2),
            Background.from_colors(style.colors.control_fill),
            Background.from_colors(style.colors.accent_fill),
            Background.from_colors(style.colors.control_strong_stroke),
            3,
            20
        )


Style.register_style_cls(CheckBoxStyle)


class CheckBox(Widget, AnimationWrapper, StateAnimManager):
    WND_NAME = "check"
    style: CheckBoxStyle
    check_sym_am: DrawLinesAE
    box_anim: StateGradientAnimation
    box_bg_anim: ColorGradientAnimation

    PAD = 5 * SCALE

    def __init__(self, parent: wx.Window, label: str = "", style=0, widget_style: WidgetStyle = None):
        super().__init__(parent, style, widget_style)
        AnimationWrapper.__init__(self)
        StateAnimManager.__init__(self)

        self.current_state: wx.CheckBoxState = \
            parse_flag(style, wx.CHK_CHECKED, wx.CHK_UNDETERMINED, default=wx.CHK_UNCHECKED)
        self.state_type: int = parse_flag(style, wx.CHK_3STATE, default=wx.CHK_2STATE)
        self.allow_3_state_for_user: bool = bool(style & wx.CHK_ALLOW_3RD_STATE_FOR_USER)
        self.align_right: bool = bool(style & wx.ALIGN_RIGHT)

        self.mask_state: MaskState = MaskState.NONE  # 指示是否绘制点击图层
        self.check_sym_am = self.reg_anim_element("check", DrawLinesAE(MAKE_ANIMATION(0.2, KeyFrameCurves.SMOOTH), []))
        self.box_anim = StateGradientAnimation(0.1, self.style.box_bg)
        self.box_active_anim = StateGradientAnimation(0.1, self.style.active_bg)
        self.crt_normal_bg = wx.Colour(self.box_anim.value)
        self.crt_active_bg = wx.Colour(self.box_active_anim.value)
        self.reg_state_animation("normal_box_bg", "crt_normal_bg", self.box_anim)
        self.reg_state_animation("active_box_bg", "crt_active_bg", self.box_active_anim)
        self.box_bg_anim = ColorGradientAnimation(0.15, self.crt_normal_bg, self.crt_active_bg)
        self.reg_animation("box_bg", self.box_bg_anim)
        self.border_anim = StateGradientAnimation(0.1, self.style.border)
        self.crt_border = wx.Colour(self.border_anim.value)
        self.reg_state_animation("border", "crt_border", self.border_anim)

        self.text_extent: tuple[float, float, float, float] = (1.0, 1.0, 0.0, 0.0)

        self.SetLabel(label)
        self.Bind(wx.EVT_MOUSE_EVENTS, self.on_mouse_events)
        if self.current_state == wx.CHK_CHECKED:
            self.stop_animation("check")

    def animation_callback(self):
        self.own_animation_callback()
        self.Refresh()

    def on_mouse_events(self, event: wx.MouseEvent):
        event.Skip()
        box_pos, box_size = self.get_box_info()
        in_box = wx.Rect2D(*box_pos, *box_size).Contains(wx.Point2D(event.GetPosition()))

        if event.IsButton() and event.LeftUp() and in_box:  # 处理点击事件
            three_state = self.state_type == wx.CHK_3STATE and self.allow_3_state_for_user
            if self.current_state == wx.CHK_UNCHECKED:
                self.play_animation("check")
                self.current_state = wx.CHK_CHECKED
            elif self.current_state == wx.CHK_CHECKED:
                if three_state:
                    self.current_state = wx.CHK_UNDETERMINED
                else:
                    self.current_state = wx.CHK_UNCHECKED
            elif wx.CHK_UNDETERMINED:
                self.current_state = wx.CHK_UNCHECKED
            self.on_change_state()
            self.Refresh()

        elif event.Moving() or event.Dragging() or event.IsButton():  # 处理遮罩状态更改
            last_state = self.mask_state
            if in_box:
                if event.LeftIsDown():
                    self.mask_state = MaskState.PRESSED
                else:
                    self.mask_state = MaskState.HOVER
            else:
                self.mask_state = MaskState.NONE
            if self.mask_state != last_state:
                self.Refresh()

    def on_change_state(self):
        event = CheckBoxEvent(self, self.current_state == wx.CHK_CHECKED, self.current_state)
        self.ProcessEvent(event)
        if self.current_state == wx.CHK_CHECKED:
            self.box_bg_anim.set_invent(False)
        elif self.current_state == wx.CHK_UNCHECKED:
            self.box_bg_anim.set_invent(True)
        self.box_bg_anim.set_color(self.box_anim.value, self.box_active_anim.value)
        self.play_animation("box_bg")

    def SetLabel(self, label: str):
        super().SetLabel(label)
        gc = CustomGraphicsContext(wx.GraphicsContext.Create(self))
        gc.SetFont(self.GetFont(), self.style.fg)
        self.refresh_extent(gc)
        self.refresh_size()

    def refresh_extent(self, gc: CustomGraphicsContext):
        self.text_extent = gc.GetFullTextExtent(self.GetLabel())

    def refresh_size(self):
        h = self.style.box_size * SCALE + self.PAD * 2
        size = (int(h + self.text_extent[0]) + 100, int(h))
        self.RawSetMinSize(size)
        self.RawCacheBestSize(size)

    def get_box_info(self) -> tuple[tuple[float, float], tuple[float, float]]:
        """获取勾选框位置"""
        w, h = self.GetTupClientSize()
        box_size = (self.style.box_size * SCALE,) * 2
        if not self.align_right:  # left
            box_pos = (self.PAD, (h - box_size[1]) / 2)
        else:  # right
            box_pos = (w - self.PAD - box_size[0], (h - box_size[1]) / 2)
        return box_pos, box_size

    def draw_content(self, gc: CustomGraphicsContext):
        # 绘制勾选框
        box_pos, box_size = self.get_box_info()
        radius = self.style.box_corner_radius * SCALE
        with gc.State:
            gc.Translate(*box_pos)
            # 绘制背景
            if self.box_bg_anim.is_playing:
                box_bg_color = self.box_bg_anim.value
            else:
                box_bg_color = self.crt_normal_bg if self.current_state == wx.CHK_UNCHECKED else self.crt_active_bg
            gc.SetBrush(wx.Brush(box_bg_color))
            if self.current_state in [wx.CHK_CHECKED, wx.CHK_UNDETERMINED]:
                gc.SetPen(gc.CreatePen(wx.GraphicsPenInfo(box_bg_color, width=0)))
            else:
                gc.SetPen(gc.CreatePen(wx.GraphicsPenInfo(self.crt_border, width=round(SCALE))))
            gc.DrawRoundedRectangle(0, 0, *box_size, radius)

            if self.current_state in [wx.CHK_CHECKED, wx.CHK_UNDETERMINED]:  # 绘制选中或者半选中
                # 绘制勾选符号
                gc.SetPen(self.style.sym_pen.create_pen(gc, box_size))
                if self.current_state == wx.CHK_CHECKED:
                    x, y = 0.22, 0.3
                    PTS = [(0.08 + x, 0.28 + y), (0.24 + x, 0.4 + y),
                           (0.52 + x, 0.08 + y)]  # 200%缩放下 - [(2, 7), (6, 10), (13, 2)]
                elif self.current_state == wx.CHK_UNDETERMINED:
                    PTS = [(0.3, 0.52), (0.7, 0.52)]
                point2Ds = [wx.Point2D(point[0] * box_size[0], point[1] * box_size[1]) for point in PTS]
                self.check_sym_am.point2Ds = point2Ds
                gc.DrawAnimationElement(self.check_sym_am)

        # 绘制文字
        gc.SetFont(self.GetFont(), self.style.fg)
        w, h = self.GetTupClientSize()
        if not self.align_right:
            x = box_pos[0] * 2 + box_size[0]
            y = h / 2
            gc.DrawText(self.GetLabel(), x, y, center_align="left")
        else:
            x = box_pos[0] - self.PAD
            y = h / 2
            gc.DrawText(self.GetLabel(), x, y, center_align="right")

    @staticmethod
    def translate_style(style: Style) -> CheckBoxStyle:
        return CheckBoxStyle.load(style)

    # 一些无聊的设值函数

    def Check(self, check: bool):
        self.current_state = wx.CHK_CHECKED if check else wx.CHK_UNCHECKED
        self.Refresh()

    def IsChecked(self) -> bool:
        if self.current_state == wx.CHK_UNDETERMINED:
            return True
        return self.current_state == wx.CHK_CHECKED

    def Get3StateValue(self) -> wx.CheckBoxState:
        return self.current_state

    def Set3StateValue(self, value: wx.CheckBoxState):
        self.current_state = value
        self.Refresh()

    def Is3State(self) -> bool:
        return self.state_type == wx.CHK_3STATE

    def Is3rdStateAllowedForUser(self) -> bool:
        return self.allow_3_state_for_user
