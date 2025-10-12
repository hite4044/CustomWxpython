import ctypes

DWM_BB_ENABLE = 0x00000001  # 已指定 fEnable 成员的值
# noinspection SpellCheckingInspection
DWM_BB_BLURREGION = 0x00000002  # 已指定 hRgnBlur 成员的值
# noinspection SpellCheckingInspection
DWM_BB_TRANSITIONONMAXIMIZED = 0x00000004  # 已指定 fTransitionOnMaximized 成员的值


# noinspection PyPep8Naming,SpellCheckingInspection
class DWM_WINDOW_CORNER_PREFERENCE:
    DWMWCP_DEFAULT = 0
    DWMWCP_DONOTROUND = 1
    DWMWCP_ROUND = 2
    DWMWCP_ROUNDSMALL = 3


# noinspection PyPep8Naming,SpellCheckingInspection
class DWM_SYSTEMBACKDROP_TYPE:
    DWMSBT_AUTO = 0
    DWMSBT_NONE = 1
    DWMSBT_MAINWINDOW = 2
    DWMSBT_TRANSIENTWINDOW = 3
    DWMSBT_TABBEDWINDOW = 4


# noinspection PyPep8Naming,SpellCheckingInspection
class DWMWINDOWATTRIBUTE:
    DWMWA_USE_IMMERSIVE_DARK_MODE = 20
    DWMWA_WINDOW_CORNER_PREFERENCE = 33
    DWMWA_CAPTION_COLOR = 35
    DWMWA_SYSTEMBACKDROP_TYPE = 38


# noinspection PyPep8Naming,SpellCheckingInspection
class ACCENT_STATE:
    ACCENT_DISABLED = 0  # 禁用
    ACCENT_ENABLE_GRADIENT = 1  # 纯色背景
    ACCENT_ENABLE_TRANSPARENTGRADIENT = 2  # 带颜色透明
    ACCENT_ENABLE_BLURBEHIND = 3  # 模糊
    ACCENT_ENABLE_ACRYLICBLURBEHIND = 4  # 带颜色模糊
    ACCENT_ENABLE_HOSTBACKDROP = 5  # 透明
    ACCENT_INVALID_STATE = 6


# noinspection PyPep8Naming,SpellCheckingInspection
class WINDOW_COMPOSITION_ATTRIB:
    WCA_ACCENT_POLICY = 19


# noinspection PyPep8Naming
class MARGINS(ctypes.Structure):
    def __init__(self, cxLeftWidth: int, cxRightWidth: int, cyTopHeight: int, cyBottomHeight: int):
        super().__init__(cxLeftWidth, cxRightWidth, cyTopHeight, cyBottomHeight)

    _fields_ = [
        ("cxLeftWidth", ctypes.c_int),
        ("cxRightWidth", ctypes.c_int),
        ("cyTopHeight", ctypes.c_int),
        ("cyBottomHeight", ctypes.c_int),
    ]


# noinspection PyPep8Naming,SpellCheckingInspection
class DWM_BLURBEHIND(ctypes.Structure):
    def __init__(self, dwFlags: int, fEnable: bool, hRgnBlur: int, fTransitionOnMaximized: bool):
        super().__init__(dwFlags, fEnable, hRgnBlur, fTransitionOnMaximized)

    _fields_ = [
        ("dwFlags", ctypes.c_int),
        ("fEnable", ctypes.c_bool),
        ("hRgnBlur", ctypes.c_void_p),
        ("fTransitionOnMaximized", ctypes.c_bool),
    ]


# noinspection PyPep8Naming,SpellCheckingInspection
class WINDOW_COMPOSITION_ATTRIB_DATA(ctypes.Structure):
    def __init__(self, Attrib: int, pvData, cbData: int):
        super().__init__(Attrib, ctypes.cast(pvData, ctypes.c_void_p), cbData)

    _fields_ = [
        ("Attrib", ctypes.c_int),
        ("pvData", ctypes.c_void_p),
        ("cbData", ctypes.c_uint),
    ]


# noinspection PyPep8Naming,SpellCheckingInspection
class ACCENT_POLICY(ctypes.Structure):
    def __init__(self, AccentState: int, AccentFlags: int = 0, GradientColor: int = 0, AnimationId: int = 0):
        super().__init__(AccentState, AccentFlags, GradientColor, AnimationId)

    _fields_ = [
        ("AccentState", ctypes.c_int),
        ("AccentFlags", ctypes.c_uint),
        ("GradientColor", ctypes.c_uint),
        ("AnimationId", ctypes.c_uint),
    ]


## Function Define ##
dwmapi = ctypes.WinDLL("dwmapi")
user32 = ctypes.WinDLL("user32")


def RAISE_FAILED(func, *args):
    ret = func(*args)
    if ret != 0:
        raise ctypes.WinError()
    return 0

def DwmSetWindowAttribute(hwnd: int, dw_attr: int, obj):
    return RAISE_FAILED(dwmapi.DwmSetWindowAttribute, hwnd, dw_attr, ctypes.byref(obj), ctypes.sizeof(obj))


def DwmExtendFrameIntoClientArea(hwnd: int, enable: bool):
    if enable:
        margins = MARGINS(-1, -1, -1, -1)
    else:
        margins = MARGINS(0, 0, 0, 0)
    return RAISE_FAILED(dwmapi.DwmExtendFrameIntoClientArea, hwnd, ctypes.byref(margins))


def DwmEnableBlurBehindWindow(hwnd: int, bb: DWM_BLURBEHIND):
    return RAISE_FAILED(dwmapi.DwmEnableBlurBehindWindow, hwnd, ctypes.byref(bb))


def SetWindowCompositionAttribute(hwnd: int, attr: WINDOW_COMPOSITION_ATTRIB_DATA) -> bool:
    return user32.SetWindowCompositionAttribute(hwnd, ctypes.byref(attr))
