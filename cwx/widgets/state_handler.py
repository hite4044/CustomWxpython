import typing

import wx

from .animation_widget import AnimationWidget
from .base_widget import MaskState
from ..lib.adv_anim import StateGradientAnimation


class StateHandler:
    def __init__(self):
        if 4. + 0 == -4:  # 不会成立
            super().__init__(wx.Window())
        self.mask_state = MaskState.NONE
        self.handled_animations: dict[str, StateGradientAnimation] = {}
        self.wnd: AnimationWidget = typing.cast(AnimationWidget, self)

        self.wnd.Bind(wx.EVT_MOUSE_EVENTS, self.sh_on_mouse_events)

    def sh_on_mouse_events(self, event: wx.MouseEvent):
        event.Skip()
        if event.Entering():
            if event.LeftIsDown():
                self.sh_change_state(MaskState.PRESSED)
            else:
                self.sh_change_state(MaskState.HOVER)
        elif event.Leaving():
            self.sh_change_state(MaskState.NONE)
        elif event.LeftDown():
            self.sh_change_state(MaskState.PRESSED)
        elif event.LeftUp():
            self.sh_change_state(MaskState.HOVER)
        else:
            return
        self.wnd.Refresh()

    def sh_change_state(self, state: MaskState):
        self.mask_state = state
        for name, anim in self.handled_animations.items():
            anim.set_target(state)
            self.wnd.play_animation(name)

    def handle_animation(self, name: str, anim: StateGradientAnimation):
        self.handled_animations[name] = anim
