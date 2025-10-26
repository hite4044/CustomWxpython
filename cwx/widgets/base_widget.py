import typing
from dataclasses import dataclass
from enum import Enum

import wx
from win32.lib.win32con import GWL_STYLE, WS_CLIPSIBLINGS
from win32gui import GetWindowLong, SetWindowLong

from ..dpi import translate_size, SCALE
from ..event import PyCommandEvent
from ..lib.perf import Counter
from ..render import CustomGraphicsContext
from ..style import Style, WidgetStyle

cwxEVT_STYLE_UPDATE = wx.NewEventType()
EVT_STYLE_UPDATE = wx.PyEventBinder(cwxEVT_STYLE_UPDATE, 1)


class StyleUpdateEvent(PyCommandEvent):
    def __init__(self, gen_style: Style):
        super().__init__(cwxEVT_STYLE_UPDATE, wx.ID_ANY)
        self.gen_style = gen_style


"""
实现Widget的主题
1. 重写translate_style方法, 负责将 主题(Style) 转换为 组件主题(WidgetStyle)
2. 继承load_widget_style方法, 加载 组件主题(WidgetStyle)
"""


class MaskState(Enum):
    NONE = 0  # 无
    BELOW = 1  # 鼠标悬浮在控件上面
    DOWN = 2  # 鼠标按下


class Widget(wx.Window):
    """
    CustomWxpython的基础控件类, 具有自动DPI缩放、主题管理
    CustomWxpython's base widget class, with auto dpi scale, theme manage.
    """
    gen_style: Style  # 主题
    style: WidgetStyle  # 组件自有样式
    initializing_style: bool = False  # 指示是否正在初始化组件样式

    init_wnd: bool = True  # 指示是否初始化wx.Window类
    enable_double_buffer: bool = True

    WND_NAME = "CWX_Widget"

    def __init__(self, parent: wx.Window, style=0, widget_style: WidgetStyle = None):
        if self.init_wnd:
            super().__init__(parent, style=style | wx.TRANSPARENT_WINDOW, name=self.WND_NAME)

            sty = GetWindowLong(self.GetHandle(), GWL_STYLE)
            sty |= WS_CLIPSIBLINGS
            SetWindowLong(self.GetHandle(), GWL_STYLE, sty)
        # 确保颜色可以被继承
        super().SetBackgroundColour(parent.GetBackgroundColour())
        self.SetDoubleBuffered(self.enable_double_buffer)

        if hasattr(parent, "gen_style"):
            self.gen_style = parent.gen_style
        else:
            self.gen_style = Style()
        if widget_style:
            self.style = widget_style
        else:
            self.style = WidgetStyle.load(self.gen_style)
        self.initializing_style = True
        self.load_style(self.gen_style)
        self.initializing_style = False
        self.Bind(wx.EVT_PAINT, self.on_paint)
        # if self.__class__.__name__ != "Frame":
        #     self.Bind(wx.EVT_ERASE_BACKGROUND, lambda _:None)
        self.py_font = parent.GetFont() if hasattr(parent, "GetFont") else None
        self.last_size = self.GetSize()

        TopWindowCanvas.auto_handling_window(self)

    def __hash__(self):
        return hash(self.GetHandle())

    def __eq__(self, other):
        return other is self

    def SetFont(self, font: wx.Font):
        if not hasattr(font, "CWX_RAW_SIZE"):
            font = wx.Font(font)
            font.CWX_RAW_SIZE = font.GetPointSize()
            font.SetPointSize(round(font.GetPointSize() * SCALE))
        super().SetFont(font)
        self.py_font = font

    def GetFont(self):
        return self.py_font if hasattr(self, "py_font") and self.py_font else super().GetFont()

    def Disable(self):
        self.Enable(False)

    def GetTupClientSize(self) -> tuple[int, int]:
        return tuple(typing.cast(tuple[int, int], super().GetClientSize().GetIM()))

    def SetId(self, winid) -> 'Widget':
        """此方法返回组件自身"""
        super().SetId(winid)
        return self

    # 一些关于大小设置的DPI替换
    # Some method hook about setting size.

    def SetSize(self, size: tuple[int, int]):
        super().SetSize(translate_size(size))

    def SetMinSize(self, size: tuple[int, int]):
        super().SetMinSize(translate_size(size))

    def SetMaxSize(self, size: tuple[int, int]):
        super().SetMaxSize(translate_size(size))

    def CacheBestSize(self, size: tuple[int, int]):
        super().CacheBestSize(translate_size(size))

    def RawSetSize(self, size: tuple[int, int]):
        super().SetSize(size)

    def RawSetMinSize(self, size: tuple[int, int]):
        super().SetMinSize(size)

    def RawSetMaxSize(self, size: tuple[int, int]):
        super().SetMaxSize(size)

    def RawCacheBestSize(self, size: tuple[int, int]):
        super().CacheBestSize(size)

    # 主题函数
    # Method about theme.
    def SetBackgroundColour(self, colour: wx.Colour):
        super().SetBackgroundColour(colour)
        self.style.bg.SetRGBA(colour.GetRGBA())

    def SetForegroundColour(self, colour: wx.Colour):
        super().SetForegroundColour(colour)
        self.style.fg.SetRGBA(colour.GetRGBA())

    def load_style(self, style: Style):
        """
        转换主题为组件样式并加载, 用`init_style`属性的存在来判断是否正在初始化组件
        Translate gen style into widget style and load it,
         when `init_style` property is existed, it means it's initialing the theme on create widget.
        """
        self.gen_style = style
        self.load_widget_style(self.translate_style(style))

        if self.initializing_style:
            return
        for child in self.GetChildren():
            if hasattr(child, "load_style") and hasattr(child.load_style, "__call__"):
                child.load_style(style)

    @staticmethod
    def translate_style(style: Style) -> WidgetStyle:
        """
        转换主题为组件样式
        Translate gen style to widget style.
        """
        return style.default_style

    def on_style_update(self, event: StyleUpdateEvent):
        """
        当组件接收到更新主题的信息时, 向该控件下所有支持update_style方法的子控件转发该消息
        """
        self.load_style(event.gen_style)
        for child in self.GetChildren():
            if hasattr(child, "load_style") and hasattr(child.load_style, "__call__"):
                child.load_style(event.gen_style)

    def load_widget_style(self, style: WidgetStyle):
        """
        加载组件样式, 在这实现组件样式加载
        Load widget style, implemented widget style load here.
        """
        self.style = style

    @property
    def is_dark(self) -> bool:
        """
        指示当前主题是否为暗色主题
        Indicate whether the current theme is dark.
        """
        return self.gen_style.is_dark()

    def on_paint(self, _):
        dc = wx.PaintDC(self)

        timer = Counter(create_start=True)
        gc = CustomGraphicsContext(wx.GraphicsContext.Create(dc))
        self.draw_content(gc)
        print(f"{self.__class__.__name__}: {timer.endT()}")

    def draw_content(self, gc: CustomGraphicsContext):
        pass


@dataclass
class CanvasCache:
    window: int  # 窗口的句柄
    parent_window: int = None  # 父窗口的句柄

    own_bitmap: wx.GraphicsBitmap | None = None  # 窗口自己的渲染图
    own_bitmap_size: tuple[int, int] | None = None  # 大小

    has_child: bool = False
    rendered_bitmap: wx.GraphicsBitmap | None = None  # 包含子窗口画面的渲染图
    rendered_bitmap_size: tuple[int, int] | None = None  # 大小


class TopWindowCanvas:
    """在一个顶层窗口的画布上绘制所有CWX控件的内容, 从而支持各控件重叠进行透明度渲染"""

    def __init__(self, canvas_host: wx.TopLevelWindow):
        canvas_host.CWX_canvas = self
        self.canvas_host = canvas_host

        self.handled_windows: dict[int, Widget] = {}
        self.render_cache: dict[int, CanvasCache] = {}  # 窗口句柄 -> 渲染缓存

        self.canvas_host.SetDoubleBuffered(True)
        self.canvas_host.Bind(wx.EVT_PAINT, self.on_paint, self.canvas_host)
        self.canvas_host.Bind(wx.EVT_ERASE_BACKGROUND, lambda e: None)

        self.pos_test_window = wx.Window(canvas_host, style=wx.TRANSPARENT_WINDOW)
        self.pos_test_window.SetBackgroundColour(wx.BLACK)
        self.pos_test_window.SetPosition((0, 0))
        self.pos_test_window.SetSize((1, 1))

        self.alpha_buffer = b"\x00" * 1024 * 1024
        self.buffer = None

    @staticmethod
    def auto_handling_window(window: Widget):
        parent = window.GetTopLevelParent()
        if hasattr(parent, "CWX_canvas"):
            instance: TopWindowCanvas = getattr(parent, "CWX_canvas")
            instance.handling_window(window)

    def handling_window(self, window: Widget):
        self.handled_windows[window.GetHandle()] = window
        window.Unbind(wx.EVT_PAINT)
        window.Bind(wx.EVT_ERASE_BACKGROUND, lambda e: None)

        window.Unbind(wx.EVT_SIZE)
        window.Bind(wx.EVT_SIZE, self.on_window_size, window)
        window.Refresh = lambda: self.refresh_window(window)

        window.SetDoubleBuffered(False)

    def on_host_size(self, event: wx.SizeEvent):
        event.Skip()
        self.canvas_host.Refresh()
        self.canvas_host.Layout()

    def on_window_size(self, event: wx.SizeEvent):
        event.Skip()
        window = event.GetEventObject()
        assert isinstance(window, Widget)
        # 如果大小对不上, 删除渲染缓存
        if cache := self.render_cache.get(window.GetHandle()):
            if cache.own_bitmap_size and cache.own_bitmap_size != event.GetSize().Get():
                self.remove_cache(window)
        self.canvas_host.Refresh()

    def refresh_window(self, window: Widget):
        self.remove_cache(window)
        self.canvas_host.Refresh()

    def remove_cache(self, window: Widget, include_own: bool = True):
        # print(window.__class__.__name__, "Remove cache")
        if window.GetHandle() not in self.render_cache:
            return
        cache = self.render_cache[window.GetHandle()]
        cache.rendered_bitmap = None
        cache.rendered_bitmap_size = None
        if include_own:
            cache.own_bitmap = None
            cache.own_bitmap_size = None

        if cache.parent_window:
            parent_window = self.handled_windows[cache.parent_window]
            self.remove_cache(parent_window, include_own=False)

    def on_paint(self, _):
        dc = wx.BufferedPaintDC(self.canvas_host)
        timer = Counter()

        gc = CustomGraphicsContext(wx.GraphicsContext.Create(dc))
        dc.Clear()
        for child in self.canvas_host.GetChildren():
            if isinstance(child, Widget):
                self.draw_wnd(gc, self.canvas_host, child)

    def draw_wnd(self, gc: CustomGraphicsContext, root_window: wx.Window, window: Widget):
        gc.GetWindow = lambda: root_window
        # 计算位置
        root_pos = self.pos_test_window.GetScreenPosition()
        wnd_pos, size = window.GetScreenPosition(), window.GetClientSize().Get()
        pos = (wnd_pos.x - root_pos.x, wnd_pos.y - root_pos.y)

        # 加载缓存
        if window.GetHandle() not in self.render_cache:
            parent_handle = None if window.GetParent() is root_window else window.GetParent().GetHandle()
            cache = CanvasCache(window.GetHandle(), parent_handle)
            self.render_cache[window.GetHandle()] = cache
        else:
            cache = self.render_cache[window.GetHandle()]

        # 根据完整渲染缓存绘制
        if cache.rendered_bitmap:
            gc.DrawBitmap(cache.rendered_bitmap, *pos, *cache.rendered_bitmap_size)
            return
        elif cache.own_bitmap and not cache.has_child:
            # print(window.__class__.__name__, "Cache Hit")
            gc.DrawBitmap(cache.own_bitmap, *pos, *cache.own_bitmap_size)
            return

        # 仅根据部分渲染缓存绘制
        if cache.own_bitmap:
            # print(window.__class__.__name__, "Cache Hit")
            gc.DrawBitmap(cache.own_bitmap, *pos, *cache.own_bitmap_size)
            image = cache.own_bitmap.ConvertToImage()
        else:  # 绘制内容到图片里
            # print("Redraw", window.__class__.__name__)
            image = wx.Image(*size, clear=True)
            image.SetAlphaBuffer(self.alpha_buffer)
            low_gc = wx.GraphicsContext.Create(image)
            low_gc.GetWindow = lambda: root_window
            wnd_gc = CustomGraphicsContext(low_gc)
            window.draw_content(wnd_gc)
            wnd_gc.Destroy()
            gc_bitmap = gc.CreateBitmapFromImage(image)
            gc.DrawBitmap(gc_bitmap, *pos, *size)
            cache.own_bitmap = gc_bitmap
            cache.own_bitmap_size = typing.cast(tuple[int, int], size)

        # 如果没有子窗口, 跳过子窗口绘制
        cache.has_child = bool(window.GetChildren())
        if not window.GetChildren():
            cache.rendered_bitmap = None
            cache.rendered_bitmap_size = None
            return

        # 在自身窗口内容上绘制子窗口内容
        # print(window.GetHandle(), "Cache Unhit - Child")
        wnd_gc = CustomGraphicsContext(wx.GraphicsContext.Create(image))
        for child in window.GetChildren():
            if isinstance(child, Widget):
                self.draw_wnd(wnd_gc, root_window, child)
        wnd_gc.Destroy()
        gc_bitmap = gc.CreateBitmapFromImage(image)
        gc.DrawBitmap(gc_bitmap, *pos, *size)

        cache.rendered_bitmap = gc_bitmap
        cache.rendered_bitmap_size = typing.cast(tuple[int, int], size)
