import ctypes
import math
import typing
from ctypes import wintypes
from dataclasses import dataclass
from enum import Enum
from io import BytesIO
from math import ceil
from typing import Union

import wx
from PIL import ImageFont, Image, ImageDraw, ImageEnhance
from win32.lib.win32con import GDI_ERROR
from win32gui import CreateCompatibleDC, SelectObject, DeleteDC

from cwx.dpi import SCALE
from cwx.render.constants import CenterAlign
from cwx.render.text import TextAttr, TextParagraph, AdvancedText, TextRender
from cwx.tool.image_pil2wx import PilImg2WxImg


@dataclass
class TextRenderCache:
    text: str  # 文字
    color: tuple[int, int, int, int]  # 颜色
    font: str  # 字体信息NativeFontInfoDesc
    pos_decimal: tuple[float, float]  # 文字位置的小数

    text_bitmap: wx.GraphicsBitmap = None  # 文字渲染结果
    size: tuple[int, int] = None  # 文字图片的大小
    offset_pos: tuple[int, int] = None

    def __hash__(self):
        return hash(hash(self.text) + hash(self.color) + hash(self.font) + hash(self.pos_decimal))

    def __eq__(self, other):
        if not isinstance(other, TextRenderCache):
            return False
        return hash(self) == hash(other)


class TextCacheManager:
    def __init__(self):
        self.text_cache_cnt = 0
        self.max_text_cache_cnt = 1000
        self.rendered_text_cnt: dict[TextRenderCache, int] = {}
        self.rendered_text_cache: dict[TextRenderCache, TextRenderCache] = {}
        self.clear_timer: wx.Timer | None = None

        # 挂钩get_cache函数从而自动启动清理缓存计时器
        raw_get_cache = self.get_cache

        def get_cache_hook(req_info: TextRenderCache):
            ret = raw_get_cache(req_info)
            if not self.clear_timer:
                app = wx.GetApp()
                self.clear_timer = wx.Timer(app)
                app.Bind(wx.EVT_TIMER, self.clear_unused_cache, self.clear_timer)
                self.clear_timer.Start(1000 * 60)  # 60秒清理一次缓存
                setattr(self, "get_cache", raw_get_cache)
            return ret

        setattr(self, "get_cache", get_cache_hook)

    def get_cache(self, req_info: TextRenderCache):
        """尝试获取文字渲染缓存"""
        if req_info in self.rendered_text_cache:
            self.rendered_text_cnt[req_info] += 1
            return self.rendered_text_cache[req_info]
        return None

    def add_cache(self, info: TextRenderCache):
        """增加文字渲染缓存"""
        if info not in self.rendered_text_cache:
            self.text_cache_cnt += 1
        self.rendered_text_cache[info] = info
        self.rendered_text_cnt[info] = 1

    def remove_cache(self, info: TextRenderCache):
        """删除文字渲染缓存"""
        self.text_cache_cnt -= 1
        del self.rendered_text_cnt[info]
        return self.rendered_text_cache.pop(info)

    def clear_unused_cache(self, *_):
        """清除不常使用的文字渲染缓存, 直到缓存数量小于最大缓存大小的0.8倍"""
        if self.text_cache_cnt < self.max_text_cache_cnt:
            return
        clear_target = self.max_text_cache_cnt * 0.8

        cnt_dict: dict[int, list[TextRenderCache]] = {}
        for info, cnt in self.rendered_text_cnt.items():
            if cnt not in cnt_dict:
                cnt_dict[cnt] = [info]
            else:
                cnt_dict[cnt].append(info)
        cnt_list = list(cnt_dict.items())
        cnt_list.sort(key=lambda x: x[0])
        for cnt, info_list in cnt_list:
            for info in info_list:
                self.remove_cache(info)
                if self.text_cache_cnt < clear_target:
                    return


TheTextCacheManager = TextCacheManager()


class JumpSubClassCheck:
    """
    用于跳过wx.GraphicsContext的不可继承检查, 同时保持自动补全可用
    For jumping wx.GraphicsContext's non sub-classable check, and keep the auto compile usable
    """
    GCType: type[wx.GraphicsContext] = wx.GraphicsContext


JumpSubClassCheck.GCType = typing.cast(type[wx.GraphicsContext], object)


class StateClass:
    def __init__(self, gc: wx.GraphicsContext):
        self.gc = gc

    def __enter__(self):
        self.gc.PushState()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.gc.PopState()


class TextRenderingHint(Enum):
    DEFAULT = 0
    SINGLE_BIT_PER_PIXEL_GRID_FIT = 1
    SINGLE_BIT_PER_PIXEL = 2
    ANTI_ALIAS_GRID_FIT = 3
    ANTI_ALIAS = 4
    CLEAR_TYPE_GRID_FIT = 5


class CustomGraphicsContext(JumpSubClassCheck.GCType):
    """
    GraphicsContext的拓展类
    Extra class of GraphicsContext.
    """
    _FACTORY_GC = wx.GraphicsContext.Create()
    TRANSPARENT_BRUSH: wx.GraphicsBrush = None
    TRANSPARENT_PEN = _FACTORY_GC.CreatePen(wx.GraphicsPenInfo(wx.BLACK, 0, wx.PENSTYLE_TRANSPARENT))
    font_trace_map: dict[int, wx.Font] = {}

    force_transparent_text = True

    def __new__(cls, *args, **kwargs):
        if cls.TRANSPARENT_BRUSH is None:
            cls.TRANSPARENT_BRUSH = cls._FACTORY_GC.CreateBrush(wx.Brush(wx.BLACK, wx.BRUSHSTYLE_TRANSPARENT))
        return super().__new__(cls)

    def __init__(self, gc: wx.GraphicsContext):
        object.__init__(self)

        self.gc = gc
        self.window = gc.GetWindow()
        self.current_font: wx.Font = self.window.GetFont()
        self.current_font_color: wx.Colour = self.window.GetForegroundColour()
        self.is_dark = getattr(self.window, "gen_style").is_dark if hasattr(self.window, "gen_style") else False

        if self.force_transparent_text:
            self.enable_transparent_text = True
            return
        top_level = gc.GetWindow().GetTopLevelParent()
        if hasattr(top_level, "WindowBlurEnabled") and getattr(top_level, "WindowBlurEnabled"):
            self.enable_transparent_text = True
        else:
            self.enable_transparent_text = False

    # 为日常调用提供重定向
    def __getattr__(self, name):
        try:
            return super().__getattribute__(name)
        except AttributeError:
            return getattr(self.gc, name)

    def SetFont(self, font: wx.Font, col: wx.Colour | None = None):
        if not isinstance(font, wx.Font):
            raise NotImplementedError("The font to be set must be wx.Font")
        self.current_font = font
        if col is not None:
            self.current_font_color = col
        self.gc.SetFont(self.CreateFont(font))

    def ensure_font(self):
        if self.current_font is None:
            raise ValueError("Font not defined yet")

    def DrawText(self, string: str | AdvancedText, x: float, y: float, color: wx.Colour | None = None,
                 center_align: Union[CenterAlign, str] = "topleft", attr: TextAttr | None = None):
        """
        绘制文字，后端为cairo+pango
        :param string 绘制的文字
        :param x 绘制x坐标
        :param y 绘制y坐标
        :param color 绘制文字颜色
        :param center_align 定义绘制坐标相对的文字的中心点
        :param attr 文字属性，将与设置的字体合并
        """
        self.ensure_font()

        # 统一转化为AdvancedText
        if isinstance(string, str):
            text = AdvancedText(text=string, global_attr=TextAttr.from_wx_font(self.current_font))
            if attr is not None:
                text.global_attr.merge(attr)
        elif isinstance(string, AdvancedText):
            text = string
            if attr is not None:
                text.global_attr.merge(attr)
        else:
            raise TypeError("Invalid text type")

        # 渲染文本
        color = self.current_font_color if color is None else color
        text_bitmap = TextRender.render(self, text, self.current_font, color)

        # 计算坐标偏移
        center_align = CenterAlign.format(center_align)
        w, h = text_bitmap.size
        if CenterAlign.TOP in center_align:
            y_off = 0
        elif CenterAlign.BOTTOM in center_align:
            y_off = h
        else:
            y_off = h // 2
        if CenterAlign.LEFT in center_align:
            x_off = 0
        elif CenterAlign.RIGHT in center_align:
            x_off = w
        else:
            x_off = w // 2

        self.gc.DrawBitmap(text_bitmap.bitmap, int(x - x_off), int(y - y_off), w, h)
        # print(len(TheTextCacheManager.rendered_text_cache))

    def GetFullTextExtent(self, string: str | AdvancedText, attr: TextAttr | None = None) -> tuple[float, float, float, float]:
        if not self.enable_transparent_text:
            return typing.cast(tuple[float, float, float, float], self.gc.GetFullTextExtent(string))
        if isinstance(string, str):
            text = AdvancedText(text=string, global_attr=attr)
        elif isinstance(string, AdvancedText):
            text = string
        logical_rect, ink_rect = TextRender.get_text_bbox(text)
        return ink_rect.width / 1024, ink_rect.height / 1024, ink_rect.x / 1024, ink_rect.y / 1024#right - left, bottom - top + OFFSET * 2, left, top - OFFSET

    def DrawInnerRoundedRect(self, x: float, y: float, w: float, h: float, radius: float, border_width: float):
        """在指定的矩形内部绘制一个矩形"""
        with self.State:
            self.Translate(x, y)
            GCRender.RenderInnerRoundedRect(self.gc, border_width, radius, w, h)

    @property
    def State(self):
        """
        使用 `with gc.State:` 来保存当前状态并在结束时恢复状态
        """
        return StateClass(self.gc)

    def DrawAnimationElement(self, element):
        """绘制一个动画元素"""
        element.draw(self)


def get_offset(border_width: float):
    if border_width == 1.0:
        return 0
    return border_width / 2


def ARC(angle: float):
    return math.pi * 2 * ((angle % 360) / 360)


gdi32 = ctypes.WinDLL("gdi32")
GetFontData = gdi32.GetFontData
GetFontData.argtypes = [wintypes.HDC, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD]
GetFontData.restype = wintypes.DWORD


class GCRender:
    FONT_CVT_CACHE: dict[tuple[int, float], ImageFont.FreeTypeFont] = {}
    SPACING = int(6 * SCALE)
    OFFSET = int(3 * SCALE)

    @staticmethod
    def GetFontByHandle(wx_font: wx.Font) -> ImageFont.FreeTypeFont:
        font_size = (wx_font.GetPointSize() if hasattr(wx_font,
                                                       "CWX_RAW_SIZE") else wx_font.GetPointSize() * SCALE) / 0.75
        cache_key = (int(typing.cast(int, wx_font.GetHFONT())), font_size)
        if cache_key in GCRender.FONT_CVT_CACHE:
            return GCRender.FONT_CVT_CACHE[cache_key]

        hdc = CreateCompatibleDC(None)
        SelectObject(hdc, int(typing.cast(int, wx_font.GetHFONT())))

        dwTable = 0x66637474
        size = GetFontData(hdc, dwTable, 0, 0, 0)
        if dwTable == GDI_ERROR or size == 0xffffffff:
            dwTable = 0
            size = GetFontData(hdc, dwTable, 0, 0, 0)
        font_buffer = ctypes.create_string_buffer(size)
        if GetFontData(hdc, dwTable, 0, font_buffer, size) != size:
            raise Exception("GetFontData error")
        DeleteDC(hdc)

        font_io = BytesIO(font_buffer.raw)

        font = ImageFont.truetype(font_io, font_size)
        # fixme: 更多的属性设置
        GCRender.FONT_CVT_CACHE[cache_key] = font
        return font

    @staticmethod
    def RenderInnerRoundedRect(gc: wx.GraphicsContext, border_width: float, corner_radius: float,
                               width: float = None, height: float = None):
        """
        渲染一个紧密贴合控件外部的边框
        Render a perfect border
        """
        if width is None or height is None:
            w, h = gc.GetSize()
        else:
            w, h = width, height
        path = gc.CreatePath()
        offset = get_offset(border_width)
        dn_offset = border_width - offset
        pad = offset + corner_radius
        dn_pad = dn_offset + corner_radius
        radius = corner_radius

        path.AddArc(pad, pad, radius, ARC(270), ARC(180), 0)
        # path.AddLineToPoint(offset, h - pad)
        path.AddArc(pad, h - dn_pad, radius, ARC(180), ARC(90), 0)
        # path.AddLineToPoint(w - pad, h - dn_offset)
        path.AddArc(w - dn_pad, h - dn_pad, radius, ARC(90), ARC(0), 0)
        # path.AddLineToPoint(w - dn_offset, pad)
        path.AddArc(w - dn_pad, pad, radius, ARC(0), ARC(270), 0)
        path.AddLineToPoint(pad, offset)

        gc.DrawPath(path)

        return offset, dn_offset
