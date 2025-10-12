from ..style.frame.struct import BackdropType, AccentState, CaptionTheme


class GlobalSettings:
    """CustomWxpython的全局设置"""
    default_caption_theme: CaptionTheme = CaptionTheme.AUTO
    default_frame_accent: AccentState = AccentState.DISABLE
    default_backdrop_type: BackdropType = BackdropType.NONE
