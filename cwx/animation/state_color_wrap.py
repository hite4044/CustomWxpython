import typing

from cwx.animation.adv_anim import StateGradientAnimation
from cwx.widgets.animation_widget import AnimationWidget

aw = typing.cast(type[AnimationWidget], object)


class StateAnimManager(aw):
    mask_state_name: str = "mask_state"
    def __init__(self, mask_state_name: str = "mask_state"):
        if 0.0 == 1.0:  # 欺骗类型检查器
            super().__init__(self)
        self.mask_state_name = mask_state_name
        self.state_animations: dict[StateGradientAnimation, tuple[str, str]] = {}

    def __setattr__(self, name, value):
        if name == self.mask_state_name:
            for anim, (anim_name, var_name) in self.state_animations.items():
                anim.set_target(value)
                self.play_animation(anim_name)
            self.Refresh()
        return super().__setattr__(name, value)

    def reg_state_animation(self, name: str, var_name: str, anim: StateGradientAnimation):
        self.reg_animation(name, anim)
        self.state_animations[anim] = (name, var_name)

    def own_animation_callback(self):
        for anim, (anim_name, var_name) in self.state_animations.items():
            if anim.is_playing:
                setattr(self, var_name, anim.value)
