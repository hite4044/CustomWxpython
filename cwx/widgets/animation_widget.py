from typing import TypeVar

import wx

from ..animation import Animation, AnimationGroup
from ..style import WidgetStyle
from ..widgets.base_widget import Widget

cwxEVT_ANIMATION_OVER = wx.NewEventType()
EVT_ANIMATION_OVER = wx.PyEventBinder(cwxEVT_ANIMATION_OVER, 1)


class AnimationOverEvent(wx.PyCommandEvent):
    def __init__(self, animation: 'Animation'):
        wx.PyCommandEvent.__init__(self, cwxEVT_ANIMATION_OVER)
        self.animation = animation


class AnimationWidget(Widget):
    """
    具有自动动画管理的组件
    需要重写 `animation_callback` 方法, 该方法在每动画帧调用, 而且我们不会帮你自动刷新控件

    A widget with auto animation manage.
    How to implement:
    1. Rewrite method `animation_callback`, this method will call in each animation frame.
    """

    def __init__(self, parent: wx.Window, style=0, widget_style: WidgetStyle = None, fps: int = 60):
        super().__init__(parent, style, widget_style)
        self.fps = fps
        self.allow_multi_anim: bool = True
        self.animations: dict[str, Animation | AnimationGroup] = {}
        self.in_playing: list[Animation | AnimationGroup] = []

        self.timer = wx.Timer()
        self.timer.StartOnce(1000 // self.fps)
        self.timer.Stop()
        self.timer.Bind(wx.EVT_TIMER, self._animation_call)

    ANIM_T = TypeVar('ANIM_T')

    def reg_anim_element(self, name: str, animation_element: type[ANIM_T]) -> type[ANIM_T]:
        """
        注册一个动画元素
        """
        self.animations[name] = animation_element.anim
        return animation_element

    def reg_animation(self, name: str, animation: Animation):
        """
        注册一个动画
        Register an animation.
        """
        self.animations[name] = animation
        return animation

    def reg_animation_group(self, name: str, group: AnimationGroup):
        """
        注册一个动画组, 也可把组当作普通动画注册
        Register an animation group, same as `reg_animation`.
        """
        return self.reg_animation(name, group)

    def play_animation(self, name: str):
        """
        调整某个动画到开头, 并播放某个该动画
        Play an animation.
        """
        if name in self.animations:
            anim = self.animations[name]
        else:
            raise RuntimeError(f"PlayAnimationError, There is no animation (group) named: {name}")
        anim.play()
        if not self.allow_multi_anim and self.in_playing:
            for animation in self.in_playing:
                if animation is not anim:
                    animation.stop()
            self.in_playing.clear()
        self.in_playing.append(anim)

        if not self.timer.IsRunning():
            self.timer.StartOnce()

    def stop_animation(self, name: str | Animation | AnimationGroup):
        """
        停止某个动画, 并调整其到结尾
        Stop an animation.
        """
        if not isinstance(name, str):
            anim = name
        elif name in self.animations:
            anim = self.animations[name]
        else:
            raise RuntimeError(f"StopAnimationError, There is no animation (group) named: {name}")
        anim.stop()
        if anim in self.in_playing:
            self.in_playing.remove(anim)
        if not self.in_playing:
            self.timer.Stop()

    def _animation_call(self, _):
        """
        内部使用的函数, 请使用 `animation_callback`.
        A method for internal use, please using `animation_callback`
        """
        # timer = Counter(create_start=True)
        try:
            self.animation_callback()
        except RuntimeError:
            return
        for animation in self.in_playing[:]:
            if not animation.is_playing:
                animation.stop()
                self.in_playing.remove(animation)
        if self.in_playing:
            frame_time = 1 / self.fps
            for animation in self.in_playing:
                frame_time = min(frame_time, max(0, animation.get_next_frame_time(self.fps)))
            self.timer.StartOnce(int(frame_time * 1000))
        # print(f"Animation Frame Use: {timer.endT()}")

    def animation_callback(self):
        """
        动画回调函数, 你应该在这里处理组件数据更新逻辑, 我们不会帮你自动刷新控件
        Animation callback function, you should process widget update here.
        """
        pass
