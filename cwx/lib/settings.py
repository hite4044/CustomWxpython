from ..style.frame.struct import BackdropType, AccentState, FrameTheme


class GlobalSettings:
    """CustomWxpython的全局设置"""
    default_caption_theme: FrameTheme = FrameTheme.AUTO
    default_frame_accent: AccentState = AccentState.DONT_SET
    default_backdrop_type: BackdropType = BackdropType.DONT_SET
