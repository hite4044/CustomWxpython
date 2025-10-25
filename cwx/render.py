import ctypes
import math
import typing
from ctypes import wintypes
from dataclasses import dataclass
from enum import Enum
from io import BytesIO
from math import ceil

import wx
from PIL import ImageFont, Image, ImageDraw
from win32.lib.win32con import GDI_ERROR
from win32gui import CreateCompatibleDC, SelectObject, DeleteDC

from .animation import Animation
from .dpi import SCALE
from .tool.image_pil2wx import PilImg2WxImg


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


class AnimationElement:
    def __init__(self, anim: Animation):
        self.anim = anim

    def draw(self, gc: 'CustomGraphicsContext'):
        pass


class DrawLinesAE(AnimationElement):
    def __init__(self, anim: Animation, point2Ds: list[wx.Point2D] = None, fill_style: wx.PolygonFillMode = wx.ODDEVEN_RULE):
        super().__init__(anim)
        self.point2Ds: list[wx.Point2D] = point2Ds
        self.fill_style = fill_style

    def draw(self, gc: 'CustomGraphicsContext'):
        if self.point2Ds is None:
            return

        value = self.anim.value
        if value == 0:
            return
        if value == 1:
            gc.DrawLines(self.point2Ds, self.fill_style)
            return

        point2Ds = self.point2Ds
        active_points = [point2Ds[0]]
        distances = [point2Ds[i].GetDistance(point2Ds[i + 1]) for i in range(len(point2Ds) - 1)]
        total_distance = sum(distances)
        left_distance = total_distance * min(max(value, 0), 1)
        distance = 0
        for i, distance in enumerate(distances):
            active_points.append(point2Ds[i + 1])
            if left_distance <= distance:
                break
            left_distance -= distance
        if left_distance != 0:
            last_second_pt = wx.Point2D(active_points[-2])
            last_pt = wx.Point2D(active_points[-1])
            percent = left_distance / distance
            last_pt[0] = last_second_pt[0] + (last_pt[0] - last_second_pt[0]) * percent
            last_pt[1] = last_second_pt[1] + (last_pt[1] - last_second_pt[1]) * percent
            active_points[-1] = last_pt

        gc.DrawLines(active_points, wx.ODDEVEN_RULE)


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

    def __new__(cls, *args, **kwargs):
        if cls.TRANSPARENT_BRUSH is None:
            cls.TRANSPARENT_BRUSH = cls._FACTORY_GC.CreateBrush(wx.Brush(wx.BLACK, wx.BRUSHSTYLE_TRANSPARENT))
        return super().__new__(cls)

    def __init__(self, gc: wx.GraphicsContext):
        if 1 * 1.0 == 0:
            super().__init__()  # Never Called

        self.gc = gc
        self.current_font: wx.Font | None = None
        self.window = gc.GetWindow()
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

    def CreateFont(self, font: wx.Font, col: wx.Colour):
        gc_font = self.gc.CreateFont(font, col)
        font.color = col
        self.font_trace_map[id(gc_font)] = font
        return gc_font

    def SetFont(self, font: wx.GraphicsFont):
        if id(font) in self.font_trace_map:
            self.current_font = self.font_trace_map[id(font)]
        else:
            self.current_font = None
        self.gc.SetFont(font)

    def DrawText(self, string: str, x: float, y: float):
        """通过PIL渲染文字实现绘制无黑边的完全透明度文字"""
        if not self.enable_transparent_text:
            self.gc.DrawText(string, x, y)
            return
        info = self.LoadTextRenderInfo(string, x, y)

        if t_info := TheTextCacheManager.get_cache(info):  # 使用已渲染缓存
            bitmap, size = t_info.text_bitmap, t_info.size
            offset_pos = (int(x), int(y))
        else:  # 新增字体渲染缓存
            wx_font = self.current_font if self.current_font else self.window.GetFont()
            bitmap, size = GCRender.RenderTransparentText(self, info, wx_font)  # 增加渲染颜色
            info.size = size
            info.text_bitmap = bitmap
            TheTextCacheManager.add_cache(info)
            offset_pos = info.offset_pos

        self.gc.DrawBitmap(bitmap, *offset_pos, size[0], size[1])
        # print(len(TheTextCacheManager.rendered_text_cache))

    def GetFullTextExtent(self, text: str) -> tuple[float, float, float, float]:
        if not self.enable_transparent_text:
            return typing.cast(tuple[float, float, float, float], self.gc.GetFullTextExtent(text))
        image = Image.new("RGBA", (0, 0))
        draw = ImageDraw.Draw(image)
        wx_font = self.current_font if self.current_font else self.window.GetFont()
        font = GCRender.GetFontByHandle(wx_font)
        spacing = GCRender.SPACING
        left, top, right, bottom = draw.multiline_textbbox((0, 0), text, font, spacing=spacing)
        OFFSET = GCRender.OFFSET
        return right - left, bottom - top + OFFSET * 2, left, top - OFFSET

    def LoadTextRenderInfo(self, string: str, x: float, y: float):
        wx_font = self.current_font if self.current_font else self.window.GetFont()
        color = wx_font.color.Get(True) if hasattr(wx_font, "color") else self.window.GetForegroundColour().Get(True)
        pos_decimal = (x - int(x), y - int(y))
        return TextRenderCache(string, color, wx_font.NativeFontInfoDesc, pos_decimal, offset_pos=(int(x), int(y)))

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

    def DrawAnimationElement(self, element: AnimationElement):
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
    def RenderTransparentText(gc: CustomGraphicsContext, info: TextRenderCache, wx_font: wx.Font) -> \
            tuple[wx.GraphicsBitmap, tuple[int, int]]:
        window = gc.GetWindow()
        font = GCRender.GetFontByHandle(wx_font)

        # 获取文字大小
        SPACING = GCRender.SPACING
        OFFSET = GCRender.OFFSET

        sm_draw = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
        left, top, right, bottom = sm_draw.textbbox((0, 0),
                                                    info.text, font=font, spacing=SPACING)
        if left == top == right == bottom == 0:
            return gc.CreateBitmapFromImage(wx.Image(1, 1)), (1, 1)

        # 绘制文字
        image = Image.new("RGBA", typing.cast(tuple[int, int], (ceil(right - left), ceil(bottom - top + OFFSET))))
        draw = ImageDraw.Draw(image)
        color = wx_font.color.Get(True) if hasattr(wx_font, "color") else window.GetForegroundColour().Get(True)
        draw.text((info.pos_decimal[0] - left, info.pos_decimal[1] - top + OFFSET),
                  info.text, fill=color, font=font, spacing=SPACING)  # , embedded_color=True

        # 转化并返回
        wx_image = PilImg2WxImg(image)
        return (
            gc.CreateBitmapFromImage(wx_image),
            typing.cast(tuple[int, int], wx_image.GetSize().Get())
        )

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
