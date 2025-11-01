from ..animation import MultiColorGradientAnimation
from ..style import MixedStateColor, MaskState


class StateGradientAnimation(MultiColorGradientAnimation):
    def __init__(self, during: float, state_color: MixedStateColor):
        super().__init__(during, ("normal", state_color.normal),
                         ("hover", state_color.hover),
                         ("pressed", state_color.pressed),
                         ("disable", state_color.disabled))

    def set_target(self, state: MaskState, invent: bool = False):
        print(state)
        if state == MaskState.NONE:
            name = "normal"
        else:
            name = state.name.lower()
        super().set_target(name, invent)
