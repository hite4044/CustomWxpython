from .struct import *
from ctypes import wintypes

from cwx.style.frame.dwm import *


def set_window_composition(hwnd: int, enable: bool = True,
                           color: tuple[int, int, int, int] | None = (0, 173, 226, 40),
                           accent_state: int = ACCENT_STATE.ACCENT_ENABLE_ACRYLICBLURBEHIND):
    """对一个窗口应用模糊效果, Win10+"""
    if color is None:
        color = (0, 0, 0, 0)  # 完全透明色

    # 模糊透明效果
    DwmEnableBlurBehindWindow(hwnd, DWM_BLURBEHIND(
        dwFlags=DWM_BB_ENABLE,
        fEnable=enable,
        hRgnBlur=0,
        fTransitionOnMaximized=True,
    ))

    # 设置合成效果
    accent = ACCENT_POLICY(AccentState=accent_state if enable else ACCENT_STATE.ACCENT_DISABLED,
                           GradientColor=(color[3] << 24) | (color[2] << 16) | (color[1] << 8) | color[0])
    attrib = WINDOW_COMPOSITION_ATTRIB_DATA(
        Attrib=WINDOW_COMPOSITION_ATTRIB.WCA_ACCENT_POLICY,
        pvData=ctypes.byref(accent),
        cbData=ctypes.sizeof(accent),
    )
    SetWindowCompositionAttribute(hwnd, attrib)

    # 拓展标题栏效果至客户区/标题栏
    margins = MARGINS(-1, -1, -1, -1) if enable else MARGINS(0, 0, 0, 0)
    DwmExtendFrameIntoClientArea(hwnd, margins)


def set_caption_color(hwnd: int, color: tuple[int, int, int] | None = None):
    if color is None:
        color = (0, 0, 0)  # 完全透明色

    color_ref = wintypes.RGB(*color)
    DwmSetWindowAttribute(hwnd, DWMWINDOWATTRIBUTE.DWMWA_CAPTION_COLOR, color_ref)

def set_frame_dark(hwnd: int, is_dark: bool = True):
    DwmSetWindowAttribute(hwnd, DWMWINDOWATTRIBUTE.DWMWA_USE_IMMERSIVE_DARK_MODE, ctypes.c_int(1 if is_dark else 0))


def set_window_backdrop(hwnd: int, backdrop_type: int):
    """设置窗口的背景"""
    DwmSetWindowAttribute(hwnd, DWMWINDOWATTRIBUTE.DWMWA_SYSTEMBACKDROP_TYPE, ctypes.c_int(backdrop_type))