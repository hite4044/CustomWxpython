import wx

from .lib.dwm import *


def blur_window(window: wx.TopLevelWindow, enable: bool = True,
                color: tuple[int, int, int, int] | None = (0, 173, 226, 40),
                accent_state: int = ACCENT_STATE.ACCENT_ENABLE_ACRYLICBLURBEHIND):
    if color is None:
        color = (0, 0, 0, 0)  # 完全透明色
    hwnd = window.GetHandle()

    # 模糊透明效果
    bb = DWM_BLURBEHIND(
        dwFlags=DWM_BB_ENABLE,
        fEnable=enable,
        hRgnBlur=0,
        fTransitionOnMaximized=True,
    )
    DwmEnableBlurBehindWindow(hwnd, ctypes.byref(bb))

    # 设置合成效果
    accent = ACCENT_POLICY(AccentState=accent_state if enable else ACCENT_STATE.ACCENT_DISABLED,
                           GradientColor=(color[3] << 24) | (color[2] << 16) | (color[1] << 8) | color[0])
    attrib = WINDOW_COMPOSITION_ATTRIB_DATA(
        Attrib=WINDOW_COMPOSITION_ATTRIB.WCA_ACCENT_POLICY,
        pvData=ctypes.byref(accent),
        cbData=ctypes.sizeof(accent),
    )
    SetWindowCompositionAttribute(hwnd, ctypes.byref(attrib))

    # 拓展标题栏效果至客户区/标题栏
    margins = MARGINS(-1, -1, -1, -1) if enable else MARGINS(0, 0, 0, 0)
    DwmExtendFrameIntoClientArea(hwnd, ctypes.byref(margins))
