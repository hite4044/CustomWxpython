from enum import Enum

import wx

from .animation_widget import AnimationWidget
from ..animation import KeyFrameCurves, MAKE_ANIMATION
from ..dpi import SCALE
from ..event import SimpleCommandEvent
from ..lib.flag_parser import parse_flag
from ..render import CustomGraphicsContext, DrawLinesAE
from ..style import WidgetStyle, CheckBoxStyle, Style

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


class CheckBox(AnimationWidget):
    WND_NAME = "check"
    style: CheckBoxStyle
    check_sym_am: DrawLinesAE

    LABEL_PAD = 5 * SCALE

    class MaskState(Enum):
        NONE = 0  # 无
        BELOW = 1  # 鼠标悬浮在控件上面
        DOWN = 2  # 鼠标按下

    def __init__(self, parent: wx.Window, label: str = "", style=0, widget_style: WidgetStyle = None):
        super().__init__(parent, style, widget_style, fps=60)

        self.current_state: wx.CheckBoxState = \
            parse_flag(style, wx.CHK_CHECKED, wx.CHK_UNDETERMINED, default=wx.CHK_UNCHECKED)
        self.state_type: int = parse_flag(style, wx.CHK_3STATE, default=wx.CHK_2STATE)
        self.allow_3_state_for_user: bool = bool(style & wx.CHK_ALLOW_3RD_STATE_FOR_USER)
        self.align_right: bool = bool(style & wx.ALIGN_RIGHT)

        self.mask_state: CheckBox.MaskState = CheckBox.MaskState.NONE  # 指示是否绘制点击图层
        self.check_sym_am = self.reg_anim_element("check", DrawLinesAE(MAKE_ANIMATION(0.2, KeyFrameCurves.SMOOTH), []))

        self.text_extent: tuple[float, float] = (1.0, 1.0)

        self.SetLabel(label)
        self.Bind(wx.EVT_MOUSE_EVENTS, self.on_mouse_events)
        if self.current_state == wx.CHK_CHECKED:
            self.stop_animation("check")

    def animation_callback(self):
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
            self.send_event()
            self.Refresh()

        elif event.Moving() or event.Dragging() or event.IsButton():  # 处理遮罩状态更改
            last_state = self.mask_state
            if in_box:
                if event.LeftIsDown():
                    self.mask_state = CheckBox.MaskState.DOWN
                else:
                    self.mask_state = CheckBox.MaskState.BELOW
            else:
                self.mask_state = CheckBox.MaskState.NONE
            if self.mask_state != last_state:
                self.Refresh()

    def send_event(self):
        event = CheckBoxEvent(self, self.current_state == wx.CHK_CHECKED, self.current_state)
        self.ProcessEvent(event)

    def SetLabel(self, label: str):
        super().SetLabel(label)
        gc = CustomGraphicsContext(wx.GraphicsContext.Create(self))
        gc.SetFont(gc.CreateFont(self.GetFont(), self.style.fg))
        self.refresh_extent(gc)

    def refresh_extent(self, gc: CustomGraphicsContext):
        self.text_extent = gc.GetFullTextExtent(self.GetLabel())

    def get_box_info(self) -> tuple[tuple[float, float], tuple[float, float]]:
        """获取勾选框位置"""
        w, h = self.GetTupClientSize()
        box_size = (self.style.box_size * SCALE,) * 2
        delta = self.text_extent[0] if self.align_right else -self.text_extent[0]
        box_pos = (w - box_size[0] + delta) / 2, (h - box_size[1]) / 2
        return box_pos, box_size

    def draw_content(self, gc: CustomGraphicsContext):
        # 绘制勾选框
        box_pos, box_size = self.get_box_info()
        radius = self.style.box_corner_radius * SCALE
        with gc.State:
            gc.Translate(*box_pos)
            if self.current_state in [wx.CHK_CHECKED, wx.CHK_UNDETERMINED]:  # 绘制选中或者半选中
                # 绘制背景
                self.style.box_active_bg.reset()
                if self.mask_state == CheckBox.MaskState.DOWN:
                    self.style.box_active_bg.dark2() if self.gen_style.is_dark else self.style.box_active_bg.light2()
                elif self.mask_state == CheckBox.MaskState.BELOW:
                    self.style.box_active_bg.dark1() if self.gen_style.is_dark else self.style.box_active_bg.light1()
                gc.SetBrush(self.style.box_active_bg.create_brush(gc, box_size))
                gc.DrawRoundedRectangle(0, 0, *box_size, radius)

                # 绘制勾选符号
                gc.SetPen(self.style.box_sym.create_pen(gc, box_size))
                if self.current_state == wx.CHK_CHECKED:
                    x, y = 0.22, 0.25
                    PTS = [(0.08 + x, 0.28 + y), (0.24 + x, 0.4 + y),
                           (0.52 + x, 0.08 + y)]  # 200%缩放下 - [(2, 7), (6, 10), (13, 2)]
                elif self.current_state == wx.CHK_UNDETERMINED:
                    PTS = [(0.3, 0.52), (0.7, 0.52)]
                point2Ds = [wx.Point2D(point[0] * box_size[0], point[1] * box_size[1]) for point in PTS]
                self.check_sym_am.point2Ds = point2Ds
                gc.DrawAnimationElement(self.check_sym_am)

            elif self.current_state == wx.CHK_UNCHECKED:  # 绘制未选中
                if self.mask_state == CheckBox.MaskState.BELOW:
                    gc.SetBrush(self.style.box_hover_bg.create_brush(gc, box_size))
                else:
                    gc.SetBrush(gc.TRANSPARENT_BRUSH)
                gc.SetPen(self.style.box_border.create_pen(gc, box_size))
                gc.DrawInnerRoundedRect(0, 0, *box_size, radius, self.style.box_border.width)
            else:
                raise NotImplementedError("不要自己偷偷改current_state啊...怎么渲染我都不知道了")

        # 绘制文字
        gc.SetFont(gc.CreateFont(self.GetFont(), self.style.fg))
        self.refresh_extent(gc)
        w, h = self.GetTupClientSize()
        delta = -box_size[0] * 2 if self.align_right else box_size[0]
        gc.DrawText(self.GetLabel(),
                    (w - self.text_extent[0] + delta) / 2 + self.LABEL_PAD,
                    (h - self.text_extent[1]) / 2)

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
