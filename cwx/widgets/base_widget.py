import wx

from ..dpi import translate_size
from ..event import PyCommandEvent
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


class Widget(wx.Window):
    """
    CustomWxpython的基础控件类, 具有自动DPI缩放、主题管理
    CustomWxpython's base widget class, with auto dpi scale, theme manage.
    """
    gen_style: Style  # 主题
    style: WidgetStyle  # 组件自有样式

    def __init__(self, parent: wx.Window, style=0, widget_style: WidgetStyle = None):
        super().__init__(parent, style=style)
        self.Bind(wx.EVT_PAINT, self.on_paint)
        super().SetBackgroundColour(wx.BLACK)
        self.SetDoubleBuffered(True)

        if isinstance(parent, Widget):
            self.gen_style = parent.gen_style
        else:
            self.gen_style = Style()
        if widget_style:
            self.style = widget_style
        else:
            self.style = WidgetStyle.load(self.gen_style)
        setattr(self, "init_style", True)
        self.load_style(self.gen_style)
        delattr(self, "init_style")
        self.Bind(wx.EVT_SIZE, self.on_size)

    def on_size(self, event: wx.SizeEvent):
        event.Skip()
        self.Refresh()

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
            if hasattr(child, "update_style") and hasattr(child.update_style, "__call__"):
                child.update_style(event.gen_style)

    def load_widget_style(self, style: WidgetStyle):
        """
        加载组件样式, 在这实现组件样式加载
        Load widget style, implemented widget style load here.
        """
        self.style = style

    def on_paint(self, _):
        dc = wx.PaintDC(self)

        # timer = Counter(create_start=True)
        gc = CustomGraphicsContext(wx.GraphicsContext.Create(dc))
        self.draw_content(gc)
        # print(f"{self.__class__.__name__}: {timer.endT()}")

    def draw_content(self, gc: CustomGraphicsContext):
        pass
